bl_info = {
    "name": "BT Asset Check",
    "author": "Tristan Muzzu",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Pre-export checks: transforms, scale, manifold geometry, UVs",
    "category": "Object",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-asset_check"
)


def _bt_footer(layout):
    """Quiet footer, not a nag: one row, no pitch, below whatever the tool drew.

    Somebody who installed a free add-on is not in a buying mood, and a panel
    that shouts gets the whole repo dismissed.
    """
    layout.separator()
    row = layout.row()
    row.scale_y = 0.85
    row.operator("wm.url_open", text="PanelForge: sci-fi panel generator", icon='URL').url = PANELFORGE_URL

import bmesh
import bpy
from bpy.types import Operator, Panel
from mathutils import Vector

# panels redraw constantly, so cache instead of re-checking every frame
_RESULTS = {}


def _world_bounds(obj):
    """Min and max world-space corner, derived from vertices.

    Not from `obj.bound_box`, which is a cache that a mesh edit does not
    refresh until something calls `view_layer.update()`. `Fix Mechanical
    Issues` deletes loose vertices and then drops the object to the floor in
    the same operator call, so it used to read a box that still contained the
    vertices it had just removed and overshoot by exactly their depth. On a
    cone with one loose vertex 6m below it, the object landed **9.752052m in
    the air** instead of on Z=0, identically on 3.6.23, 4.2.23, 4.5.12,
    4.5.13, 5.0.1, 5.2.0 and 5.2.1.

    Returns None for a mesh with no vertices, which has no bounds worth
    reporting and would otherwise raise on min().
    """
    verts = obj.data.vertices
    if not verts:
        return None
    pts = [obj.matrix_world @ v.co for v in verts]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts),
                    min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts),
                    max(p.z for p in pts))))


def _parent_shear(obj):
    """The one defect on this list that Blender's own viewport will not show.

    A rotated child under a non-uniformly scaled parent is a shear, and the
    glTF and FBX formats have no way to write one: an exporter has to drop it,
    so the object lands somewhere else in the target engine while Blender keeps
    drawing it in the right place. Measured on 2026-08-27 as **410.842 mm** of
    displacement on a 1 m object, on 3.6.23, 4.5.13 and 5.2.1, and re-measured
    on all seven binaries on 2026-08-28. That is F-134, and
    `pipeline/probes/gltf_parent_inverse_shear.py` is the reproduction.

    Returns the parent's name when it fires and None when it does not, so the
    message can name the object the user has to go and fix rather than the one
    they had selected.

    Deliberately not checked here: whether the *child* is scaled. A uniformly
    scaled parent with any rotation is fine, and a non-uniformly scaled parent
    with an unrotated child is fine too. Both were confirmed as controls before
    this row was written, at 0.0001 mm and 0.0000 mm.
    """
    parent = obj.parent
    if parent is None:
        return None
    if all(abs(r) <= 1e-4 for r in obj.rotation_euler):
        return None
    sx, sy, sz = parent.matrix_world.to_scale()
    biggest, smallest = max(sx, sy, sz), min(sx, sy, sz)
    if smallest <= 1e-9:
        return None
    if biggest / smallest - 1.0 <= 1e-4:
        return None
    return parent.name


def _check(obj):
    issues = []

    if any(abs(s - 1.0) > 1e-4 for s in obj.scale):
        issues.append(("Scale not applied", 'ERROR'))
    if any(abs(r) > 1e-4 for r in obj.rotation_euler):
        issues.append(("Rotation not applied", 'INFO'))

    sheared = _parent_shear(obj)
    if sheared is not None:
        issues.append((f"Rotated under a non-uniformly scaled parent "
                       f"({sheared}): exports wrong, Apply All Transforms",
                       'ERROR'))

    bounds = _world_bounds(obj)
    if bounds is not None:
        lo, hi = bounds
        if abs(lo.z) > 0.01:
            issues.append((f"Floating {lo.z:.2f}m off Z=0", 'INFO'))

        size = max(hi[i] - lo[i] for i in range(3))
        if size > 100:
            issues.append((f"Very large ({size:.0f}m)", 'INFO'))
        elif size < 0.01:
            issues.append((f"Very small ({size:.4f}m)", 'INFO'))

    mesh = obj.data
    if not mesh.uv_layers:
        issues.append(("No UV layer", 'ERROR'))

    bm = bmesh.new()
    bm.from_mesh(mesh)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    loose = sum(1 for v in bm.verts if not v.link_edges)
    interior = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    bm.free()

    if non_manifold:
        issues.append((f"{non_manifold} non-manifold edge"
                       f"{'s' if non_manifold > 1 else ''}", 'ERROR'))
    if loose:
        issues.append((f"{loose} loose vert"
                       f"{'ices' if loose > 1 else 'ex'}", 'ERROR'))
    if interior:
        issues.append((f"{interior} interior edge"
                       f"{'s' if interior > 1 else ''}", 'ERROR'))
    if ngons:
        issues.append((f"{ngons} n-gon{'s' if ngons > 1 else ''}", 'INFO'))

    return issues


class BT_OT_asset_check(Operator):
    bl_idname = "object.bt_asset_check"
    bl_label = "Check Selected"
    bl_description = "Run pre-export checks on every selected mesh"

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        _RESULTS.clear()
        errors = 0
        for obj in [o for o in context.selected_objects if o.type == 'MESH']:
            issues = _check(obj)
            _RESULTS[obj.name] = issues
            errors += sum(1 for _, level in issues if level == 'ERROR')
        self.report({'INFO'} if not errors else {'WARNING'},
                    f"{len(_RESULTS)} checked, {errors} blocking issues")
        return {'FINISHED'}


class BT_OT_asset_fix(Operator):
    bl_idname = "object.bt_asset_fix"
    bl_label = "Fix Mechanical Issues"
    bl_description = ("Apply transforms, drop to floor, remove loose vertices. "
                      "Does not touch UVs or topology")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        for obj in meshes:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            loose = [v for v in bm.verts if not v.link_edges]
            if loose:
                bmesh.ops.delete(bm, geom=loose, context='VERTS')
                bm.to_mesh(obj.data)
                obj.data.update()
            bm.free()
            bounds = _world_bounds(obj)
            if bounds is not None:
                obj.location.z -= bounds[0].z
        _RESULTS.clear()
        self.report({'INFO'}, f"Fixed {len(meshes)} objects")
        return {'FINISHED'}


class BT_PT_asset_check(Panel):
    bl_label = "Asset Check"
    bl_idname = "BT_PT_asset_check"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("object.bt_asset_check", icon='CHECKMARK')
        col.operator("object.bt_asset_fix", icon='MODIFIER')

        if not _RESULTS:
            return
        for name, issues in _RESULTS.items():
            box = layout.box()
            if not issues:
                box.label(text=name, icon='CHECKMARK')
                continue
            box.label(text=name, icon='ERROR')
            for text, level in issues:
                box.label(text=text,
                          icon='CANCEL' if level == 'ERROR' else 'INFO')
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_asset_check, BT_OT_asset_fix, BT_PT_asset_check)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    _RESULTS.clear()
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
