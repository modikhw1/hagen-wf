"""Del 3 (steg_bygg_patch.py):
Genererar `steg_scen_brygga.py` (patchad kopia av `forvarld_karna/scen_brygga.py`) och `steg_scen_brygga.diff`.
Rör inte `forvarld_karna/scen_brygga.py` eller någon annan fil utanför `motpart/runda-2-neon/`.

Fem sammanhängande förbättringar i Lager 3-kompilatorn (ett steg mot K2, K4, K5, K6, K8):
  S1 Sann 3D-kamerageometri: återinsätter receptets pitch/roll (`rotation[0..1]`) + exakt pinhole-djupskalning
     `[1, 1, f_px/f_sam]`. Slutar skjuta andra personen (`idx_p > 0`) med okompenserad `z_kropp`, och slutar
     flytta kameran efter hallucinerade skymda SAM-fötter när `ben_synliga == False`.
  S2 Anatomiska skymda ben märkta `antagen`: när `ben_synliga[f] == False` rekonstrueras endast underkroppen
     (lår/knä/fot/tå) med konstanta benlängder — sittande lår ~12° (knä >= 0.36 m) och stående raka ben till golvet —
     utan att röra en enda synlig överkroppsled (0 px 2D-påverkan) och loggat som `status="antagen"`.
  S3 Ärlig synlighet (`kand`-filtrering + ärlig R1): spökkroppar i rutor utan bilddetektion (`kand == False`,
     t.ex. kebabspettet i asketch S3 och arminklippet i gelato S2) filtreras bort ur `rorelse` och `ut`-intervall;
     R1 döljer aldrig ett bord i en tagning där receptet har observerat det (`evidence_shots`), utan rapporterar
     kollisionen/skymningen i `beslut`.
  S4 Oberoende G7 + per-person grindar (`g7_oberoende` + `grindar_per_person`).
  S5 Medielager & bärande kärna direkt i `paket["mening"]`: laddar `semantik.json` via EXAKT lokal sökväg
     (aldrig delsträngsmatchning på mappnamn!) och fyller `karna`, `repliker` (med `a`-ruta för emit_bpy),
     `skarmtext` och `scener` (med `funktion`, `vad`, `barande`, `langd_s`) så att inspelningsmanus (K6) och
     redigerbara medielager (K5/K8) följer direkt ur `scenpaket/2`.

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\steg_bygg_patch.py
"""
from __future__ import annotations

import difflib
import pathlib

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
ORIG = ROT / "forvarld_karna/scen_brygga.py"

