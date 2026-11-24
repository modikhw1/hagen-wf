"""Import evaluated X Bot animation, never retarget it. Blender frame i = scene time i/30.

Public integration: importera(bake_path, scen_path) adds actors only to the current scene.
Standalone: blender -b --factory-startup --python scen/3d/blender/importera_bake.py
           -- --output scen/3d/blender/bake.blend
"""
import argparse
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONV = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def mat(values):
    """three.js column-major -> mathutils row-major."""
    return Matrix(np.asarray(values, dtype=float).reshape(4, 4).T.tolist())


def trs(value):
    x, y, z, w = value['quaternion']
    return Matrix.LocRotScale(Vector(value['position']), Quaternion((w, x, y, z)), Vector(value['scale']))


def key_transform(obj, frame):
    obj.rotation_mode = 'QUATERNION'
    for key in ('location', 'rotation_quaternion', 'scale'):
        obj.keyframe_insert(key, frame=frame)


def key_visibility(obj, visible, frame):
    obj.hide_viewport = obj.hide_render = not visible
    for key in ('hide_viewport', 'hide_render'):
        obj.keyframe_insert(key, frame=frame)


def constant_keys(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    curves = list(getattr(action, 'fcurves', []) or [])
    if not curves:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves.extend(bag.fcurves)
    for curve in curves:
        for point in curve.keyframe_points:
            point.interpolation = 'CONSTANT'


def mesh_object(name, data, collection, transform=None):
    vertices = np.asarray(data['positions'], dtype=np.float32).reshape(-1, 3)
    if transform is not None:
        m = np.asarray(transform, dtype=np.float64)
        vertices = vertices @ m[:3, :3].T + m[:3, 3]
    triangles = np.asarray(data['indices'], dtype=np.int32).reshape(-1, 3)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], triangles.tolist())
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def material(name, color, vertex_color=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color[:3], 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color[:3], 1)
    shader.inputs['Roughness'].default_value = .8
    if vertex_color:
        attr = m.node_tree.nodes.new('ShaderNodeVertexColor')
        attr.layer_name = 'player_color'
        m.node_tree.links.new(attr.outputs['Color'], shader.inputs['Base Color'])
    return m


def linear_hex(color):
    rgb = [int(color.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]


def create_actor(actor_id, asset, look, collection):
    prefix = f'actor:{actor_id}'
    if bpy.data.objects.get(prefix):
        raise ValueError(f'{prefix} already exists; import into a scene without baked actors')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT / 'modeller/Xbot.glb'), import_pack_images=False)
    imported = set(bpy.data.objects) - before
    arm = next(o for o in imported if o.type == 'ARMATURE')
    # Keep the imported rest skeleton and its bone-axis heuristic. The player has
    # altered the mesh (shirt volume + hair), so use that exact exported geometry.
    for obj in imported - {arm}:
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    arm.name = prefix + ':rig'
    for c in list(arm.users_collection):
        c.objects.unlink(arm)
    collection.objects.link(arm)
    root = bpy.data.objects.new(prefix, None)
    collection.objects.link(root)
    root['actor_id'] = actor_id
    root['bake_frame_origin'] = 0
    root['shirt'] = look.get('shirt', '#8a8174')
    arm.parent = root
    arm.matrix_basis = Matrix.Identity(4)
    imported_bones = {b.name.removeprefix('mixamorig').lstrip(':'): b for b in arm.pose.bones}
    bone_lookup = {name: imported_bones[name] for name in asset['bones']}
    # C_b = (conv M_gl_bind)^-1 M_bl_rest. Includes importer bone-axis correction
    # and glTF's centimetre node scale. Proportion edits belong to the POSE.
    inverse_bind = dict(zip(asset['meshes'][0]['boneNames'], asset['meshes'][0]['boneInverses']))
    corrections = {name: (CONV @ mat(inverse_bind[name]).inverted()).inverted() @ bone.bone.matrix_local
                   for name, bone in bone_lookup.items()}
    objects = [root, arm]
    meshes = []
    for index, data in enumerate(asset['meshes']):
        obj = mesh_object(prefix + ':' + data['name'], data, collection, CONV @ mat(data['bindMatrix']))
        obj.parent = root
        modifier = obj.modifiers.new('Baked X Bot skeleton', 'ARMATURE')
        modifier.object = arm
        modifier.use_deform_preserve_volume = False  # same linear blend skinning as three.js
        groups = [obj.vertex_groups.new(name=bone_lookup[n].name) for n in data['boneNames']]
        si = np.asarray(data['skinIndices']).reshape(-1, 4)
        sw = np.asarray(data['skinWeights']).reshape(-1, 4)
        for v, (ids, weights) in enumerate(zip(si, sw)):
            for bi, weight in zip(ids, weights):
                if weight > 0:
                    groups[int(bi)].add([v], float(weight), 'REPLACE')
        color = data['color']
        if data['colors']:
            colors = np.asarray(data['colors'], dtype=np.float32).reshape(-1, 3)
            # The task explicitly asks for look.shirt (the player uses roleColor).
            # Keep the player's skin/trousers/shoes; only change the shirt colour.
            top = linear_hex(look.get('shirt', '#8a8174'))
            for v, (ids, weights) in enumerate(zip(si, sw)):
                regions = {}
                for bi, weight in zip(ids, weights):
                    n = data['boneNames'][int(bi)]
                    r = 'skin' if any(x in n for x in ('Head', 'Neck', 'Eye', 'Hand')) else 'shoes' if any(x in n for x in ('Foot', 'Toe')) else 'bottom' if any(x in n for x in ('Hips', 'UpLeg', 'Leg')) else 'top'
                    regions[r] = regions.get(r, 0) + weight
                if max(regions, key=regions.get) == 'top':
                    colors[v] = np.asarray(top) * (.82 if 'Joints' in data['name'] else 1)
            attr = obj.data.color_attributes.new(name='player_color', type='FLOAT_COLOR', domain='POINT')
            rgba = np.column_stack((colors, np.ones(len(colors)))).astype(np.float32)
            attr.data.foreach_set('color', rgba.ravel())
        if data['colors']:
            # Workbench's MATERIAL mode ignores shader vertex attributes. Give it
            # the same region palette, while Eevee/Cycles still interpolate the
            # exact vertex colours through the shader at region boundaries.
            palette = np.unique(np.round(colors, 6), axis=0)
            for pindex, pcolor in enumerate(palette):
                obj.data.materials.append(material(f'{obj.name}:region{pindex}', pcolor, True))
            triangles = np.asarray(data['indices']).reshape(-1, 3)
            means = colors[triangles].mean(axis=1)
            ids = np.square(means[:, None, :] - palette[None, :, :]).sum(axis=2).argmin(axis=1)
            obj.data.polygons.foreach_set('material_index', ids.astype(np.int32))
        else:
            obj.data.materials.append(material(obj.name, color))
        meshes.append(obj)
        objects.append(obj)
    face = bpy.data.objects.new(prefix + ':face', None)
    collection.objects.link(face)
    face.parent, face.parent_type, face.parent_bone = arm, 'BONE', bone_lookup['Head'].name
    # Blender bone parenting is at the tail; the bake is relative to the head.
    face.matrix_parent_inverse = Matrix.Translation((0, -bone_lookup['Head'].bone.length, 0))
    parts = {}
    for name, color in asset['faceColors'].items():
        obj = mesh_object(prefix + ':' + name, asset['faceGeometry'], collection)
        obj.parent = face
        obj.data.materials.append(material(obj.name, color))
        parts[name] = obj
        objects.append(obj)
    objects.append(face)
    return dict(root=root, armature=arm, bones=bone_lookup, corrections=corrections,
                face=face, parts=parts, objects=objects, meshes=meshes)


