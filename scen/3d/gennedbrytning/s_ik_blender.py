"""0031, utförande nivå 1 (körs i Blender efter mhr_rig): IK för en speglad hand. mhr_rig.py och kedjans kod oförändrade.

  blender -b <scen.blend> --python scen/3d/gennedbrytning/s_ik_blender.py -- <plan.json> <referens-samspel.json> [--overgang 6]
För varje IK-fönster i planens scener (scener[].spegling.ik: ben, mal_ben, ut-rutor): ett mål (empty) följer referensens mal_ben
(den hand som gjorde handlingen före speglingen, ur j_samspel_blender.py på den ospeglade planen) ruta för ruta, och en IK-begränsning
(kedja 2: underarm och överarm) på benets förälder drar handleden dit. Inflytandet tonas in och ut över --overgang rutor.
Sparar scen.blend på plats. Ut: utskrift IK_KLAR med antal fönster.
"""
import json, sys
import bpy

a = sys.argv[sys.argv.index('--') + 1:]; plan = json.load(open(a[0], encoding='utf-8')); ref = {r['ruta']: r for r in json.load(open(a[1], encoding='utf-8'))['rutor']}
ov = int(a[a.index('--overgang') + 1]) if '--overgang' in a else 6
sc = bpy.context.scene; n = 0
for d in plan.get('scener') or []:
    sp = d.get('spegling')
    if not sp: continue
    arm = bpy.data.objects.get(f'person:{sp["person"]}') or next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name.startswith('person:'))
    for f in sp['ik']:
        ben = next(b for b in arm.pose.bones if b.name == f['ben'] or b.name.endswith(':' + f['ben']))
        under = ben.parent if ben.parent and 'twist' not in ben.parent.name else ben.parent.parent
        mal = bpy.data.objects.new(f'ik_mal:{f["namn"]}', None); sc.collection.objects.link(mal)
        u0, u1 = f['ut']
        for u in range(u0 - ov, u1 + ov):
            r = ref.get(u)
            if r and f['mal_ben'] in r['leder']: mal.location = r['leder'][f['mal_ben']]['huvud']; mal.keyframe_insert('location', frame=u)
        c = under.constraints.new('IK'); c.target = mal; c.chain_count = 2; c.use_tail = True; c.name = f'ik:{f["namn"]}'
        for u, w in ((u0 - ov - 1, 0.), (u0, 1.), (u1 - 1, 1.), (u1 + ov, 0.)):
            c.influence = w; c.keyframe_insert('influence', frame=u)
        n += 1
bpy.ops.wm.save_mainfile()
print('IK_KLAR', n)