HJALP_KOD = r'''
def _rekonstruera_skymda_ben(
    X: np.ndarray,
    leder: list[str],
    pose_etikett: str,
    ben_synliga_arr: np.ndarray,
    golv: float = 0.0,
) -> dict:
    """S2: Rekonstruerar skymda ben (där ben_synliga==False) utan att röra överkroppen (c_spine0 och uppåt).
    Bevarar konstanta anatomiska benlängder per person (H8 CV ~ 0) och undviker SAM:s skymda huk (knä 0.14-0.22 m).
    """
    ix = {n: i for i, n in enumerate(leder)}
    T = len(X)
    mask_skymd = ~np.asarray(ben_synliga_arr, dtype=bool)
    n_skymd = int(mask_skymd.sum())
    if n_skymd == 0:
        return dict(andrade_rutor=0, status="observed")

    # Mät personens egna medianlängder för lår och skenben (begränsade till realistiskt vuxenspann)
    l1_l = np.linalg.norm(X[:, ix["l_lowleg"]] - X[:, ix["l_upleg"]], axis=-1)
    l1_r = np.linalg.norm(X[:, ix["r_lowleg"]] - X[:, ix["r_upleg"]], axis=-1)
    l2_l = np.linalg.norm(X[:, ix["l_foot"]] - X[:, ix["l_lowleg"]], axis=-1)
    l2_r = np.linalg.norm(X[:, ix["r_foot"]] - X[:, ix["r_lowleg"]], axis=-1)
    L1_raw = float(np.median(np.r_[l1_l, l1_r]))
    L2_raw = float(np.median(np.r_[l2_l, l2_r]))
    L1 = float(np.clip(L1_raw, 0.36, 0.46))
    L2 = float(np.clip(L2_raw, 0.36, 0.45))

    # Mjuk horisontell framåtriktning ur axellinjen (oberoende av skymda höfter!)
    ax_all = X[:, ix["r_uparm"]] - X[:, ix["l_uparm"]]
    ax_all[:, 2] = 0.0
    ax_med = np.median(ax_all, axis=0)
    if np.linalg.norm(ax_med) < 1e-4:
        ax_med = np.array([1.0, 0.0, 0.0])
    hoger = ax_med / (np.linalg.norm(ax_med) + 1e-9)
    fram = np.cross(hoger, np.array([0.0, 0.0, 1.0]))
    fram[2] = 0.0
    fram = fram / (np.linalg.norm(fram) + 1e-9)
    # Kontrollera tecken mot blickriktningen (c_head -> nasa_mal) så att knäna pekar framåt, inte bakåt!
    blick = np.median(X[:, ix["nasa_mal"], :2] - X[:, ix["c_head"], :2], axis=0)
    if float(fram[:2] @ blick) < 0.0:
        fram = -fram
        hoger = -hoger

    hoft_bredd = float(np.clip(0.5 * np.median(np.linalg.norm(X[:, ix["r_upleg"], :2] - X[:, ix["l_upleg"], :2], axis=-1)), 0.08, 0.13))
    fot_z_mal = golv + FOTLED_OVER_GOLV
    ta_z_mal = golv + TA_OVER_GOLV

    for t in range(T):
        if not mask_skymd[t]:
            continue
        sp0 = X[t, ix["c_spine0"]].copy()
        for sida, tecken in (("l", -1.0), ("r", +1.0)):
            hoft = sp0 + hoger * (tecken * hoft_bredd) + np.array([0.0, 0.0, -0.04])
            if pose_etikett == "sittande":
                # Vågrätt / lätt sluttande lår (~12°), knä >= 0.36 m, skenben rakt/lätt indraget till golv med exakt L2
                dz_lar = -L1 * math.sin(math.radians(12.0))
                kna_z = max(0.36, min(hoft[2] + dz_lar, fot_z_mal + L2 - 0.005))
                dz_faktisk = kna_z - hoft[2]
                hor_lar = math.sqrt(max(L1 ** 2 - dz_faktisk ** 2, 1e-4))
                kna = np.array([hoft[0] + fram[0] * hor_lar, hoft[1] + fram[1] * hor_lar, kna_z])
                dz_sken = kna_z - fot_z_mal
                if dz_sken <= L2:
                    hor_sken = math.sqrt(max(L2 ** 2 - dz_sken ** 2, 0.0))
                    fot = np.array([kna[0] - fram[0] * 0.5 * hor_sken, kna[1] - fram[1] * 0.5 * hor_sken, fot_z_mal])
                    # Exakt normering till L2
                    v_sk = fot - kna
                    if np.linalg.norm(v_sk) > 1e-6:
                        # Behåll z om möjligt via horisontell cirkelskärning
                        fot = np.array([kna[0] - fram[0] * hor_sken, kna[1] - fram[1] * hor_sken, fot_z_mal])
                else:
                    fot = kna + np.array([0.0, 0.0, -L2])
            else:
                # Stående bakom disk: ben nästan raka ned mot golvet med lätt naturlig knäböj (exakta L1, L2)
                hojd_till_fot = max(hoft[2] - fot_z_mal, 0.10)
                if hojd_till_fot >= L1 + L2 - 0.005:
                    # Bäcken högt nog för raka ben; behåll benlängd L1+L2 och låt fot nå golv eller sväva minimalt
                    eff_L1, eff_L2 = L1, L2
                    kna = hoft + np.array([0.0, 0.0, -eff_L1]) + fram * 0.015
                    kna = hoft + (kna - hoft) / np.linalg.norm(kna - hoft) * eff_L1
                    fot = kna + np.array([0.0, 0.0, -eff_L2])
                else:
                    # 2-leds-IK rakt ned till fot på golvet med lätt framåtböjt knä
                    dist = min(hojd_till_fot, L1 + L2 - 1e-4)
                    a = (L1 ** 2 - L2 ** 2 + dist ** 2) / (2.0 * max(dist, 1e-6))
                    hh = math.sqrt(max(L1 ** 2 - a ** 2, 0.0))
                    kna = hoft + np.array([0.0, 0.0, -a]) + fram * hh
                    fot = hoft + np.array([0.0, 0.0, -dist])
            ta = np.array([fot[0] + fram[0] * 0.12, fot[1] + fram[1] * 0.12, max(ta_z_mal, fot[2] - 0.045)])
            X[t, ix[f"{sida}_upleg"]] = hoft
            X[t, ix[f"{sida}_lowleg"]] = kna
            X[t, ix[f"{sida}_foot"]] = fot
            X[t, ix[f"{sida}_ball"]] = ta

    return dict(andrade_rutor=n_skymd, totalt_rutor=T, andel=round(n_skymd / max(T, 1), 3),
                L1=round(L1, 3), L2=round(L2, 3), status="antagen")


def _ladda_exakt_semantik(ingest: pathlib.Path, semantik_fil: pathlib.Path | None = None) -> dict | None:
    """S5: Läser semantik.json ENBART via explicit sökväg eller direkt inuti ingest-mappen (aldrig delsträngsmatchning)."""
    kandidater = []
    if semantik_fil is not None:
        kandidater.append(pathlib.Path(semantik_fil))
    kandidater.append(ingest / "semantik/semantik.json")
    for k in kandidater:
        if k.exists():
            raw = json.loads(k.read_text(encoding="utf-8"))
            return raw.get("data", raw)
    return None
'''

