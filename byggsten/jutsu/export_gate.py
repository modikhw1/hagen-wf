"""Blender-side delivery gate. Embed this file in Jutsu operations; no local imports."""
import bpy
import math
from mathutils import Vector


def object_curves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    action = ad.action
    if hasattr(action, 'fcurves'):
        for curve in action.fcurves:
            yield action.fcurves, curve
    else:
        slot = getattr(getattr(ad, 'action_slot', None), 'handle', None)
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    if slot is None or bag.slot_handle == slot:
                        for curve in bag.fcurves:
                            yield bag.fcurves, curve


def merge_scene_animation(scene):
    """One multi-slot Action preserves simultaneous motion with default GLB export."""
    owners=[]
    for obj in scene.objects:
        for owner in (obj, obj.data):
            if owner is not None and getattr(owner,'animation_data',None) and owner.animation_data.action and owner not in owners:
                owners.append(owner)
    # Retain original datablocks until save; revision history and .blend1 preserve the source.
    merged=bpy.data.actions.new('PIPE_scene_timeline')
    layer=merged.layers.new('Scene timeline')
    strip=layer.strips.new(type='KEYFRAME')
    assignments=[]
    for owner in owners:
        slot=merged.slots.new(id_type=owner.id_type,name=owner.name)
        bag=strip.channelbags.new(slot)
        for _,source in list(object_curves(owner)):
            if source.modifiers:
                raise RuntimeError('EXPORT BLOCKED: unsupported curve modifier on '+owner.name)
            curve=bag.fcurves.new(source.data_path,index=source.array_index)
            curve.extrapolation=source.extrapolation
            curve.keyframe_points.add(len(source.keyframe_points))
            for a,b in zip(source.keyframe_points,curve.keyframe_points):
                b.co=a.co; b.interpolation=a.interpolation; b.easing=a.easing
                b.handle_left_type=a.handle_left_type; b.handle_right_type=a.handle_right_type
                b.handle_left=a.handle_left; b.handle_right=a.handle_right
            curve.update()
        assignments.append((owner,slot))
    for owner,slot in assignments:
        owner.animation_data.action=merged
        owner.animation_data.action_slot=slot
    return len(assignments)


def prepare_export_scene():
    scene = bpy.context.scene
    saved_frame = scene.frame_current
    candidates = [o for o in scene.objects if o.type == 'MESH']
    forbidden = [o.name for o in candidates if '_beat_' in o.name or any(c.hide_render or c.hide_viewport for c in o.users_collection)]
    if forbidden:
        raise RuntimeError('EXPORT BLOCKED: hidden/alternative meshes remain: '+', '.join(forbidden[:8]))
    prepared = []
    previous = bpy.context.preferences.edit.keyframe_new_interpolation_type
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'
        for obj in candidates:
            curves = list(object_curves(obj))
            hide = next((c for _,c in curves if c.data_path == 'hide_render'), None)
            if hide is None:
                if obj.hide_render or obj.hide_viewport:
                    raise RuntimeError('EXPORT BLOCKED: static hidden mesh '+obj.name)
                continue
            scale_curves = [c for _,c in curves if c.data_path == 'scale']
            if scale_curves and 'pipe_base_scale' not in obj:
                raise RuntimeError('EXPORT BLOCKED: authored scale needs explicit visibility carrier: '+obj.name)
            base = list(obj.get('pipe_base_scale', obj.scale))
            obj['pipe_base_scale'] = base
            # Disabling viewport evaluation leaves constraint-driven geometry at identity.
            for owner,curve in curves:
                if curve.data_path == 'hide_viewport':
                    owner.remove(curve)
            obj.hide_viewport = False
            frames = sorted({scene.frame_start, scene.frame_end} | {int(k.co.x) for k in hide.keyframe_points})
            states = [hide.evaluate(frame) >= .5 for frame in frames]
            for frame in frames:
                hidden = hide.evaluate(frame) >= .5
                obj.scale = (0,0,0) if hidden else base
                obj.keyframe_insert('scale',frame=frame)
            # Preferences do not reliably override existing/action-created key interpolation.
            for _,curve in object_curves(obj):
                if curve.data_path == 'scale':
                    for key in curve.keyframe_points:
                        key.interpolation = 'CONSTANT'
            obj['pipe_visibility'] = 'scale-zero-constant-v1'
            obj['pipe_visibility_animated'] = len(set(states)) > 1
            prepared.append(obj.name)
        # Verify the switch itself, not merely the existence of a scale channel.
        probes={scene.frame_start,scene.frame_end,saved_frame}
        for name in prepared:
            for _,curve in object_curves(bpy.data.objects[name]):
                if curve.data_path=='hide_render':
                    for key in curve.keyframe_points:
                        probes.update(int(key.co.x)+offset for offset in (-1,0,1) if scene.frame_start<=int(key.co.x)+offset<=scene.frame_end)
        for frame in sorted(probes):
            scene.frame_set(frame)
            for name in prepared:
                obj=bpy.data.objects[name]
                expected=(0,0,0) if obj.hide_render else obj['pipe_base_scale']
                if max(abs(a-b) for a,b in zip(obj.scale,expected))>1e-6:
                    raise RuntimeError(f'EXPORT BLOCKED: visibility fade {name} frame {frame}')
        scene.frame_set(saved_frame)
        bpy.context.view_layer.update()
        failures=[]
        for obj in candidates:
            points=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
            if not all(math.isfinite(x) for point in points for x in point):
                failures.append(obj.name+': nonfinite bounds')
            dimensions=[max(p[k] for p in points)-min(p[k] for p in points) for k in range(3)]
            if obj.name.startswith('RIG_') and obj.name.endswith('_huvud') and max(dimensions)>.4:
                failures.append(obj.name+': oversized head '+str(dimensions))
        if failures:
            raise RuntimeError('EXPORT BLOCKED: '+'; '.join(failures[:8]))
        slots=merge_scene_animation(scene)
        scene.frame_set(saved_frame); bpy.context.view_layer.update()
        scene['pipe_export_gate']='v2: no hidden alternatives, portable step visibility, bounded heads, shared timeline; GLB audit still required'
        return {'mesh_count':len(candidates),'portable_visibility_objects':len(prepared),'hidden_alternatives':0,'timeline_slots':slots,'glb_audit_required':True}
    finally:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = previous


result = prepare_export_scene()
