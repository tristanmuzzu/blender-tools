bl_info = {
    "name": "BT Align & Distribute",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Align objects on an axis and space them evenly",
    "category": "Object",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-align_distribute"
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

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator, Panel
from mathutils import Vector

AXES = (('X', "X", ""), ('Y', "Y", ""), ('Z', "Z", ""))
INDEX = {'X': 0, 'Y': 1, 'Z': 2}


def _bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return ([min(c[i] for c in corners) for i in range(3)],
            [max(c[i] for c in corners) for i in range(3)])


class BT_OT_align(Operator):
    bl_idname = "object.bt_align"
    bl_label = "Align"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(name="Axis", items=AXES, default='X')
    mode: EnumProperty(
        name="Mode",
        items=[('MIN', "Min", "Lowest edge"),
               ('CENTRE', "Centre", "Bounding centre"),
               ('MAX', "Max", "Highest edge")],
        default='CENTRE')

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 2

    def execute(self, context):
        i = INDEX[self.axis]
        objects = context.selected_objects
        active = context.view_layer.objects.active
        anchor = active if active in objects else objects[0]

        lo, hi = _bounds(anchor)
        target = {'MIN': lo[i], 'MAX': hi[i],
                  'CENTRE': (lo[i] + hi[i]) / 2}[self.mode]

        for obj in objects:
            if obj is anchor:
                continue
            olo, ohi = _bounds(obj)
            current = {'MIN': olo[i], 'MAX': ohi[i],
                       'CENTRE': (olo[i] + ohi[i]) / 2}[self.mode]
            obj.location[i] += target - current

        self.report({'INFO'}, f"Aligned {len(objects) - 1} to {anchor.name}")
        return {'FINISHED'}


class BT_OT_distribute(Operator):
    bl_idname = "object.bt_distribute"
    bl_label = "Distribute Evenly"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(name="Axis", items=AXES, default='X')

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 3

    def execute(self, context):
        i = INDEX[self.axis]
        # outer two stay put, everything between gets respaced
        objects = sorted(context.selected_objects,
                         key=lambda o: (_bounds(o)[0][i] + _bounds(o)[1][i]) / 2)
        first = (_bounds(objects[0])[0][i] + _bounds(objects[0])[1][i]) / 2
        last = (_bounds(objects[-1])[0][i] + _bounds(objects[-1])[1][i]) / 2
        gaps = len(objects) - 1
        if gaps < 2:
            return {'CANCELLED'}
        step = (last - first) / gaps

        for n, obj in enumerate(objects[1:-1], start=1):
            lo, hi = _bounds(obj)
            centre = (lo[i] + hi[i]) / 2
            obj.location[i] += (first + step * n) - centre

        self.report({'INFO'}, f"Distributed {len(objects)} objects")
        return {'FINISHED'}


class BT_PT_align(Panel):
    bl_label = "Align & Distribute"
    bl_idname = "BT_PT_align"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        layout = self.layout
        for axis in ("X", "Y", "Z"):
            row = layout.row(align=True)
            row.label(text=axis)
            for mode, label in (('MIN', "Min"), ('CENTRE', "Mid"), ('MAX', "Max")):
                op = row.operator("object.bt_align", text=label)
                op.axis, op.mode = axis, mode
        layout.separator()
        row = layout.row(align=True)
        for axis in ("X", "Y", "Z"):
            row.operator("object.bt_distribute",
                         text=f"Space {axis}").axis = axis
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_align, BT_OT_distribute, BT_PT_align)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
