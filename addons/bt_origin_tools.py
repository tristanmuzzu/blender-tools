bl_info = {
    "name": "BT Origin Tools",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Set object origin to bottom, centre, or world zero in one click",
    "category": "Object",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-origin_tools"
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


def _world_bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector((min(c.x for c in corners),
                 min(c.y for c in corners),
                 min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners),
                 max(c.y for c in corners),
                 max(c.z for c in corners)))
    return lo, hi


class BT_OT_set_origin(Operator):
    bl_idname = "object.bt_set_origin"
    bl_label = "Set Origin"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(
        name="Mode",
        items=[
            ('BOTTOM', "Bottom Centre", "Base of the bounding box — what game engines expect"),
            ('CENTRE', "Bounding Centre", "Middle of the bounding box"),
            ('WORLD', "World Origin", "Move origin to 0,0,0 without moving geometry"),
        ],
        default='BOTTOM')

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        cursor = context.scene.cursor
        saved = cursor.location.copy()
        done = 0

        for obj in [o for o in context.selected_objects if o.type == 'MESH']:
            lo, hi = _world_bounds(obj)
            if self.mode == 'BOTTOM':
                target = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
            elif self.mode == 'CENTRE':
                target = (lo + hi) / 2
            else:
                target = Vector((0, 0, 0))

            cursor.location = target
            # origin_set hits the whole selection, so do them one at a time
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            done += 1

        cursor.location = saved
        self.report({'INFO'}, f"Origin set on {done} objects")
        return {'FINISHED'}


class BT_OT_drop_to_floor(Operator):
    bl_idname = "object.bt_drop_to_floor"
    bl_label = "Drop to Floor"
    bl_description = "Move selected objects so their lowest point rests on Z=0"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        for obj in [o for o in context.selected_objects if o.type == 'MESH']:
            lo, _ = _world_bounds(obj)
            obj.location.z -= lo.z
        return {'FINISHED'}


class BT_PT_origin_tools(Panel):
    bl_label = "Origin Tools"
    bl_idname = "BT_PT_origin_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        col = self.layout.column(align=True)
        for mode, label, icon in (('BOTTOM', "Origin to Bottom", 'TRIA_DOWN_BAR'),
                                  ('CENTRE', "Origin to Centre", 'PIVOT_BOUNDBOX'),
                                  ('WORLD', "Origin to World", 'EMPTY_AXIS')):
            col.operator("object.bt_set_origin", text=label, icon=icon).mode = mode
        self.layout.operator("object.bt_drop_to_floor", icon='EXPORT')
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_set_origin, BT_OT_drop_to_floor, BT_PT_origin_tools)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
