"""Installs each addon, runs its operators on a real scene, unloads it.

Checking that something registers isn't worth much on its own, so every tool
gets actually used here.

    blender --background --factory-startup --python test_all.py
"""
import glob
import math
import os
import sys

import bmesh
import bpy
import mathutils
from bpy_extras.object_utils import world_to_camera_view

# Derived from this file, never hardcoded. An absolute path to one developer's
# home directory pointed at a directory the sandbox user cannot even read, and
# the suite then discovered zero addons and reported "RESULT 0/0 tools passed"
# with exit 0 -- a pass, on every Blender version, testing nothing at all.
# F-016.
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
    bpy.ops.object.select_all(action='DESELECT')
    a.select_set(True)
    b.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_batch_rename(pattern="Crate_###", start=5)
    # Sorted by name, so Cube then Sphere, and zero-padded to the number of
    # hashes. "any object starts with Crate_" passed on a one-object rename and
    # on numbering that repeated itself.
    assert sorted(o.name for o in (a, b)) == ["Crate_005", "Crate_006"], \
        sorted(o.name for o in (a, b))
    assert sorted(o.data.name for o in (a, b)) == ["Crate_005", "Crate_006"], \
        "mesh data names went out of sync with the objects"
    bpy.ops.object.bt_find_replace(find="Crate", replace="Box")
    assert sorted(o.name for o in (a, b)) == ["Box_005", "Box_006"], \
        sorted(o.name for o in (a, b))

@ex("bt_origin_tools")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT')
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_set_origin(mode='BOTTOM')
    # Where the origin landed, not merely that the operator returned. The
    # description promises the base of the bounds, and a buyer who trusts that
    # in an engine finds out when the asset sinks or floats.
    low = min((a.matrix_world @ v.co).z for v in a.data.vertices)
    assert abs(a.location.z - low) < 1e-4, \
        f"BOTTOM origin at z {a.location.z}, lowest vertex at {low}"
    assert abs(low - 0.5) < 1e-4, f"the mesh moved: lowest vertex now {low}"
    bpy.ops.object.bt_set_origin(mode='WORLD')
    assert a.location.length < 1e-4, f"WORLD origin at {a.location[:]}"
    low_after = min((a.matrix_world @ v.co).z for v in a.data.vertices)
    assert abs(low_after - low) < 1e-4, \
        f"WORLD moved the geometry: {low} to {low_after}"
    bpy.ops.object.bt_set_origin(mode='BOTTOM')
    bpy.ops.object.bt_drop_to_floor()

@ex("bt_mesh_stats")
def _(a, b, g):
    bpy.context.view_layer.objects.active = a
    import bt_mesh_stats
    s = bt_mesh_stats._stats(a)
    assert s["tris"] > 0 and s["verts"] > 0
    # `a` is a cube: 6 quads, 12 triangles, no n-gons, nothing loose. A readout
    # is only worth anything if the numbers are right, and "> 0" cannot tell a
    # correct count from any other count.
    assert s["tris"] == 12, f"cube reported {s['tris']} triangles"
    assert s["ngons"] == 0, f"cube reported {s['ngons']} n-gons"
    assert s["loose"] == 0, f"cube reported {s['loose']} loose verts"
    bm = bmesh.new()
    bm.from_mesh(a.data)
    bm.verts.new(mathutils.Vector((9.0, 9.0, 9.0)))
    bm.to_mesh(a.data)
    bm.free()
    a.data.update()
    assert bt_mesh_stats._stats(a)["loose"] == 1, "a loose vertex went uncounted"
    # The operator, not just the helper. Until 2026-09-06 this add-on was the
    # one of the twelve whose operator the suite never called: a planted
    # `raise` at the top of `execute()` still reported OK and 12/12, because
    # `_stats` is a module function and `object.bt_select_ngons` was reached by
    # nothing. 17 of 18 operators were covered and the README said "runs its
    # operators", so this closes the gap the claim already assumed.
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, location=(0, 6, 0))
    cyl = bpy.context.active_object
    try:
        # An 8-sided cylinder is 8 quads down the side and two 8-gon caps, so
        # the count the operator has to find is exactly 2 and "some" would not
        # tell a working selection from a select-all.
        assert sum(1 for f in cyl.data.polygons if len(f.vertices) > 4) == 2, (
            "the fixture is wrong, not the operator")
        bpy.ops.object.bt_select_ngons()
        assert cyl.mode == 'EDIT', "the operator left the object out of edit mode"
        bpy.ops.object.mode_set(mode='OBJECT')
        picked = [f for f in cyl.data.polygons if f.select]
        assert len(picked) == 2, f"selected {len(picked)} faces, expected the 2 caps"
        assert all(len(f.vertices) > 4 for f in picked), "a quad got selected"
    finally:
        if cyl.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(cyl, do_unlink=True)
        bpy.context.view_layer.objects.active = a

