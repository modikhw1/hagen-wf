"""Styrmaterial ur Blender-förvisualiseringen (kör efter bygg_scen.py, helst med bakad rörelse).

Ut i scen/3d/blender/ut/:
  blockout.mp4              hela klippet, Workbench (materialfärger), klipp på källans bildrutor, ORIGINALLJUDET under
  tagning_<id>.mp4          samma, en fil per tagning, med tagningens eget ljudintervall (som referens till videomodellen)
  ljud_<id>.wav             tagningens originalljud (röstreferens / läppsynk)
  forsta_<id>.png           första bildrutan per tagning i full upplösning (startbild för bild-till-video)
  djup_<id>.png             djupkarta för samma bildruta (nära = ljus)
  promptpaket.md            tagningslista + instruktion till ChatGPT (PS2-SOP:n) för prompten

Kör: blender -b scen/3d/blender/scen.blend --python scen/3d/blender/rendera.py -- [--bara-bilder] [--skala 100]
eller live via MCP: runpy.run_path(..., init_globals={'ARGV': [...]}, run_name='__main__')
"""
import json, subprocess, sys, shutil
from pathlib import Path
import bpy

HIT = Path(__file__).resolve().parent if '__file__' in globals() else Path(r'C:\Users\praiseworthy\Desktop\hagen-wf\scen\3d\blender')
A = globals().get('ARGV') or (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
HIT = Path(A[A.index('--arbetsut') + 1]).resolve() if '--arbetsut' in A else HIT
UT = Path(A[A.index('--ut') + 1]).resolve() if '--ut' in A else HIT / 'ut'; UT.mkdir(parents=True, exist_ok=True)
SKALA = int(A[A.index('--skala') + 1]) if '--skala' in A else 100
WINDOWS_VIDEO = ['-profile:v', 'main', '-pix_fmt', 'yuv420p', '-ar', '48000', '-ac', '2', '-movflags', '+faststart'] if '--windows-video' in A else []
sc = bpy.context.scene
L = json.loads((HIT / 'tagningslista.json').read_text(encoding='utf-8'))


def motor(namn):
    try: sc.render.engine = namn
    except TypeError as e: raise SystemExit(f'motor {namn}: {e}')


def workbench():
    motor('BLENDER_WORKBENCH')
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.show_cavity = False
    sc.display.render_aa = '8'
    sc.render.resolution_percentage = SKALA; sc.render.film_transparent = False


def stillbild(fil, f, kam):
    sc.frame_set(f); sc.camera = kam
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = str(fil)
    bpy.ops.render.render(write_still=True)


def djup(fil, f, kam):
    """Djup via Workbench-Z i kompositorn: normaliserat och inverterat (nära = ljust)."""
    sc.frame_set(f); sc.camera = kam
    vl = sc.view_layers[0]; vl.use_pass_z = True
    sc.use_nodes = True
    tree = sc.node_tree if hasattr(sc, 'node_tree') and sc.node_tree else None
    if tree is None:   # Blender 5: kompositorn är en nodgrupp på scenen
        tree = bpy.data.node_groups.new('djup', 'CompositorNodeTree'); sc.compositing_node_group = tree
    tree.nodes.clear()
    rl = tree.nodes.new('CompositorNodeRLayers'); norm = tree.nodes.new('CompositorNodeNormalize'); inv = tree.nodes.new('CompositorNodeInvert')
    tree.links.new(rl.outputs['Depth'], norm.inputs[0]); tree.links.new(norm.outputs[0], inv.inputs['Color'])
    try:
        ut = tree.nodes.new('CompositorNodeComposite'); tree.links.new(inv.outputs[0], ut.inputs[0])
    except RuntimeError:
        ut = tree.nodes.new('NodeGroupOutput'); tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor'); tree.links.new(inv.outputs[0], ut.inputs[0])
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = str(fil)
    bpy.ops.render.render(write_still=True)
    sc.use_nodes = False
    if hasattr(sc, 'compositing_node_group'): sc.compositing_node_group = None


def video():
    """Hela tidslinjen som PNG-sekvens (kamerabyten via markörer), sedan ffmpeg med originalljudet."""
    tmp = (UT / 'ramar').resolve()
    if tmp.parent != UT.resolve(): raise ValueError('Unsafe render cache path')
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = str(tmp / 'f')
    sc.render.use_file_extension = True
    bpy.ops.render.render(animation=True)
    ljud = HIT / 'ljud-original.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-start_number', str(sc.frame_start), '-i', str(tmp / 'f%04d.png'), '-i', str(ljud),
                    '-map', '0:v', '-map', '1:a', '-af', 'apad', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '160k', *WINDOWS_VIDEO, '-shortest', str(UT / 'blockout.mp4')], check=True)
    for t in L['tagningar']:
        s0, d = t['start_s'], t['langd_s']
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s0:.4f}', '-t', f'{d:.4f}', '-i', str(UT / 'blockout.mp4'), '-c:v', 'libx264', '-crf', '18', '-c:a', 'aac', *WINDOWS_VIDEO, str(UT / f"tagning_{t['id']}.mp4")], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s0:.4f}', '-t', f'{d:.4f}', '-i', str(ljud), str(UT / f"ljud_{t['id']}.wav")], check=True)
    shutil.rmtree(tmp, ignore_errors=True)


