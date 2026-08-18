bl_info = {
    "name": "BT Mesh Stats",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Live triangle, n-gon, loose vertex and UV readout for the active mesh",
    "category": "Object",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-mesh_stats"
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


def _stats(obj, evaluated=True):
    """Counts for the active mesh. Evaluated shows what actually renders."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    source = obj.evaluated_get(depsgraph) if evaluated else obj
    mesh = source.to_mesh() if evaluated else obj.data

    try:
        mesh.calc_loop_triangles()
        tris = len(mesh.loop_triangles)
        verts = len(mesh.vertices)
        ngons = sum(1 for p in mesh.polygons if len(p.vertices) > 4)
        tri_faces = sum(1 for p in mesh.polygons if len(p.vertices) == 3)
        quads = sum(1 for p in mesh.polygons if len(p.vertices) == 4)
        uvs = len(mesh.uv_layers)

        bm = bmesh.new()
        bm.from_mesh(mesh)
        loose = sum(1 for v in bm.verts if not v.link_edges)
        non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
        bm.free()
    finally:
        if evaluated:
            source.to_mesh_clear()

    return {"tris": tris, "verts": verts, "ngons": ngons, "quads": quads,
            "tri_faces": tri_faces, "uvs": uvs, "loose": loose,
            "non_manifold": non_manifold}


class BT_OT_select_ngons(Operator):
    bl_idname = "object.bt_select_ngons"
    bl_label = "Select N-gons"
    bl_description = "Enter edit mode with every face over four sides selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        if context.object.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_face_by_sides(number=4, type='GREATER')
        return {'FINISHED'}


class BT_PT_mesh_stats(Panel):
    bl_label = "Mesh Stats"
    bl_idname = "BT_PT_mesh_stats"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        layout = self.layout
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            layout.label(text="Select a mesh", icon='INFO')
            return

        try:
            s = _stats(obj)
        except Exception as exc:  # noqa: BLE001 -- a panel draw() that raises
            # spams the console every redraw and can wedge the UI. Whatever
            # the mesh did, the panel says so and keeps drawing.
            layout.label(text=f"Unavailable: {exc}", icon='ERROR')
            return

        col = layout.column(align=True)
        col.label(text=f"Triangles: {s['tris']:,}")
        col.label(text=f"Vertices: {s['verts']:,}")
        col.label(text=f"Quads: {s['quads']:,}   Tris: {s['tri_faces']:,}")

        box = layout.box()
        box.label(text="Warnings", icon='ERROR' if (
            s['ngons'] or s['loose'] or s['non_manifold'] or not s['uvs'])
            else 'CHECKMARK')
        if s['ngons']:
            row = box.row()
            row.label(text=f"N-gons: {s['ngons']}")
            row.operator("object.bt_select_ngons", text="", icon='RESTRICT_SELECT_OFF')
        if s['loose']:
            box.label(text=f"Loose verts: {s['loose']}")
        if s['non_manifold']:
            box.label(text=f"Non-manifold edges: {s['non_manifold']}")
        if not s['uvs']:
            box.label(text="No UV layer")
        if not (s['ngons'] or s['loose'] or s['non_manifold']) and s['uvs']:
            box.label(text="Clean")
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_select_ngons, BT_PT_mesh_stats)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
