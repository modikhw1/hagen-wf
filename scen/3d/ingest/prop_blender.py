"""Blender-geometri för propbankens former och upplösta propnycklar.

Körs endast i en egen bakgrunds-Blender via mhr_rig.py.
"""
import bpy
from mathutils import Matrix, Vector

def mat(farg):
    m=bpy.data.materials.new('prop:'+farg);m.diffuse_color=tuple(int(farg[i:i+2],16)/255 for i in (1,3,5))+(1,)
    return m

def prim(form, pos, dim, color, parent, name):
    if form=='cylinder':bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.5,depth=1)
    elif form=='ellipsoid':bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.5)
    else:bpy.ops.mesh.primitive_cube_add(size=1)
    ob=bpy.context.object;ob.name=name;ob.parent=parent;ob.location=pos;ob.dimensions=dim;ob.data.materials.append(mat(color))
    if form=='ellipsoid':
        for p in ob.data.polygons:p.use_smooth=True
    return ob

def bygg(plan):
    for p in plan.get('props',[]):
        if not p.get('byggd'):continue
        root=bpy.data.objects.new('prop:'+p['id']+':'+p['scen'],None);bpy.context.collection.objects.link(root)
        root['semantisk_typ']=p['prop_typ'];root['ursprung']='Parametrisk bank, uppmätta regioner och antagna djup/grepp; se plan.json'
        root['grepp_m']=p['bank']['grepp'];root.rotation_mode='QUATERNION'
        size=Vector(p['matt_m']);objects=[]
        for i,d in enumerate(p['bank']['delar']):
            pos=[d['pos'][j]*size[j] for j in range(3)];dim=[d['matt'][j]*size[j] for j in range(3)]
            objects.append(prim(d['form'],pos,dim,d['farg'],root,root.name+':'+str(i)))
        if p.get('kamerahand'):
            # Grov underarm och hand. Spårbox, inte en ny kroppsskattning.
            hand=prim('ellipsoid',[0,-size.y*.2,-.045],[.075,.105,.045],'#c49a7c',root,root.name+':kamerahand');objects.append(hand)
            a=Vector((0,-size.y*.2,-.07));b=Vector((-.06,-.42,.10));v=b-a
            arm=prim('cylinder',(a+b)/2,[.06,.06,v.length],'#668497',root,root.name+':underarm')
            arm.rotation_euler=v.to_track_quat('Z','Y').to_euler();objects.append(arm)
        for o in objects:
            o.hide_render=o.hide_viewport=True;o.keyframe_insert('hide_render',frame=-1);o.keyframe_insert('hide_viewport',frame=-1)
        for k in p['nycklar']:
            root.matrix_world=Matrix(k['matris']);f=k['ut'];root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_quaternion',frame=f)
            for o in objects:
                o.hide_render=o.hide_viewport=not k['synlig'];o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
        for o in objects:
            o.hide_render=o.hide_viewport=True;o.keyframe_insert('hide_render',frame=p['synlig_ut'][1]);o.keyframe_insert('hide_viewport',frame=p['synlig_ut'][1])