def importera(bake_path, scen_path):
    bake_path, scen_path = Path(bake_path), Path(scen_path)
    bake = json.loads(bake_path.read_text(encoding='utf-8'))
    spec = json.loads(scen_path.read_text(encoding='utf-8'))
    assets = json.loads((bake_path.parent / bake['assets']).read_text(encoding='utf-8'))
    if bake['schema'] != 'scen3d-bake/1' or len(bake['frames']) != bake['N']:
        raise ValueError('Invalid or incomplete bake')
    looks = {a['id']: a['look'] for a in spec['actors']}
    looks['guest'] = {**looks.get('B', {}), 'shirt': '#b5a99c'}
    collection = bpy.data.collections.new('bakade_aktorer')
    bpy.context.scene.collection.children.link(collection)
    actors = {aid: create_actor(aid, asset, looks[aid], collection) for aid, asset in assets['actors'].items()}
    last = {aid: next(f['actors'][aid] for f in bake['frames'] if f['actors'][aid]['visible']) for aid in actors}
    for f in bake['frames']:
        i = f['i']
        for aid, actor in actors.items():
            visible = f['actors'][aid]['visible']
            if visible:
                last[aid] = f['actors'][aid]
            value = last[aid]
            root_gl = mat(value['root']['matrix'])
            actor['root'].matrix_basis = CONV @ root_gl @ CONV.inverted()
            key_transform(actor['root'], i)
            root_inverse = root_gl.inverted()
            targets = {name: CONV @ root_inverse @ mat(data['world']) @ actor['corrections'][name]
                       for name, data in value['bones'].items()}
            # convert_local_to_pose avoids reliance on dependency-graph update order.
            for name, bone in actor['bones'].items():
                parent_name = assets['actors'][aid]['bones'][name]['parent']
                parent_args = dict(parent_matrix=targets[parent_name], parent_matrix_local=bone.parent.bone.matrix_local) if parent_name else {}
                bone.matrix_basis = bone.bone.convert_local_to_pose(targets[name], bone.bone.matrix_local, invert=True, **parent_args)
                key_transform(bone, i)
            actor['face'].matrix_basis = actor['corrections']['Head'].inverted() @ trs(value['face'])
            key_transform(actor['face'], i)
            for name, obj in actor['parts'].items():
                obj.matrix_basis = trs(value['face']['parts'][name])
                key_transform(obj, i)
            actor['root']['mouthOpen'] = value['mouthOpen']
            actor['root'].keyframe_insert('["mouthOpen"]', frame=i)
            for obj in actor['objects']:
                show = visible and value['face'].get('visible', True) if obj == actor['face'] or obj in actor['parts'].values() else visible
                if obj in actor['parts'].values():
                    name = next(n for n, o in actor['parts'].items() if o == obj)
                    show = show and value['face']['parts'][name]['visible']
                key_visibility(obj, show, i)
        if i % 60 == 0 or i == bake['N'] - 1:
            print(f'Keyed {i + 1}/{bake["N"]}', flush=True)
    for actor in actors.values():
        for obj in actor['objects']:
            constant_keys(obj)
    scene = bpy.context.scene
    scene.render.fps = bake['fps']
    scene.frame_start, scene.frame_end = 0, bake['N'] - 1
    scene.frame_set(0)
    print(f'Imported {len(actors)} actors, {bake["N"]} frames; no set, props or cameras created', flush=True)
    return actors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bake', default=str(HERE / 'bake.json'))
    parser.add_argument('--scen', default=str(ROOT / 'scen3d.json'))
    parser.add_argument('--output', default=str(HERE / 'bake.blend'))
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    importera(args.bake, args.scen)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output).resolve()))