ERSATT = [
    # --- sökvägar: kopian bor i motpart/runda-2-neon/ men importerar forvarld_karna, byggsten/brygga och runda-1-claude
    (
        "HIT = pathlib.Path(__file__).resolve().parent\nROT = HIT.parent\n",
        "ROT = pathlib.Path(__file__).resolve().parents[2]   # STEG-PATCH: kopian bor i motpart/runda-2-neon/\n"
        "HIT = ROT / \"forvarld_karna\"\n"
        "sys.path.insert(0, str(ROT / \"motpart/runda-1-claude\"))\n",
    ),
    # --- Lägg in hjälpfunktioner S2 och S5 före kompilera_scenpaket
    (
        "def kompilera_scenpaket(\n"
        "    klipp_namn: str,\n"
        "    ingest: pathlib.Path,\n"
        "    obs: Observationer,\n"
        "    recept: Recept,\n"
        "    ut_mapp: pathlib.Path,\n"
        "    steg: int = 1,\n"
        ") -> pathlib.Path:",
        HJALP_KOD + "\n\ndef kompilera_scenpaket(\n"
        "    klipp_namn: str,\n"
        "    ingest: pathlib.Path,\n"
        "    obs: Observationer,\n"
        "    recept: Recept,\n"
        "    ut_mapp: pathlib.Path,\n"
        "    steg: int = 1,\n"
        "    semantik_fil: pathlib.Path | None = None,\n"
        ") -> pathlib.Path:",
    ),
    # --- S1: Återinsätt kamerans verkliga pitch och roll (rotation[0..1]) i stället för (90, 0, rz)
    (
        "        R_cam = _euler_xyz_till_mat(90.0, 0.0, cam_nod.rotation[2])",
        "        R_cam = _euler_xyz_till_mat(cam_nod.rotation[0], cam_nod.rotation[1], cam_nod.rotation[2])  # STEG S1",
    ),
    # --- S1 + S2 + S3: pinhole djup-skalning, ben_synliga-medveten höjdkalibrering, kand-filtrering och anatomiska skymda ben
    (
        "            q_seq = np.load(seq_fil)\n"
        "            n_seq = len(q_seq[\"pose\"])\n"
        "            kallor = [\n"
        "                HARLEDD.get(n, (n,)) if n not in (\"huvud_upp\", \"nasa_mal\") else (\"c_head\",)\n"
        "                for n in LEDER_T1\n"
        "            ]\n"
        "\n"
        "            U, XS, X_RA_2D = [], [], []\n"
        "            raw_fots, raw_backen = [], []\n"
        "            sp2_ix = IX[\"c_spine2\"]\n"
        "            for u in range(a0, b0):\n"
        "                f_ix = min(u - a0, n_seq - 1)\n"
        "                pose_f = q_seq[\"pose\"][f_ix]\n"
        "                ct_raw = q_seq[\"cam_t_ra\"][f_ix]\n"
        "                bal_m = pose_f[sp2_ix, :3] / 100.0\n"
        "                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + kappa * (bal_m + (ct_raw @ F.T))\n"
        "                alla_w = (c_cam @ R_cam.T) + C_world\n"
        "                raw_fots.append(min(alla_w[IX[\"l_foot\"], 2], alla_w[IX[\"r_foot\"], 2]))\n"
        "                raw_backen.append(alla_w[IX[\"c_spine0\"], 2])\n"
        "            med_fot_z = float(np.median(raw_fots)) if raw_fots else 0.0\n"
        "            med_backen_z = float(np.median(raw_backen)) if raw_backen else 0.55\n"
        "\n"
        "            z_skift = 0.0\n"
        "            if d_pers.pose == \"staende\" and med_fot_z > 0.08:\n"
        "                z_skift = -(med_fot_z - FOTLED_OVER_GOLV)\n"
        "            elif d_pers.pose == \"sittande\":\n"
        "                mal_backen_z = float(sittande_backen[pid][0][2]) if pid in sittande_backen else 0.55\n"
        "                if abs(med_backen_z - mal_backen_z) > 0.08:\n"
        "                    z_skift = mal_backen_z - med_backen_z\n"
        "            z_kropp = 0.0\n"
        "            if idx_p == 0:\n"
        "                ny_cz = max(0.92, C_world[2] + z_skift)\n"
        "                z_kam_delta = ny_cz - C_world[2]\n"
        "                C_world[2] = ny_cz\n"
        "                z_kropp = z_skift - z_kam_delta\n"
        "                q_cam = mat_till_quat(R_cam)\n"
        "            else:\n"
        "                z_kropp = z_skift\n"
        "\n"
        "            for u in range(a0, b0):\n"
        "                if (u - a0) % steg and u != b0 - 1:\n"
        "                    continue\n"
        "                f_ix = min(u - a0, n_seq - 1)\n"
        "                pose_f = q_seq[\"pose\"][f_ix]\n"
        "                ct_raw = q_seq[\"cam_t_ra\"][f_ix]\n"
        "                bal_m = pose_f[sp2_ix, :3] / 100.0\n"
        "                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + kappa * (bal_m + (ct_raw @ F.T))\n"
        "                alla_w = (c_cam @ R_cam.T) + C_world\n"
        "                if z_kropp != 0.0:\n"
        "                    alla_w[:, 2] += z_kropp",
        "            q_seq = np.load(seq_fil)\n"
        "            n_seq = len(q_seq[\"pose\"])\n"
        "            # STEG S1: exakt pinhole-djupskalning f_px/f_sam (bevarar bålens 2D-läge och 3D-strålriktning)\n"
        "            djup_skala = np.array([1.0, 1.0, f_px / float(q_seq[\"fokal\"])])\n"
        "            ben_synl_raw = q_seq[\"ben_synliga\"] if \"ben_synliga\" in q_seq.files else np.ones(n_seq, bool)\n"
        "            kand_raw = q_seq[\"kand\"] if \"kand\" in q_seq.files else np.ones(n_seq, bool)\n"
        "            har_synliga_ben = float(np.mean(ben_synl_raw)) >= 0.30\n"
        "            kallor = [\n"
        "                HARLEDD.get(n, (n,)) if n not in (\"huvud_upp\", \"nasa_mal\") else (\"c_head\",)\n"
        "                for n in LEDER_T1\n"
        "            ]\n"
        "\n"
        "            U, XS, X_RA_2D, BEN_S = [], [], [], []\n"
        "            raw_fots, raw_backen = [], []\n"
        "            sp2_ix = IX[\"c_spine2\"]\n"
        "            for u in range(a0, b0):\n"
        "                f_ix = min(u - a0, n_seq - 1)\n"
        "                if not bool(kand_raw[f_ix]):\n"
        "                    continue\n"
        "                pose_f = q_seq[\"pose\"][f_ix]\n"
        "                ct_raw = q_seq[\"cam_t_ra\"][f_ix]\n"
        "                bal_m = pose_f[sp2_ix, :3] / 100.0\n"
        "                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + (bal_m + (ct_raw @ F.T)) * djup_skala\n"
        "                alla_w = (c_cam @ R_cam.T) + C_world\n"
        "                raw_fots.append(min(alla_w[IX[\"l_foot\"], 2], alla_w[IX[\"r_foot\"], 2]))\n"
        "                raw_backen.append(alla_w[IX[\"c_spine0\"], 2])\n"
        "            med_fot_z = float(np.median(raw_fots)) if raw_fots else 0.0\n"
        "            med_backen_z = float(np.median(raw_backen)) if raw_backen else 0.55\n"
        "\n"
        "            # STEG S1: Flytta bara kamera + kropp tillsammans när faktisk kroppshöjd avviker från fysiskt spann.\n"
        "            # Flytta ALDRIG kameran efter hallucinerade skymda SAM-fötter när ben_synliga == False!\n"
        "            z_skift = 0.0\n"
        "            if d_pers.pose == \"staende\":\n"
        "                if har_synliga_ben and med_fot_z > 0.08:\n"
        "                    z_skift = -(med_fot_z - FOTLED_OVER_GOLV)\n"
        "                elif not har_synliga_ben:\n"
        "                    if med_backen_z < 0.78:\n"
        "                        z_skift = 0.86 - med_backen_z\n"
        "                    elif med_backen_z > 1.12:\n"
        "                        z_skift = 0.96 - med_backen_z\n"
        "            elif d_pers.pose == \"sittande\":\n"
        "                mal_backen_z = float(sittande_backen[pid][0][2]) if pid in sittande_backen else 0.55\n"
        "                if abs(med_backen_z - mal_backen_z) > 0.12:\n"
        "                    z_skift = mal_backen_z - med_backen_z\n"
        "            z_kropp = 0.0\n"
        "            if idx_p == 0 and z_skift != 0.0:\n"
        "                # Håll kamera+kropp ihop (z_kropp=0) men begränsa skiftet till <= 2.5*sigma från obs-höjd (min 0.78 m)\n"
        "                obs_h = float(k_obs.kamera.hojd_m.v)\n"
        "                obs_s = float(k_obs.kamera.hojd_m.s)\n"
        "                ny_cz = float(np.clip(C_world[2] + z_skift, max(0.78, obs_h - 2.4 * obs_s), obs_h + 2.4 * obs_s))\n"
        "                C_world[2] = ny_cz\n"
        "                q_cam = mat_till_quat(R_cam)\n"
        "                beslut.append(dict(regel=\"S1_kamera_hojd_kalibrering\", person=pid, tagning=sid,\n"
        "                                   kamera_z=round(ny_cz, 3), obs_hojd=obs_h, z_skift_onskad=round(z_skift, 3)))\n"
        "            # För idx_p > 0: aldrig okompenserad z_kropp som bryter 2D-projektionen!\n"
        "\n"
        "            # STEG S3: Filtrera bort spökrutor (kand == False) utom om hela tagningen saknar kand\n"
        "            giltiga_u = [u for u in range(a0, b0) if bool(kand_raw[min(u - a0, n_seq - 1)])]\n"
        "            if not giltiga_u:\n"
        "                giltiga_u = [a0]\n"
        "            n_spok_bort = (b0 - a0) - len(giltiga_u)\n"
        "            if n_spok_bort > 0:\n"
        "                beslut.append(dict(regel=\"S3_kand_spokfilter\", person=pid, tagning=sid,\n"
        "                                   borttagna_rutor=n_spok_bort, kvar_rutor=len(giltiga_u),\n"
        "                                   orsak=\"Rutor utan bilddetektion (kand=False) filtreras bort för att undvika spökkroppar.\"))\n"
        "\n"
        "            for u in giltiga_u:\n"
        "                if (u - a0) % steg and u != giltiga_u[-1]:\n"
        "                    continue\n"
        "                f_ix = min(u - a0, n_seq - 1)\n"
        "                pose_f = q_seq[\"pose\"][f_ix]\n"
        "                ct_raw = q_seq[\"cam_t_ra\"][f_ix]\n"
        "                bal_m = pose_f[sp2_ix, :3] / 100.0\n"
        "                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + (bal_m + (ct_raw @ F.T)) * djup_skala\n"
        "                alla_w = (c_cam @ R_cam.T) + C_world\n"
        "                if z_kropp != 0.0:\n"
        "                    alla_w[:, 2] += z_kropp\n"
        "                BEN_S.append(bool(ben_synl_raw[f_ix]))",
    ),
    # --- S2: Rekonstruera skymda ben före R3 fotkontakt + sätt ärligt synlighetsintervall sp["ut"] från U ---
    (
        "            C_arr = kam_bana_per_ruta if kam_bana_per_ruta is not None else np.tile(C_world, (len(X), 1))\n"
        "            andr = fotkontakt(X, LEDER_T1, golv_z)\n",
        "            # STEG S2: Rekonstruera skymda ben anatomiskt (märkt antagen) utan att ändra synlig överkropp!\n"
        "            skymd_info = _rekonstruera_skymda_ben(X, LEDER_T1, d_pers.pose or \"staende\", np.array(BEN_S, bool), golv_z)\n"
        "            if skymd_info[\"andrade_rutor\"] > 0:\n"
        "                beslut.append(dict(regel=\"S2_skymda_ben_antagen\", person=pid, tagning=sid, **skymd_info,\n"
        "                                   orsak=\"Underkropp saknar bildstöd (ben_synliga=False); ben rekonstruerade anatomiskt utan att röra överkroppen.\"))\n"
        "            C_arr = kam_bana_per_ruta if kam_bana_per_ruta is not None else np.tile(C_world, (len(X), 1))\n"
        "            andr = fotkontakt(X, LEDER_T1, golv_z)\n",
    ),
    (
        "            rorelse.setdefault(pid, []).append(dict(\n"
        "                tagning=sid,\n"
        "                ut=[a0, b0],\n"
        "                rutor=rutor_int,\n"
        "            ))",
        "            rorelse.setdefault(pid, []).append(dict(\n"
        "                tagning=sid,\n"
        "                ut=[int(min(U)), int(max(U)) + 1] if U else [a0, b0],\n"
        "                rutor=rutor_int,\n"
        "            ))",
    ),
    # --- Märk stolens status tydligt som "antagen" (K4) ---
    (
        "            farg=\"#6b5344\", status=\"amodal_inferred\", rum=\"gemensamt\", synlig_ut=[[0, N]],",
        "            farg=\"#6b5344\", status=\"antagen\", rum=\"gemensamt\", synlig_ut=[[0, N]],",
    ),
    # --- S3: R1 döljer ALDRIG ett bord i en tagning där receptet har observerat det (n.evidence_shots) ---
    (
        "                    if ins.any(axis=1).mean() > 0.05:\n"
        "                        bort_iv.append([a0, b0])\n"
        "                        beslut.append(dict(\n"
        "                            regel=\"R1_kollisionsskydd\",\n"
        "                            objekt=n.id,\n"
        "                            person=pid,\n"
        "                            tagning=sid,\n"
        "                            orsak=f\"{n.id} överlappar {pid}:s rörelsebana i {sid} och döljs i tagningen.\",\n"
        "                        ))\n"
        "                        break",
        "                    if ins.any(axis=1).mean() > 0.05:\n"
        "                        if sid in (n.evidence_shots or []):\n"
        "                            beslut.append(dict(\n"
        "                                regel=\"S3_kollision_rapporterad\",\n"
        "                                objekt=n.id, person=pid, tagning=sid,\n"
        "                                andel=round(float(ins.any(axis=1).mean()), 3),\n"
        "                                orsak=f\"{n.id} är observerat i {sid} och behålls synligt; kollision rapporteras ärligt.\",\n"
        "                            ))\n"
        "                        else:\n"
        "                            bort_iv.append([a0, b0])\n"
        "                            beslut.append(dict(\n"
        "                                regel=\"R1_kollisionsskydd\",\n"
        "                                objekt=n.id, person=pid, tagning=sid,\n"
        "                                orsak=f\"{n.id} ej observerat i {sid} och överlappar {pid}; döljs.\",\n"
        "                            ))\n"
        "                            break",
    ),
    (
        "                    if ov > 0.25:\n"
        "                        bort_iv.append([a0, b0])\n"
        "                        beslut.append(dict(\n"
        "                            regel=\"R1_skymningsskydd\",\n"
        "                            objekt=n.id,\n"
        "                            person=pid,\n"
        "                            tagning=sid,\n"
        "                            orsak=f\"{n.id} skymmer {round(ov*100)}% av {pid}:s överkropp i {sid}.\",\n"
        "                        ))\n"
        "                        break",
        "                    if ov > 0.25:\n"
        "                        if sid in (n.evidence_shots or []):\n"
        "                            beslut.append(dict(\n"
        "                                regel=\"S3_skymning_rapporterad\",\n"
        "                                objekt=n.id, person=pid, tagning=sid, tackning=round(float(ov), 3),\n"
        "                                orsak=f\"{n.id} är observerat i {sid} och behålls synligt (täckning {round(ov*100)}%).\",\n"
        "                            ))\n"
        "                        else:\n"
        "                            bort_iv.append([a0, b0])\n"
        "                            beslut.append(dict(\n"
        "                                regel=\"R1_skymningsskydd\",\n"
        "                                objekt=n.id, person=pid, tagning=sid,\n"
        "                                orsak=f\"{n.id} ej observerat i {sid} och skymmer {round(ov*100)}%; döljs.\",\n"
        "                            ))\n"
        "                            break",
    ),
    # --- S5: Lyft in semantikens medielager (repliker, skärmtext, scener, kärna) direkt i paket["mening"] ---
    (
        "        mening=dict(repliker=[], roller=personer_meta, rum_relationer={\"tro\": recept.tro}),",
        "        mening=_bygg_mening_och_medielager(ingest, semantik_fil, tagningar, personer_meta, recept, fps),",
    ),
    # --- S4: Oberoende G7 + per-person grindar (efter all efterbehandling) ---
    (
        "    ut_mapp.mkdir(parents=True, exist_ok=True)\n"
        "    paket_fil = ut_mapp / \"paket.json\"\n"
        "    paket_fil.write_text(json.dumps(paket, ensure_ascii=False, separators=(\",\", \":\")), encoding=\"utf-8\")\n"
        "\n"
        "    # --- 3. Kör Kvalitetsgrindar G1–G7 ---\n"
        "    rader = grindar.mat(paket)\n",
        "    # STEG S4: Trohet mot oberoende 2D (g7_oberoende) på slutpaketet + en grindrad per (tagning, person)\n"
        "    import g7_oberoende\n"
        "    obs_d = json.loads(obs.model_dump_json())\n"
        "    for r in g7_oberoende.mat_paket(klipp_namn, paket, obs_d, ingest=ingest):\n"
        "        paket[\"trohet\"][f\"{r['tagning']}:{r['person']}\"] = dict(\n"
        "            metod=\"g7_oberoende\", led_med=r[\"led_med\"], led_p90=r[\"led_p90\"], i_box=r[\"i_box\"], iou=r[\"iou\"],\n"
        "            i_mask=r[\"i_mask\"], spok_andel=r[\"spok_andel\"], flaggad=r[\"flaggad\"], skal=r[\"skal\"])\n"
        "    ut_mapp.mkdir(parents=True, exist_ok=True)\n"
        "    paket_fil = ut_mapp / \"paket.json\"\n"
        "    paket_fil.write_text(json.dumps(paket, ensure_ascii=False, separators=(\",\", \":\")), encoding=\"utf-8\")\n"
        "\n"
        "    # --- 3. Kör Kvalitetsgrindar G1–G7 (per person) ---\n"
        "    rader = g7_oberoende.grindar_per_person(paket)\n",
    ),
]

