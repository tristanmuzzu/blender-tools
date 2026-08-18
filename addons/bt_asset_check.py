bl_info = {
    "name": "BT Asset Check",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
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


def _check(obj):
    issues = []

    if any(abs(s - 1.0) > 1e-4 for s in obj.scale):
        issues.append(("Scale not applied", 'ERROR'))
    if any(abs(r) > 1e-4 for r in obj.rotation_euler):
        issues.append(("Rotation not applied", 'INFO'))

    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    min_z = min(c.z for c in corners)
    if abs(min_z) > 0.01:
        issues.append((f"Floating {min_z:.2f}m off Z=0", 'INFO'))

    size = max((max(c[i] for c in corners) - min(c[i] for c in corners))
               for i in range(3))
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
        issues.append((f"{non_manifold} non-manifold edges", 'ERROR'))
    if loose:
        issues.append((f"{loose} loose vertices", 'ERROR'))
    if interior:
        issues.append((f"{interior} interior edges", 'ERROR'))
    if ngons:
        issues.append((f"{ngons} n-gons", 'INFO'))

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
            corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
            obj.location.z -= min(c.z for c in corners)
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
