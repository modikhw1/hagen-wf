"""Analys av en feed-forward-rekonstruktion (modal_ffrek_vggt.py): kamerapose per bild, punktmoln, golvplan, kluster av tagningar, översiktsbild.
Kör (från scen/):  .venv/Scripts/python.exe -X utf8 3d/ingest/ffrek_analys.py 3d/ingest/ut/b-tilltal-ravara-tagningar/ffrek/vggt
Skriver i mappen: kameror.json, moln.ply, analys.json, oversikt.png."""
import json, sys
import numpy as np

D = sys.argv[1]
K = json.load(open(f'{D}/korning.json', encoding='utf8')); M = K['bilder']
Z = np.load(f'{D}/vggt_ra.npz')
E, Kin, dep, dconf, img = Z['extrinsic'], Z['intrinsic'], Z['depth'].astype(np.float32)[..., 0], Z['depth_conf'].astype(np.float32), Z['images']
S, _, H, W = img.shape
rng = np.random.default_rng(0)

# kameror: extrinsic = kamera-från-värld (OpenCV). Inverterar till värld-från-kamera.
T = []; C = []; F = []; Y = []
for e in E:
    R, t = e[:, :3], e[:, 3]; Tw = np.eye(4); Tw[:3, :3] = R.T; Tw[:3, 3] = -R.T @ t
    T.append(Tw); C.append(Tw[:3, 3]); F.append(Tw[:3, 2]); Y.append(-Tw[:3, 1])
T, C, F, Y = map(np.array, (T, C, F, Y))

# punktmoln ur djup + kamera (README: säkrare än punkthuvudet). Utesluter maskerade (svarta) och utfyllda (vita) pixlar och lägsta konfidensen.
uu, vv = np.meshgrid(np.arange(W), np.arange(H))
P = []; Cl = []; Ix = []
giltig_andel = []
for i in range(S):
    rgb = img[i].transpose(1, 2, 0)
    ok = ~((rgb.max(-1) <= 6) | (rgb.min(-1) >= 250)) & (dep[i] > 0)
    giltig_andel.append(float(ok.mean()))
    thr = np.percentile(dconf[i][ok], 40) if ok.any() else np.inf
    ok &= dconf[i] >= thr
    z = dep[i][ok]; fx, fy, cx, cy = Kin[i][0, 0], Kin[i][1, 1], Kin[i][0, 2], Kin[i][1, 2]
    pc = np.stack([(uu[ok] - cx) / fx * z, (vv[ok] - cy) / fy * z, z], -1)
    pw = pc @ T[i][:3, :3].T + T[i][:3, 3]
    P.append(pw); Cl.append(rgb[ok]); Ix.append(np.full(len(pw), i))
P, Cl, Ix = np.concatenate(P), np.concatenate(Cl), np.concatenate(Ix)

# upp-riktning: medel av kamerornas -Y (telefonen hålls ungefär upprätt), förfinas med golvets normal
up0 = Y.mean(0); up0 /= np.linalg.norm(up0)
sub = P[rng.choice(len(P), min(len(P), 60000), replace=False)]
skala_ref = np.median(np.linalg.norm(sub - C.mean(0), axis=1))   # typiskt avstånd kamera->scen i modellens enheter
tol = 0.02 * skala_ref
best = None
for _ in range(4000):
    a, b, c = sub[rng.choice(len(sub), 3, replace=False)]
    n = np.cross(b - a, c - a); nn = np.linalg.norm(n)
    if nn < 1e-9: continue
    n /= nn
    if n @ up0 < 0: n = -n
    if n @ up0 < np.cos(np.radians(25)): continue
    d0 = -n @ a
    hc = C @ n + d0
    if (hc <= 0).any(): continue                    # alla kameror ovanför planet
    inl = np.abs(sub @ n + d0) < tol
    # golvet = lägsta stora horisontella planet: viktar inliers, men kräver att få punkter ligger under
    under = (sub @ n + d0 < -3 * tol).mean()
    score = inl.sum() * (1 - min(1, under * 5))
    if best is None or score > best[0]: best = (score, n, d0, inl.sum(), under)
_, n, d0, ninl, under = best
inl = np.abs(sub @ n + d0) < tol
A = np.c_[sub[inl], np.ones(inl.sum())]; _, _, vt = np.linalg.svd(A); pl = vt[-1]; pl /= np.linalg.norm(pl[:3])
if pl[:3] @ up0 < 0: pl = -pl
n, d0 = pl[:3], pl[3]
hojd_kam = C @ n + d0
hojd_pkt = sub @ n + d0