MENING_HJALP = r'''
def _bygg_mening_och_medielager(
    ingest: pathlib.Path,
    semantik_fil: pathlib.Path | None,
    tagningar: list[dict],
    personer_meta: dict,
    recept: Recept,
    fps: float,
) -> dict:
    """S5: Lyfter in semantikens repliker, skärmtext, scenfunktioner och bärande kärna direkt i scenpaket/2."""
    sem = _ladda_exakt_semantik(ingest, semantik_fil)
    if sem is None:
        return dict(repliker=[], skarmtext=[], scener=[], karna="", sammanfattning="",
                    roller=personer_meta, rum_relationer={"tro": recept.tro}, semantik_kalla=None)

    kl_info = sem.get("klipp") or {}
    karna = kl_info.get("karna", "")
    samman = kl_info.get("sammanfattning", "")
    plats_txt = (sem.get("plats") or {}).get("typ") or (sem.get("plats") or {}).get("beskrivning") or recept.tro

    # Mappa semantikens P1/P2/P3 -> paketets A/B/C
    p_till_roll = {f"P{i+1}": chr(ord("A") + i) for i in range(6)}
    tagn_map = {t["id"]: t for t in tagningar}
    tagn_sem = {str(x.get("tagning", "")).lower(): x for x in (sem.get("tagningar") or [])}

    repliker = []
    for r in (sem.get("repliker") or []):
        sid = str(r.get("tagning", "")).lower()
        t_obj = tagn_map.get(sid)
        a_ruta = int(round(float(r.get("start_s", 0.0)) * fps))
        if t_obj is not None:
            a_ruta = max(t_obj["ut"][0], min(a_ruta, t_obj["ut"][1] - 1))
        funktion = (tagn_sem.get(sid) or {}).get("funktion", "")
        repliker.append(dict(
            id=r.get("id", f"r_{len(repliker)+1}"),
            talare=p_till_roll.get(r.get("talare", ""), r.get("talare", "")),
            tagning=sid,
            text=r.get("text", ""),
            start_s=float(r.get("start_s", 0.0)),
            slut_s=float(r.get("slut_s", 0.0)),
            a=a_ruta,
            barande=bool(funktion in ("krok", "vandning", "punchline")),
        ))

    skarmtext = []
    for idx, st in enumerate(sem.get("skarmtext") or []):
        sid = str(st.get("tagning", "")).lower()
        funktion = (tagn_sem.get(sid) or {}).get("funktion", "")
        txt = st.get("text", "")
        bar = bool(funktion in ("krok", "vandning", "punchline") or "vs" in txt.lower())
        skarmtext.append(dict(id=f"st_{idx+1}", tagning=sid, text=txt, barande=bar, funktion=funktion))

    scener = []
    for t in tagningar:
        sid = t["id"]
        a0, b0 = t["ut"]
        ts = tagn_sem.get(sid, {})
        funktion = ts.get("funktion") or "scen"
        sc_rep = [r for r in repliker if r["tagning"] == sid]
        sc_txt = [x for x in skarmtext if x["tagning"] == sid]
        scener.append(dict(
            tagning=sid,
            ut=[a0, b0],
            start_s=round(a0 / fps, 2),
            slut_s=round(b0 / fps, 2),
            langd_s=round((b0 - a0) / fps, 2),
            vem=[p["id"] for p in t["personer"]] or ["ingen_person_i_bild"],
            var=plats_txt,
            funktion=funktion,
            vad=ts.get("vad") or f"Tagning {sid}",
            repliker=[r["text"] for r in sc_rep],
            skarmtext=[x["text"] for x in sc_txt],
            barande=bool(funktion in ("krok", "vandning", "punchline")),
        ))

    return dict(
        karna=karna,
        sammanfattning=samman,
        tal_finns=bool(kl_info.get("tal_finns", bool(repliker))),
        sprak=kl_info.get("sprak", "okand"),
        repliker=repliker,
        skarmtext=skarmtext,
        scener=scener,
        roller=personer_meta,
        rum_relationer={"tro": recept.tro},
        semantik_kalla=str(semantik_fil) if semantik_fil else str(ingest / "semantik/semantik.json"),
    )
'''