def promptpaket():
    rader = ['# Promptpaket (klistra in i ChatGPT tillsammans med PS2-SOP:n)', '',
             'Klistra först in hela `unemployed_corp/spar/ps2_viral_sop.txt`. Klistra sedan in det här. Bifoga `forsta_<id>.png` (layout och utsnitt), '
             '`tagning_<id>.mp4` (rörelse och tajming, om modellen tar videoreferens) och `ljud_<id>.wav` (röst och läppsynk) per tagning.', '',
             '**Låsta krav utöver SOP:n:**',
             '- Varje tagning ska ha exakt den angivna längden och klippen ligga på angivna sekunder.',
             '- Kropparnas rörelse, gester och munrörelser ska följa referensvideon bildruta för bildruta.',
             '- Repliken ska passa originalljudet ord för ord vid angivna tider.',
             '- Placering av personer, bord och föremål ska vara exakt som i startbilden.',
             '- Inga extra repliker, ingen musik och ingen textning.', '']
    for t in L['tagningar']:
        k = t['kamera']
        rader.append(f"## {t['id']} ({t['beat']}): {t['start_s']:.2f}–{t['slut_s']:.2f} s ({t['langd_s']:.2f} s, bildruta {t['bildrutor'][0]}–{t['bildrutor'][1]})")
        rader.append(f"- Kamera: {k['utsnitt']}, {k['rorelse']}, {k['objektiv_mm']} mm ekv. ({k['fov']}°), {k['avstand_m']} m från motivet, {k['hojd_mot_ogon_m']} m över ögonhöjd, lutning {k['lutning']}°.")
        rader.append('- I bild: ' + ', '.join(f"{a['id']} ({a['roll']}{', sitter' if a['sitter'] else ''})" for a in t['i_bild']) + (f"; talar utanför bild: {', '.join(t['talare_utanfor_bild'])}" if t['talare_utanfor_bild'] else ''))
        for r in t['repliker']:
            ord_ = ' '.join(f"{w['w']}[{w['start']:.2f}]" for w in r['ord'])
            rader.append(f"- {r['talare']}: \"{r['text']}\"  ord (scentid s): {ord_}")
        rader.append('')
    (UT / 'promptpaket.md').write_text('\n'.join(rader), encoding='utf-8')


if __name__ == '__main__':
    workbench()
    for t in L['tagningar']:
        kam = bpy.data.objects['kam:' + t['id']]; f0 = t['bildrutor'][0]
        stillbild(UT / f"forsta_{t['id']}.png", f0, kam)
        djup(UT / f"djup_{t['id']}.png", f0, kam)
        workbench()
    if '--bara-bilder' not in A: video()
    promptpaket()
    print('rendera: klar ->', UT)
