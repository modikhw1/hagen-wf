"""Kameratracking ur ett klipp med Blenders inbyggda camera solver (libmv). Personer maskas bort först.

Körs i GUI-Blender via MCP (klippredigerarens operatorer kräver ett CLIP_EDITOR-område).
Tunga steg körs som separata anrop, eftersom MCP-anrop över ~2 min får timeout:

    ns = runpy.run_path(r'...\\kamera_track.py')
    ns['forbered'](klipp, maskfil)  # klipp, scen och CLIP_EDITOR-område
    ns['detektera'](steg=15)        # punkter var 15:e bildruta, utanför personen
    ns['spara'](...)                # spåra framåt och bakåt (kan behöva delas upp i omgångar: grupper=...)
    ns['rensa']()                   # tysta markörer på personen och ta bort korta spår (täckningen säkras)
    ns['los']()                     # lös kameran med förfinad fokallängd och k1
    ns['exportera'](utfil)          # kamera.json (världsmatris per bildruta, fokal, sensor, fel) + kameraobjekt i scenen

Maskfil: .npy (N × h × w bool), där True betyder person. Tas fram med YOLO-seg; se scen/3d/klipp2.
"""
import bpy, json, time
import numpy as np

NS = bpy.app.driver_namespace


def forbered(klipp, maskfil, namn='spar', fokal_gissning=22.0):
    sc = bpy.data.scenes.get(namn) or bpy.data.scenes.new(namn)
    bpy.context.window.scene = sc
    clip = bpy.data.movieclips.get(namn) or bpy.data.movieclips.load(klipp); clip.name = namn
    sc.active_clip = clip; sc.frame_start, sc.frame_end = 1, clip.frame_duration
    sc.render.fps = round(clip.fps); sc.render.resolution_x, sc.render.resolution_y = clip.size[:]
    s = clip.tracking.settings
    s.default_pattern_size = 25; s.default_search_size = 151; s.default_motion_model = 'Perspective'
    s.default_correlation_min = 0.8; s.default_margin = 20; s.use_default_brute = True; s.use_default_normalization = True
    clip.tracking.camera.sensor_width = 36.0; clip.tracking.camera.focal_length = fokal_gissning
    area = max(bpy.context.window.screen.areas, key=lambda a: a.width * a.height)
    NS['kt'] = dict(clip=clip.name, area=area, gammal=area.type, mask=np.load(maskfil))
    area.type = 'CLIP_EDITOR'; sp = area.spaces.active; sp.clip = clip; sp.mode = 'TRACKING'
    return clip.frame_duration


def _ctx():
    k = NS['kt']; area = k['area']; sp = area.spaces.active
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return bpy.data.movieclips[k['clip']], sp, bpy.context.temp_override(area=area, region=region, space_data=sp)


def _person(f, co):
    M = NS['kt']['mask']; n, h, w = M.shape
    x = int(co[0] * w); y = int((1 - co[1]) * h)
    return 0 <= x < w and 0 <= y < h and 0 <= f - 1 < n and bool(M[f - 1, y, x])


def detektera(steg=15, troskel=0.02, avstand=45):
    clip, sp, ctx = _ctx(); sc = bpy.context.scene; t = clip.tracking
    fore = {tr.name for tr in t.tracks}
    with ctx:
        for f in range(1, clip.frame_duration + 1, steg):
            sc.frame_set(f); sp.clip_user.frame_current = f
            bpy.ops.clip.select_all(action='DESELECT')
            bpy.ops.clip.detect_features(placement='FRAME', margin=30, threshold=troskel, min_distance=avstand)
        for tr in t.tracks: tr.select = tr.name not in fore and _person(tr.markers[0].frame, tr.markers[0].co)
        bpy.ops.clip.delete_track(confirm=False)
    NS['kt']['nya'] = sorted({(tr.markers[0].frame, tr.name) for tr in t.tracks if tr.name not in fore})
    return len(NS['kt']['nya'])


