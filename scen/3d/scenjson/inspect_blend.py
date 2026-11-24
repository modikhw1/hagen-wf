"""Skriv endast Blender-scenens läsbara nyckeltal till stdout."""
import bpy
from mathutils import Vector

for frame in (36, 42):
    bpy.context.scene.frame_set(frame)
    print("FRAME", frame)
    for obj in bpy.context.scene.objects:
        if obj.type not in {"ARMATURE", "MESH", "CAMERA"}:
            continue
        if obj.type == "MESH":
            corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
            lo = [min(p[i] for p in corners) for i in range(3)]
            hi = [max(p[i] for p in corners) for i in range(3)]
            print(obj.name, obj.type, "bbox", [round(x, 4) for x in lo], [round(x, 4) for x in hi])
        else:
            print(obj.name, obj.type, "loc", [round(x, 4) for x in obj.matrix_world.translation])
            if obj.type == "CAMERA":
                forward = -(obj.matrix_world.to_3x3().col[2])
                up = obj.matrix_world.to_3x3().col[1]
                print(" CAMERA_FORWARD", [round(x, 6) for x in forward], "UP", [round(x, 6) for x in up])
            if obj.type == "ARMATURE" and obj.name == "person:1":
                print(" BONES_FIRST", [b.name for b in list(obj.pose.bones)[:30]])
                wanted = ("root", "upleg", "pelvis", "hip", "head", "eye", "ankle", "ball", "foot", "neck")
                for bone in obj.pose.bones:
                    if any(word in bone.name.lower() for word in wanted):
                        p = obj.matrix_world @ bone.head
                        print(" BONE", bone.name, [round(x, 4) for x in p])