def main():
    src = ORIG.read_text(encoding="utf-8")
    ny = src
    for gammal, nytt in ERSATT:
        n = ny.count(gammal)
        if n != 1:
            raise SystemExit(f"Patchen hittade {n} träffar (kräver 1) för:\n{gammal[:220]}")
        ny = ny.replace(gammal, nytt)
    # Sätt in _bygg_mening_och_medielager direkt efter _ladda_exakt_semantik
    mark = "def kompilera_scenpaket("
    assert ny.count(mark) == 1
    ny = ny.replace(mark, MENING_HJALP + "\n\n" + mark)

    huvud = (
        "# STEG-PATCH (Del 3, Neon runda 2): KOPIA av forvarld_karna/scen_brygga.py med S1-S5.\n"
        "# Generera om med motpart/runda-2-neon/steg_bygg_patch.py; originalet är orört.\n"
    )
    out_py = HIT / "steg_scen_brygga.py"
    out_diff = HIT / "steg_scen_brygga.diff"
    out_py.write_text(huvud + ny, encoding="utf-8")
    diff = difflib.unified_diff(
        src.splitlines(keepends=True),
        ny.splitlines(keepends=True),
        fromfile="forvarld_karna/scen_brygga.py",
        tofile="motpart/runda-2-neon/steg_scen_brygga.py",
    )
    out_diff.write_text("".join(diff), encoding="utf-8")
    print("Skrev:", out_py, "och", out_diff)


if __name__ == "__main__":
    main()