@ex("bt_auto_frame")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT')
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    for fill in (0.5, 0.8):
        bpy.ops.object.bt_auto_frame(fill=fill)
        bpy.context.view_layer.update()
        scene, cam = bpy.context.scene, bpy.context.scene.camera
        xs, ys = [], []
        for v in a.data.vertices:
            ndc = world_to_camera_view(scene, cam, a.matrix_world @ v.co)
            xs.append(ndc.x)
            ys.append(ndc.y)
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        # The claim is a fraction of frame, so measure the fraction of frame.
        # Projecting the verts is the same arithmetic the operator solves
        # against, which makes this a check that it converged rather than an
        # independent derivation, and that is the failure worth catching: a
        # solver that stops early or picks the wrong bracket.
        assert abs(span - fill) < 0.02, \
            f"asked for {fill} of frame, measured {span:.3f}"

@ex("bt_turntable")
def _(a, b, g):
    scene = bpy.context.scene
    cam = scene.camera
    bpy.ops.object.select_all(action='DESELECT')
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_turntable(frames=48)
    pivot = bpy.data.objects.get("BT_Turntable_Pivot")
    assert pivot is not None, "no pivot"
    assert cam.parent is pivot, f"camera parented to {cam.parent}"
    # One full turn over the range, sampled off the animated value rather than
    # off the Action, which has no fcurves on 5.x at all. Frame 1 and frame 48
    # are the same pose, which is why the scene range stops at 47.
    assert scene.frame_end == 47, f"frame_end {scene.frame_end}"
    seen = {}
    for frame in (1, 24, 48):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        seen[frame] = (pivot.rotation_euler.z, cam.matrix_world.translation.copy())
    assert abs(seen[1][0]) < 1e-4, f"frame 1 at {seen[1][0]}"
    assert abs(seen[48][0] + math.tau) < 1e-4, f"frame 48 at {seen[48][0]}"
    # Linear, checked across the range rather than at the ends. This is what
    # caught F-121: the tool set a user preference and trusted it, the
    # preference never reached keyframe_insert, and every turntable it ever
    # made eased in and out. Frame 2 of 48 was at 0.0084 rad against a linear
    # 0.1337, and both ends still matched perfectly.
    for frame in (2, 12, 24, 36, 47):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        want = -math.tau * (frame - 1) / 47
        assert abs(pivot.rotation_euler.z - want) < 1e-3, \
            f"frame {frame} at {pivot.rotation_euler.z:.4f}, linear is {want:.4f}"
    assert (seen[1][1] - seen[48][1]).length < 1e-4, "the loop does not close"
    assert (seen[1][1] - seen[24][1]).length > 1.0, "the camera never moved"
    scene.frame_set(1)
    bpy.ops.object.bt_turntable_clear()
    assert cam.parent is None, "clear left the camera parented"

@ex("bt_quick_export")
def _(a, b, g):
    import tempfile
    d = tempfile.mkdtemp()
    bpy.ops.object.select_all(action='DESELECT')
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.export_scene.bt_quick_export(directory=d, fmt='GLTF', target='UNITY')
    written = glob.glob(os.path.join(d, "*.glb"))
    assert written, "no glb written"
    # What came out, not that something came out. Re-importing is the only
    # check that reads the file rather than the operator's return value.
    before = len(a.data.loop_triangles) or sum(
        len(p.vertices) - 2 for p in a.data.polygons)
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=written[0])
    fresh_objs = [o for o in bpy.data.objects
                  if o not in existing and o.type == 'MESH']
    assert fresh_objs, f"{written[0]} re-imported as nothing"
    fresh_objs[0].data.calc_loop_triangles()
    after = len(fresh_objs[0].data.loop_triangles)
    assert after == before, f"exported {before} triangles, read back {after}"
    for o in fresh_objs:
        bpy.data.objects.remove(o)

