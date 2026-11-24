"""Skapar g7_scen_brygga.py (patchad KOPIA av forvarld_karna/scen_brygga.py) och g7_scen_brygga.diff.

Originalet ändras inte. Varje ersättning kräver exakt en träff i originalet, annars avbryts skriptet, så att patchen
inte tyst glider om Argon ändrar filen.

Patchar (motiveras i G7.md):
  P1 kappa: skala bara bålens DJUP med f_px/f_sam (SAM:s egen fokal ur sekvensen) i stället för hela bål-translationen
     med f_sann/f_kedja. Bevarar bålens 2D-läge exakt och lemmarnas till första ordningen.
  P2 kamerahöjd: ingen klämning vid 0,92 m som flyttar kroppen relativt kameran; konflikten loggas som beslut.
  P3 G7: trohet mäts mot oberoende 2D (g7_oberoende.mat_paket) på det SLUTLIGA paketet, efter disk-skjutning.
  P4 grindar: en rad per (tagning, person) i stället för att sista personen skriver över raden.
Kör: .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-1-claude\\g7_lag_patch.py
"""
import difflib
import pathlib

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parent.parent
ORIG = ROT / "forvarld_karna/scen_brygga.py"

ERSATT = [
    # --- sökvägar: kopian bor i motpart/, men ska importera forvarld_karna/ och byggsten/brygga/ som originalet
    ("HIT = pathlib.Path(__file__).resolve().parent\nROT = HIT.parent\n",
     "ROT = pathlib.Path(__file__).resolve().parents[2]   # G7-PATCH: kopian bor i motpart/runda-1-claude/\n"
     "HIT = ROT / \"forvarld_karna\"\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))\n"),
    # --- P1 kappa (första loopen: höjdmedianer)
    ("                bal_m = pose_f[sp2_ix, :3] / 100.0\n"
     "                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + kappa * (bal_m + (ct_raw @ F.T))\n"
     "                alla_w = (c_cam @ R_cam.T) + C_world\n"
     "                raw_fots.append",
     "                bal_m = pose_f[sp2_ix, :3] / 100.0\n"
     "                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + (bal_m + (ct_raw @ F.T)) * djup_skala  # G7-PATCH P1\n"
     "                alla_w = (c_cam @ R_cam.T) + C_world\n"
     "                raw_fots.append"),
    # --- P1 kappa (andra loopen: lederna som går in i paketet)
    ("                bal_m = pose_f[sp2_ix, :3] / 100.0\n"
     "                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + kappa * (bal_m + (ct_raw @ F.T))\n"
     "                alla_w = (c_cam @ R_cam.T) + C_world\n"
     "                if z_kropp",
     "                bal_m = pose_f[sp2_ix, :3] / 100.0\n"
     "                c_cam = (pose_f[:, :3] / 100.0 - bal_m) + (bal_m + (ct_raw @ F.T)) * djup_skala  # G7-PATCH P1\n"
     "                alla_w = (c_cam @ R_cam.T) + C_world\n"
     "                if z_kropp"),
    ("            q_seq = np.load(seq_fil)\n            n_seq = len(q_seq[\"pose\"])\n",
     "            q_seq = np.load(seq_fil)\n            n_seq = len(q_seq[\"pose\"])\n"
     "            # G7-PATCH P1: SAM skattade cam_t under sin egen fokal f_sam. Byte till renderfokal f_px med bevarad\n"
     "            # bildposition = skala bara djupet (F-ramens z) med f_px/f_sam. Originalet skalade x, y och z med\n"
     "            # kappa = f_sann/f_kedja, vilket flyttar bålen radiellt mot bildmitten med faktorn f_px/f_sam.\n"
     "            djup_skala = np.array([1.0, 1.0, f_px / float(q_seq[\"fokal\"])])\n"),
    # --- P2 kamerahöjd
    ("            if idx_p == 0:\n"
     "                ny_cz = max(0.92, C_world[2] + z_skift)\n"
     "                z_kam_delta = ny_cz - C_world[2]\n"
     "                C_world[2] = ny_cz\n"
     "                z_kropp = z_skift - z_kam_delta\n",
     "            if idx_p == 0:\n"
     "                # G7-PATCH P2: kamera och kropp flyttas alltid tillsammans (2D bevaras). Originalet klämde kameran\n"
     "                # vid 0,92 m och lade resten på kroppen, vilket flyttade kroppen nedåt i bild (gelato s1, notan s2/s6/s7).\n"
     "                ny_cz = C_world[2] + z_skift\n"
     "                if ny_cz < 0.92:\n"
     "                    beslut.append(dict(regel=\"R18_kamerahojd_konflikt\", person=pid, tagning=sid, kamera_z=round(float(ny_cz), 3),\n"
     "                                       orsak=\"Fot-/sitthöjden kräver kamerahöjd under 0,92 m; behålls för 2D-trohet och rapporteras.\"))\n"
     "                z_kam_delta = ny_cz - C_world[2]\n"
     "                C_world[2] = ny_cz\n"
     "                z_kropp = 0.0\n"),
    # --- P3 ärlig G7 efter all efterbehandling, före grindarna
    ("    ut_mapp.mkdir(parents=True, exist_ok=True)\n"
     "    paket_fil = ut_mapp / \"paket.json\"\n"
     "    paket_fil.write_text(json.dumps(paket, ensure_ascii=False, separators=(\",\", \":\")), encoding=\"utf-8\")\n",
     "    # G7-PATCH P3: trohet mot oberoende 2D (SAM-2D, YOLO-ruta/-mask) på det slutliga paketet.\n"
     "    import g7_oberoende\n"
     "    obs_d = json.loads(obs.model_dump_json())\n"
     "    for r in g7_oberoende.mat_paket(klipp_namn, paket, obs_d, ingest=ingest):\n"
     "        paket[\"trohet\"][f\"{r['tagning']}:{r['person']}\"] = dict(\n"
     "            metod=\"g7_oberoende\", led_med=r[\"led_med\"], led_p90=r[\"led_p90\"], i_box=r[\"i_box\"], iou=r[\"iou\"],\n"
     "            i_mask=r[\"i_mask\"], spok_andel=r[\"spok_andel\"], flaggad=r[\"flaggad\"], skal=r[\"skal\"])\n"
     "    ut_mapp.mkdir(parents=True, exist_ok=True)\n"
     "    paket_fil = ut_mapp / \"paket.json\"\n"
     "    paket_fil.write_text(json.dumps(paket, ensure_ascii=False, separators=(\",\", \":\")), encoding=\"utf-8\")\n"),
    # --- P4 en grindrad per person
    ("    rader = grindar.mat(paket)\n",
     "    import g7_oberoende\n    rader = g7_oberoende.grindar_per_person(paket)  # G7-PATCH P4\n"),
]


def main():
    src = ORIG.read_text(encoding="utf-8")
    ny = src
    for gammal, nytt in ERSATT:
        n = ny.count(gammal)
        if n != 1:
            raise SystemExit(f"Patchen hittade {n} träffar (kräver 1) för:\n{gammal[:200]}")
        ny = ny.replace(gammal, nytt)
    huvud = ('# G7-PATCH: KOPIA av forvarld_karna/scen_brygga.py med P1–P4 (se motpart/runda-1-claude/G7.md).\n'
             '# Ändra inte här för hand; generera om med g7_lag_patch.py.\n')
    (HIT / "g7_scen_brygga.py").write_text(huvud + ny, encoding="utf-8")
    diff = difflib.unified_diff(src.splitlines(keepends=True), ny.splitlines(keepends=True),
                                fromfile="forvarld_karna/scen_brygga.py", tofile="motpart/runda-1-claude/g7_scen_brygga.py")
    (HIT / "g7_scen_brygga.diff").write_text("".join(diff), encoding="utf-8")
    print("skrev g7_scen_brygga.py och g7_scen_brygga.diff")


if __name__ == "__main__":
    main()
