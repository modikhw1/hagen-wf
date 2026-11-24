"""Headless Blender 5.2 3D-rendering av Gamla Paradigmet (Argon/Opus) vs Blind Agent C (Rule-Pipe v7)
för både guacamole (tvånivåsbar + öppna Zon 3-horisonter) och gelato (glasmonter + kamera ovanför vs P2 inuti disken).

Körs av djup_blind_eval.py via:
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python motpart\runda-2-neon\djup_blender_scen_render.py
"""
import math
import pathlib
import bpy
from mathutils import Vector

OUT = pathlib.Path(__file__).resolve().parent / "djup_blind_renders"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 960
    scene.render.resolution_y = 640
    scene.render.image_settings.file_format = "PNG"
    # Mörk bakgrund i värld
    world = bpy.data.worlds.new("W")
    scene.world = world
    world.color = (0.08, 0.10, 0.14)


def make_mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    return m


def add_box(name, center, size, rgba):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(make_mat(f"mat_{name}", rgba))
    return o


def add_person(name, xy, z_base, height, seated=False, rgba=(0.25, 0.65, 0.95, 1.0)):
    # Enkel tydlig 3D-siluett (ben/kropp + huvud) för skalreferens
    x, y = xy
    if seated:
        # Sittande bål från seat_z till huvud
        torso_h = height * 0.45
        add_box(f"{name}_torso", (x, y, z_base + torso_h / 2), (0.42, 0.28, torso_h), rgba)
        add_box(f"{name}_head", (x, y, z_base + torso_h + 0.14), (0.20, 0.22, 0.24), (0.92, 0.78, 0.66, 1.0))
        add_box(f"{name}_legs", (x, y + 0.16, z_base / 2), (0.36, 0.20, z_base), (0.18, 0.22, 0.30, 1.0))
    else:
        leg_h = height * 0.48
        torso_h = height * 0.37
        add_box(f"{name}_legs", (x, y, leg_h / 2), (0.34, 0.24, leg_h), (0.18, 0.22, 0.30, 1.0))
        add_box(f"{name}_torso", (x, y, leg_h + torso_h / 2), (0.44, 0.26, torso_h), rgba)
        add_box(f"{name}_head", (x, y, leg_h + torso_h + 0.13), (0.20, 0.22, 0.24), (0.92, 0.78, 0.66, 1.0))


def add_cam_marker(name, pos, rgba=(1.0, 0.25, 0.25, 1.0)):
    add_box(name, pos, (0.22, 0.30, 0.18), rgba)