@ex("bt_asset_check")
def _(a, b, g):
    import bt_asset_check
    # Plant the two things it says it catches, then require it to say so. The
    # cube starts at z=1.5, so it is already floating; this adds scale.
    a.scale = (2.0, 1.0, 1.0)
    bpy.ops.object.select_all(action='DESELECT')
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_asset_check()
    said = [text for text, _ in bt_asset_check._RESULTS[a.name]]
    assert any("Scale not applied" in t for t in said), said
    assert any("Floating" in t for t in said), said
    # A loose vertex well below the body, which is the case the fix used to get
    # wrong and no test here ever planted. `bt_asset_fix` deletes loose verts
    # and then drops the object to the floor in the same operator call, so a
    # cached `bound_box` still holds the vertex it just removed and the drop
    # overshoots by exactly that depth. Measured before the fix: the object
    # came to rest **9.752052m in the air** on all seven versions.
    n = len(a.data.vertices)
    a.data.vertices.add(1)
    a.data.vertices[-1].co = mathutils.Vector((0.0, 0.0, -6.0))
    a.data.update()
    bpy.context.view_layer.update()
    bpy.ops.object.bt_asset_check()
    said = [text for text, _ in bt_asset_check._RESULTS[a.name]]
    assert any("loose vert" in t for t in said), said

    bpy.ops.object.bt_asset_fix()
    assert all(abs(s - 1.0) < 1e-4 for s in a.scale), f"scale still {a.scale[:]}"
    assert len(a.data.vertices) == n, f"loose vertex survived: {len(a.data.vertices)}"
    low = min((a.matrix_world @ v.co).z for v in a.data.vertices)
    assert abs(low) < 0.01, f"still floating at {low}"
    bpy.ops.object.bt_asset_check()
    said = [text for text, _ in bt_asset_check._RESULTS[a.name]]
    assert not any("Scale not applied" in t or "Floating" in t for t in said), said

@ex("bt_collection_sort")
def _(a, b, g):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.bt_collection_sort(mode='TYPE')
    for obj, want in ((a, "Meshes"), (g, "Meshes"),
                      (bpy.context.scene.camera, "Cameras")):
        names = [c.name for c in obj.users_collection]
        assert names == [want], f"{obj.name} ended up in {names}"

@ex("bt_seam_by_angle")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT')
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.mesh.bt_seam_by_angle(angle=math.radians(40))
    assert a.data.uv_layers, "unwrap produced no UVs"
    # Every edge of a cube is 90 degrees, so a 40 degree threshold marks all
    # twelve and a 120 degree threshold marks none. Counting the seams is what
    # separates "the operator ran" from "the operator used the angle".
    seams = sum(1 for e in a.data.edges if e.use_seam)
    assert seams == 12, f"40 degrees on a cube marked {seams} of 12 edges"
    area = 0.0
    uv = a.data.uv_layers.active.data
    for poly in a.data.polygons:
        pts = [uv[i].uv for i in poly.loop_indices]
        area += abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y
                        - pts[(i + 1) % len(pts)].x * pts[i].y
                        for i in range(len(pts)))) / 2
    assert area > 0.05, f"UV area {area:.4f} is degenerate"
    bpy.ops.mesh.bt_seam_by_angle(angle=math.radians(120), unwrap=False)
    seams = sum(1 for e in a.data.edges if e.use_seam)
    assert seams == 0, f"120 degrees on a cube marked {seams} edges"