def spara(max_sekunder=90):
    """Spårar nyskapade grupper framåt och bakåt. Avbryter efter max_sekunder; anropa igen tills den returnerar 0."""
    clip, sp, ctx = _ctx(); sc = bpy.context.scene; t = clip.tracking; t0 = time.time()
    kvar = NS['kt'].get('nya', [])
    with ctx:
        while kvar and time.time() - t0 < max_sekunder:
            f = kvar[0][0]; grupp = {n for ff, n in kvar if ff == f}
            for d in (False, True):
                sc.frame_set(f); sp.clip_user.frame_current = f
                for tr in t.tracks: tr.select = tr.name in grupp
                bpy.ops.clip.track_markers(backwards=d, sequence=True)
            kvar = [x for x in kvar if x[0] != f]
    NS['kt']['nya'] = kvar
    return len(kvar)


def rensa(min_langd=20, lang=60, per_fonster=25, fonster=15, tak=300):
    clip, sp, ctx = _ctx(); t = clip.tracking
    for tr in t.tracks:
        for m in tr.markers:
            if not m.mute and _person(m.frame, m.co): m.mute = True
    L = {tr.name: sum(1 for m in tr.markers if not m.mute) for tr in t.tracks}
    behall = set()   # täckning först: de längsta spåren per fönster, sedan fyll upp till taket med långa spår
    for f in range(1, clip.frame_duration + 1, fonster):
        k = sorted([tr for tr in t.tracks if (m := tr.markers.find_frame(f)) and not m.mute], key=lambda tr: -L[tr.name])
        behall |= {tr.name for tr in k[:per_fonster]}
    for n, l in sorted(L.items(), key=lambda x: -x[1]):
        if len(behall) >= tak: break
        if l >= lang: behall.add(n)
    behall = {n for n in behall if L[n] >= min_langd}
    with ctx:
        for tr in t.tracks: tr.select = tr.name not in behall
        bpy.ops.clip.delete_track(confirm=False)
    return len(t.tracks), [sum(1 for tr in t.tracks if (m := tr.markers.find_frame(f)) and not m.mute) for f in range(1, clip.frame_duration + 1, fonster)]


def los(fokal_gissning=22.0, fel_grans=None):
    """Löser kameran. Med fel_grans tas spår med större fel bort, och lösningen görs om en gång."""
    clip, sp, ctx = _ctx(); t = clip.tracking; s = t.settings
    s.use_keyframe_selection = True; s.refine_intrinsics_focal_length = True; s.refine_intrinsics_radial_distortion = True
    t.camera.focal_length = fokal_gissning; t.camera.k1 = t.camera.k2 = t.camera.k3 = 0
    with ctx:
        bpy.ops.clip.solve_camera()
        if fel_grans and t.reconstruction.is_valid:
            for tr in t.tracks: tr.select = tr.has_bundle and tr.average_error > fel_grans
            bpy.ops.clip.delete_track(confirm=False); bpy.ops.clip.solve_camera()
    r = t.reconstruction
    return dict(giltig=r.is_valid, medelfel_px=round(r.average_error, 3), kameror=len(r.cameras), bildrutor=clip.frame_duration,
                fokal_mm=round(t.camera.focal_length, 2), k1=round(t.camera.k1, 4), spar=len(t.tracks))


def exportera(utfil):
    """kamera.json + kameraobjektet 'kam:spar' med nycklad rörelse (Blenders setup_tracking_scene-logik, utan att ändra resten)."""
    clip, sp, ctx = _ctx(); t = clip.tracking; r = t.reconstruction; sc = bpy.context.scene
    with ctx:
        bpy.ops.clip.setup_tracking_scene()
    cam = sc.camera
    ut = dict(klipp=clip.filepath, fps=clip.fps, bredd=clip.size[0], hojd=clip.size[1], sensor_mm=t.camera.sensor_width,
              fokal_mm=t.camera.focal_length, k1=t.camera.k1, medelfel_px=r.average_error, upp='Z', ramar=[])
    for f in range(1, clip.frame_duration + 1):
        sc.frame_set(f)
        ut['ramar'].append(dict(f=f, lost=bool(r.cameras.find_frame(frame=f)), matris=[list(rad) for rad in cam.matrix_world]))
    ut['punkter'] = [dict(namn=tr.name, xyz=list(tr.bundle), fel=tr.average_error) for tr in t.tracks if tr.has_bundle]
    with open(utfil, 'w', encoding='utf-8') as fh: json.dump(ut, fh)
    return len(ut['ramar']), sum(x['lost'] for x in ut['ramar']), len(ut['punkter'])