# horisontella nivåer ovanför golvet (disk/våg): toppar i höjdhistogrammet
hist, kant = np.histogram(hojd_pkt[(hojd_pkt > 0.15 * np.median(hojd_kam)) & (hojd_pkt < 1.3 * np.median(hojd_kam))], bins=60)
mid = (kant[:-1] + kant[1:]) / 2; toppar = [float(mid[j]) for j in np.argsort(hist)[::-1][:4]]

# golvbas för översikten
e1 = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < .9 else np.cross(n, [1.0, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
fram_mean = F.mean(0); fram_mean -= (fram_mean @ n) * n
if np.linalg.norm(fram_mean) > 1e-6:                  # e2 pekar i genomsnittlig blickriktning (in i scenen)
    e2 = fram_mean / np.linalg.norm(fram_mean); e1 = np.cross(e2, n)

tag = [m['tagning'] for m in M]; tagn = list(dict.fromkeys(tag))
per = {}
for s in tagn:
    idx = [i for i, t in enumerate(tag) if t == s]
    c = C[idx].mean(0); f = F[idx].mean(0); f /= np.linalg.norm(f)
    spr = float(np.linalg.norm(C[idx] - c, axis=1).max())
    vink = float(np.degrees(np.arccos(np.clip(F[idx] @ f, -1, 1))).max())
    fh = f - (f @ n) * n; fh /= np.linalg.norm(fh)
    per[s] = dict(bilder=idx, centrum=c.tolist(), blick=f.tolist(), kamerahojd=float(c @ n + d0), lutning_ned_grader=float(np.degrees(np.arcsin(-(f @ n)))),
                  plan_xy=[float(c @ e1), float(c @ e2)], plan_blick_grader=float(np.degrees(np.arctan2(fh @ e1, fh @ e2))),
                  spridning_inom_tagning=spr, vinkelspridning_inom_tagning_grader=vink,
                  konfidens_median=float(np.median([np.median(dconf[i]) for i in idx])))

json.dump(dict(bilder=[dict(**m, varld_fran_kamera=T[i].tolist(), intrinsics_518=Kin[i].tolist(), konfidens_median=float(np.median(dconf[i])),
                            konfidens_p90=float(np.percentile(dconf[i], 90)), giltig_andel=giltig_andel[i]) for i, m in enumerate(M)],
               not_konvention='OpenCV (x höger, y ned, z fram), värld = första bildens kamera, modellens enheter (inte metriska). intrinsics gäller 518x518-utfylld bild.'),
          open(f'{D}/kameror.json', 'w', encoding='utf8'), indent=1, ensure_ascii=False)


def skala_for(namn, kamh_m):
    return kamh_m / float(np.median(hojd_kam))


def kluster(skala):
    par = []; gr = {s: {s} for s in tagn}
    for a in range(len(tagn)):
        for b in range(a + 1, len(tagn)):
            pa, pb = per[tagn[a]], per[tagn[b]]
            dist = float(np.linalg.norm(np.array(pa['centrum']) - np.array(pb['centrum'])) * skala)
            vink = float(np.degrees(np.arccos(np.clip(np.dot(pa['blick'], pb['blick']), -1, 1))))
            par.append(dict(a=tagn[a], b=tagn[b], avstand_m=round(dist, 2), vinkel_grader=round(vink, 1), samma=dist < .5 and vink < 30))
            if dist < .5 and vink < 30:
                u = gr[tagn[a]] | gr[tagn[b]]
                for s in u: gr[s] = u
    return par, sorted({tuple(sorted(g, key=lambda x: int(x[1:]))) for g in gr.values()}, key=lambda g: int(g[0][1:]))


# skala: VGGT är inte metrisk. Två alternativa antaganden redovisas: kamerahöjd 1,45 m (ingestens antagande) och högsta horisontella nivå = disk 0,9 m.
skalor = {'kamerahojd_1.45m': 1.45 / float(np.median(hojd_kam))}
disk = [t for t in toppar if t < 0.95 * np.median(hojd_kam)]
if disk: skalor['disk_0.9m_(starkaste_nivå_under_kameran)'] = 0.9 / disk[0]
res = dict(golv=dict(normal=n.tolist(), d=float(d0), inliers_andel=float(inl.mean()), andel_punkter_under=float(under), vinkel_mot_kamera_upp_grader=float(np.degrees(np.arccos(np.clip(n @ up0, -1, 1))))),
           kamerahojd_modellenheter=dict(median=float(np.median(hojd_kam)), min=float(hojd_kam.min()), max=float(hojd_kam.max())),
           horisontella_nivaer_modellenheter=toppar, skalor_m_per_enhet=skalor, tagningar=per, kluster={})
for k, s in skalor.items():
    par, gr = kluster(s); res['kluster'][k] = dict(grupper=[list(g) for g in gr], par=par,
                                                   kamerahojd_m={t: round(per[t]['kamerahojd'] * s, 2) for t in tagn},
                                                   disk_niva_m=[round(t * s, 2) for t in toppar])
json.dump(res, open(f'{D}/analys.json', 'w', encoding='utf8'), indent=1, ensure_ascii=False)

# ply (nedsamplat, binärt)
k = rng.choice(len(P), min(len(P), 400000), replace=False)
hdr = f'ply\nformat binary_little_endian 1.0\nelement vertex {len(k)}\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n'
rec = np.empty(len(k), dtype=[('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('r', 'u1'), ('g', 'u1'), ('b', 'u1')])
rec['x'], rec['y'], rec['z'] = P[k].T; rec['r'], rec['g'], rec['b'] = Cl[k].T
with open(f'{D}/moln.ply', 'wb') as fh: fh.write(hdr.encode()); fh.write(rec.tobytes())

# översikt ovanifrån (golvplanet)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
s = skalor['kamerahojd_1.45m']
k2 = rng.choice(len(P), min(len(P), 80000), replace=False)
x, y, h = (P[k2] @ e1) * s, (P[k2] @ e2) * s, (P[k2] @ n + d0) * s
fig, ax = plt.subplots(1, 2, figsize=(17, 8.5))
ax[0].scatter(x, y, c=Cl[k2] / 255, s=.4, alpha=.5, linewidths=0)
cm = plt.get_cmap('tab20')
ax[1].scatter(x, y, c=[cm(tagn.index(tag[i]) / max(1, len(tagn) - 1) * .95) for i in Ix[k2]], s=.4, alpha=.35, linewidths=0)
for a in ax:
    for i in range(S):
        col = cm(tagn.index(tag[i]) / max(1, len(tagn) - 1) * .95)
        cx_, cy_ = C[i] @ e1 * s, C[i] @ e2 * s; fh = F[i] - (F[i] @ n) * n
        a.arrow(cx_, cy_, fh @ e1 * .35, fh @ e2 * .35, color=col, width=.012, head_width=.06, length_includes_head=True)
    for t in tagn:
        px, py = np.array(per[t]['plan_xy']) * s; a.annotate(t, (px, py), fontsize=9, color=cm(tagn.index(t) / max(1, len(tagn) - 1) * .95), xytext=(4, -10), textcoords='offset points', weight='bold')
    a.set_aspect('equal'); a.set_xlabel('m (antagen kamerahöjd 1,45 m)'); a.grid(alpha=.3)
lo, hi = np.percentile(x, [1, 99]), np.percentile(y, [1, 99]); cxs = np.array([C[i] @ e1 * s for i in range(S)]); cys = np.array([C[i] @ e2 * s for i in range(S)])
for a in ax: a.set_xlim(min(lo[0], cxs.min()) - .3, max(lo[1], cxs.max()) + .3); a.set_ylim(min(hi[0], cys.min()) - .3, max(hi[1], cys.max()) + .3)
ax[0].set_title('VGGT, alla 11 tagningar i ett pass: punktmoln ovanifrån (färg = RGB)'); ax[1].set_title('samma, punkter färgade per tagning; pilar = kamerans blick')
plt.tight_layout(); plt.savefig(f'{D}/oversikt.png', dpi=110)
print(json.dumps({k: res[k] for k in ['golv', 'kamerahojd_modellenheter', 'horisontella_nivaer_modellenheter', 'skalor_m_per_enhet']}, indent=1, ensure_ascii=False))
for k_, v in res['kluster'].items(): print(k_, v['grupper'], v['kamerahojd_m'])
for t in tagn: print(t, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in per[t].items() if kk not in ('bilder', 'centrum', 'blick')})