@ex("bt_material_slots")
def _(a, b, g):
    m1 = bpy.data.materials.new("Metal")
    m2 = bpy.data.materials.new("Metal.001")
    a.data.materials.append(m1)
    a.data.materials.append(m2)
    bpy.ops.object.select_all(action='DESELECT')
    a.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_merge_duplicates()
    assert [ms.material.name for ms in a.material_slots] == ["Metal", "Metal"], \
        [ms.material.name for ms in a.material_slots]
    bpy.ops.object.bt_clean_slots()
    # Every face is on slot 0, so slot 1 is unused and goes. The claim is
    # "removes unused slots", and removing a used one is the failure that would
    # cost somebody their shading.
    assert len(a.data.materials) == 1, f"{len(a.data.materials)} slots left"
    assert a.data.materials[0].name == "Metal", a.data.materials[0].name
    # And the other direction: two slots with faces on both survive.
    used = bpy.data.materials.new("Trim")
    a.data.materials.append(used)
    for i, poly in enumerate(a.data.polygons):
        poly.material_index = i % 2
    bpy.ops.object.bt_clean_slots()
    assert len(a.data.materials) == 2, \
        f"a slot with faces on it was removed, {len(a.data.materials)} left"

@ex("bt_surface_scatter")
def _(a, b, g):
    bpy.ops.object.select_all(action='DESELECT')
    b.select_set(True)
    g.select_set(True)
    bpy.context.view_layer.objects.active = g
    bpy.ops.object.bt_surface_scatter(count=200, seed=1)
    coll = bpy.data.collections.get("BT_Scatter")
    assert coll, "no scatter collection"
    # The ground is one 12m quad, so "did it place anything" cannot see the
    # bug this catches: the old code sampled the triangle made from the face's
    # first three loop verts and put 800 of 800 instances in half the quad,
    # with the diagonal visible. Quadrant counts fail on that and pass on a
    # whole-face scatter. Loose enough to survive a different RNG, tight
    # enough that an empty half is impossible: a half-quad scatter puts 0 in
    # two of these four cells.
    quads = [0, 0, 0, 0]
    for o in coll.objects:
        quads[(o.location.x >= 0) * 2 + (o.location.y >= 0)] += 1
    assert min(quads) >= len(coll.objects) // 10, \
        f"scatter is not covering the face: quadrant counts {quads}"
    # And named after the object it is an instance of, not after sources[0].
    for o in coll.objects:
        assert o.name.startswith(o.data.name.split(".")[0]), \
            f"{o.name} carries mesh {o.data.name}"

@ex("bt_align_distribute")
def _(a, b, g):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(6, 0, 0))
    c = bpy.context.object
    bpy.ops.object.select_all(action='DESELECT')
    for o in (a, b, c):
        o.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.bt_align(axis='Y', mode='CENTRE')
    ys = []
    for o in (a, b, c):
        lo = min((o.matrix_world @ v.co).y for v in o.data.vertices)
        hi = max((o.matrix_world @ v.co).y for v in o.data.vertices)
        ys.append((lo + hi) / 2)
    assert max(ys) - min(ys) < 1e-4, f"aligned centres still spread: {ys}"
    bpy.ops.object.bt_distribute(axis='X')
    xs = sorted((min((o.matrix_world @ v.co).x for v in o.data.vertices)
                 + max((o.matrix_world @ v.co).x for v in o.data.vertices)) / 2
                for o in (a, b, c))
    gaps = [round(xs[i + 1] - xs[i], 4) for i in range(len(xs) - 1)]
    assert max(gaps) - min(gaps) < 1e-3, f"uneven gaps after distribute: {gaps}"
    assert min(gaps) > 0.1, f"everything collapsed to one point: {gaps}"

sys.path.insert(0, ADDON_DIR)
modules = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ADDON_DIR, "*.py")))
failures = []

# An empty run is a failure, not a pass. Finding no addons meant this printed
# "RESULT 0/0 tools passed" and exited 0, so compat.py reported 5/5 across
# every Blender version while the suite exercised nothing. A suite that cannot
# tell "everything works" from "I tested nothing" is not a suite. F-016.
if not modules:
    print("RESULT 0/0 tools passed")
    print(f"FAIL no addons found in {ADDON_DIR} -- nothing was tested")
    raise SystemExit(1)

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
