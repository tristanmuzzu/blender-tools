"""Install, enable, exercise and disable every free tool.

Registration is the easy half. This also RUNS each operator against real
geometry, because an addon that registers but throws on first click is worse
than one that fails to install -- the user has already paid attention.
"""
import bpy, addon_utils, os, sys, glob, math, traceback

ADDON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "addons")

def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1.5))
    a = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(3, 0, 0.4))
    b = bpy.context.object
    bpy.ops.mesh.primitive_plane_add(size=12)
    ground = bpy.context.object
    bpy.ops.object.camera_add(location=(8, -8, 5), rotation=(1.1, 0, 0.8))
    bpy.context.scene.camera = bpy.context.object
    return a, b, ground

EXERCISE = {}

def ex(name):
    def deco(fn):
        EXERCISE[name] = fn
        return fn
    return deco

@ex("bt_batch_rename")
def _(a, b, g):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.bt_batch_rename(pattern="Crate_###", start=1)
    assert any(o.name.startswith("Crate_") for o in bpy.context.scene.objects)
    bpy.ops.object.bt_find_replace(find="Crate", replace="Box")

@ex("bt_origin_tools")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT'); a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_set_origin(mode='BOTTOM')
    bpy.ops.object.bt_drop_to_floor()

@ex("bt_mesh_stats")
def _(a, b, g):
    bpy.context.view_layer.objects.active = a
    import bt_mesh_stats
    s = bt_mesh_stats._stats(a)
    assert s["tris"] > 0 and s["verts"] > 0

@ex("bt_auto_frame")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT'); a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_auto_frame(fill=0.8)

@ex("bt_turntable")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT'); a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_turntable(frames=48)
    bpy.ops.object.bt_turntable_clear()

@ex("bt_quick_export")
def _(a, b, g):
    import tempfile
    d = tempfile.mkdtemp()
    bpy.ops.object.select_all(action='DESELECT'); a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.export_scene.bt_quick_export(directory=d, fmt='GLTF', target='UNITY')
    assert glob.glob(os.path.join(d, "*.glb")), "no glb written"

@ex("bt_asset_check")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT'); a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_asset_check()
    bpy.ops.object.bt_asset_fix()

@ex("bt_collection_sort")
def _(a, b, g):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.bt_collection_sort(mode='TYPE')

@ex("bt_seam_by_angle")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT'); a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.mesh.bt_seam_by_angle(angle=math.radians(40))
    assert a.data.uv_layers, "unwrap produced no UVs"

@ex("bt_material_slots")
def _(a, b, g):
    m1 = bpy.data.materials.new("Metal")
    m2 = bpy.data.materials.new("Metal.001")
    a.data.materials.append(m1); a.data.materials.append(m2)
    bpy.ops.object.select_all(action='DESELECT'); a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_merge_duplicates()
    bpy.ops.object.bt_clean_slots()

@ex("bt_surface_scatter")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT')
    b.select_set(True); g.select_set(True)
    bpy.context.view_layer.objects.active = g
    bpy.ops.object.bt_surface_scatter(count=40, seed=1)
    assert bpy.data.collections.get("BT_Scatter"), "no scatter collection"

@ex("bt_align_distribute")
def _(a, b, g):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(6, 0, 0))
    c = bpy.context.object
    bpy.ops.object.select_all(action='DESELECT')
    for o in (a, b, c): o.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_align(axis='Y', mode='CENTRE')
    bpy.ops.object.bt_distribute(axis='X')

sys.path.insert(0, ADDON_DIR)
modules = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ADDON_DIR, "*.py")))
failures = []

for mod in modules:
    try:
        src = os.path.join(ADDON_DIR, mod + ".py")
        bpy.ops.preferences.addon_install(filepath=src, overwrite=True)
        # Scene FIRST: read_factory_settings unregisters every enabled addon,
        # so enabling before building the scene silently undoes the enable.
        a, b, g = fresh_scene()
        bpy.ops.preferences.addon_enable(module=mod)
        fn = EXERCISE.get(mod)
        if fn is None:
            failures.append(f"{mod}: NO EXERCISE DEFINED")
        else:
            fn(a, b, g)
        bpy.ops.preferences.addon_disable(module=mod)
        print(f"  OK   {mod}")
    except Exception as exc:
        failures.append(f"{mod}: {type(exc).__name__}: {exc}")
        print(f"  FAIL {mod}: {type(exc).__name__}: {exc}")

print(f"RESULT {len(modules)-len(failures)}/{len(modules)} tools passed")
if failures:
    for f in failures:
        print("  !", f)
    raise SystemExit(1)