def look_at(cam_obj, target):
    direction = Vector(target) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_iso_cam(pos, target, lens=32.0):
    cam_data = bpy.data.cameras.new("IsoCam")
    cam_data.lens = lens
    cam_obj = bpy.data.objects.new("IsoCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    cam_obj.location = Vector(pos)
    look_at(cam_obj, target)


def render_to(fname):
    bpy.context.scene.render.filepath = str(OUT / fname)
    bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------
# 1. GUACAMOLE — GAMLA PARADIGMET (Argon / Opus: platt 0.78 m skiva + sluten 4-väggslåda!)
# ------------------------------------------------------------------
def build_guac_old():
    clear_scene()
    # Golv
    add_box("golv", (0, 0, -0.02), (4.6, 3.8, 0.04), (0.22, 0.20, 0.18, 1.0))
    # Slutna 4-väggar (fejkade slutna väggar på alla 4 sidor — två genomskinliga framsidor för insyn)
    add_box("vagg_bak", (0, 1.85, 1.35), (4.6, 0.08, 2.7), (0.55, 0.28, 0.28, 1.0))
    add_box("vagg_vanster", (-2.26, 0, 1.35), (0.08, 3.8, 2.7), (0.55, 0.28, 0.28, 1.0))
    add_box("vagg_hoger_fejk", (2.26, 0, 0.75), (0.08, 3.8, 1.5), (0.75, 0.20, 0.20, 1.0))
    add_box("vagg_fram_fejk", (0, -1.85, 0.55), (4.6, 0.08, 1.1), (0.75, 0.20, 0.20, 1.0))
    # Argons/Opus platta 0.77-0.78 m disk (saknar helt tvånivåssteget!)
    add_box("platt_disk_078", (0, 0.1, 0.71), (1.45, 0.44, 0.14), (0.75, 0.52, 0.30, 1.0))
    # Låg vanlig stol 0.45 m + A och B
    add_box("stol_A", (-0.1, -0.55, 0.225), (0.45, 0.45, 0.45), (0.35, 0.35, 0.38, 1.0))
    add_person("A", (-0.1, -0.55), 0.45, 1.78, seated=True, rgba=(0.25, 0.55, 0.90, 1.0))
    add_person("B", (0.2, 0.80), 0.0, 1.80, seated=False, rgba=(0.20, 0.65, 0.35, 1.0))
    setup_iso_cam((4.6, -4.3, 3.3), (0.0, 0.0, 0.85), lens=34)
    render_to("render_guac_old.png")


# ------------------------------------------------------------------
# 2. GUACAMOLE — BLIND AGENT C (Rule-Pipe v7: 0.89 m + 1.14 m tvånivåsbar + barstol 0.78 m + ÖPPEN Z3!)
# ------------------------------------------------------------------
def build_guac_v7():
    clear_scene()
    # Öppet golvplan (Zon 3 öppen horisont på höger & bakom kamera -> INGA fejkväggar!)
    add_box("golv", (0, 0, -0.02), (4.2, 4.2, 0.04), (0.24, 0.22, 0.20, 1.0))
    # Enbart Z1 observerade väggar (wall_ahead träpanel + wall_left mexikansk vägg!)
    add_box("wall_ahead_Z1", (0, 1.95, 1.275), (4.0, 0.08, 2.55), (0.64, 0.66, 0.42, 1.0))
    add_box("wall_left_Z1", (-1.95, 0, 1.275), (0.08, 4.0, 2.55), (0.90, 0.55, 0.14, 1.0))
    # Tvånivås-bardisk ur Blind C (v7):
    # Tier 1: Nedre vit arbetsbänk 0.89 m (0.55 x 2.45 m)
    add_box("worktop_089", (0.25, 0.15, 0.445), (0.55, 2.45, 0.89), (0.88, 0.90, 0.92, 1.0))
    # Tier 2: Övre kopparbardisk 1.14 m (0.40 x 2.50 m) — tydligt +25 cm steg!
    add_box("copper_bar_114", (-0.22, 0.15, 0.57), (0.40, 2.50, 1.14), (0.78, 0.44, 0.22, 1.0))
    # Tier 3: Bakbarskyl 1.35 m mot wall_ahead
    add_box("cooler_135", (0.35, 1.62, 0.675), (0.90, 0.55, 1.35), (0.48, 0.54, 0.60, 1.0))
    # Hög barstol 0.78 m + gäst A (diagonalt längre bort) + stående bartender B (1.57 m diagonal!)
    add_box("barstool_078", (-0.78, 0.55, 0.39), (0.38, 0.38, 0.78), (0.30, 0.24, 0.18, 1.0))
    add_person("A", (-0.78, 0.55), 0.78, 1.78, seated=True, rgba=(0.25, 0.55, 0.90, 1.0))
    add_person("B", (0.62, -0.15), 0.0, 1.80, seated=False, rgba=(0.18, 0.68, 0.35, 1.0))
    # Kamera S4 vid 1.34 m höjd
    add_cam_marker("cam_S4_134", (0.05, -1.45, 1.34), (0.20, 0.90, 0.45, 1.0))
    setup_iso_cam((4.6, -4.3, 3.3), (0.0, 0.0, 0.85), lens=34)
    render_to("render_guac_v7.png")


# ------------------------------------------------------------------
# 3. GELATO — GAMLA PARADIGMET (Argon 0.72 m platt skiva + Opus P2-kamera 0.711 m INUTI disken!)
# ------------------------------------------------------------------
def build_gelato_old():
    clear_scene()
    add_box("golv", (0, 0, -0.02), (4.0, 4.0, 0.04), (0.22, 0.20, 0.18, 1.0))
    add_box("vagg_bak", (0, 1.8, 1.4), (4.0, 0.08, 2.8), (0.55, 0.28, 0.28, 1.0))
    add_box("vagg_sid_fejk", (-1.95, 0, 1.4), (0.08, 4.0, 2.8), (0.75, 0.20, 0.20, 1.0))
    # Platt 0.72 m bordsskiva
    add_box("disk_072", (0, 0.0, 0.65), (1.45, 0.44, 0.14), (0.68, 0.66, 0.58, 1.0))
    add_person("A", (0.0, 0.85), 0.0, 1.68, seated=False, rgba=(0.25, 0.55, 0.90, 1.0))
    # Opus P2-kamera vid 0.711 m (röd klump — rakt i diskhöjd / under kantinerna!)
    add_cam_marker("cam_P2_0711", (0.0, -0.75, 0.711), (0.95, 0.18, 0.18, 1.0))
    setup_iso_cam((3.6, -3.4, 2.5), (0.0, 0.15, 0.85), lens=35)
    render_to("render_gelato_old.png")


# ------------------------------------------------------------------
# 4. GELATO — BLIND AGENT C (Rule-Pipe v7: 0.88 m kantindäck + 1.22 m glasmonter + kamera 1.42 m + ÖPPEN Z3!)
# ------------------------------------------------------------------
def build_gelato_v7():
    clear_scene()
    add_box("golv", (0, 0, -0.02), (3.6, 3.8, 0.04), (0.24, 0.22, 0.20, 1.0))
    # Endast Z1 observerad bakvägg (left/right/behind = Z3 öppen horisont!)
    add_box("wall_ahead_Z1", (0, 1.75, 1.35), (3.2, 0.08, 2.7), (0.74, 0.66, 0.54, 1.0))
    # Tier 1: Glassdiskens bas & kantindäck 0.88 m (1.40 x 0.90 m)
    add_box("pan_deck_088", (0, -0.05, 0.44), (1.40, 0.90, 0.88), (0.72, 0.76, 0.80, 1.0))
    # Pastel-kantiner på 0.88 m-däcket
    for ix, col in enumerate([(0.95, 0.86, 0.65, 1), (0.75, 0.52, 0.48, 1), (0.78, 0.86, 0.68, 1)]):
        add_box(f"pan_{ix}", (-0.38 + ix * 0.38, -0.05, 0.89), (0.32, 0.68, 0.04), col)
    # Tier 2: Glasmonter / nyskydd 1.22 m (sidostolpar + topp-hylla 0.30 m djup!)
    add_box("sneeze_top_122", (0, -0.35, 1.20), (1.40, 0.30, 0.05), (0.90, 0.93, 0.95, 1.0))
    add_box("glass_post_L", (-0.68, -0.35, 1.04), (0.04, 0.04, 0.32), (0.75, 0.82, 0.88, 1.0))
    add_box("glass_post_R", (0.68, -0.35, 1.04), (0.04, 0.04, 0.32), (0.75, 0.82, 0.88, 1.0))
    # Tier 3: Bakre arbetsyta 0.90 m (utan den avvisade hallucinerade gasspisen!)
    add_box("back_prep_090", (0, 1.40, 0.45), (1.85, 0.60, 0.90), (0.62, 0.65, 0.68, 1.0))
    add_person("A", (0.0, 0.75), 0.0, 1.68, seated=False, rgba=(0.25, 0.55, 0.90, 1.0))
    # Kamera S1 korrekt vid 1.42 m höjd, lutad ned mot kantinerna!
    add_cam_marker("cam_S1_142", (0.0, -0.92, 1.42), (0.20, 0.90, 0.45, 1.0))
    setup_iso_cam((3.6, -3.4, 2.5), (0.0, 0.15, 0.85), lens=35)
    render_to("render_gelato_v7.png")


if __name__ == "__main__":
    build_guac_old()
    build_guac_v7()
    build_gelato_old()
    build_gelato_v7()
    print("BLENDER 5.2 RENDERS DONE!")
