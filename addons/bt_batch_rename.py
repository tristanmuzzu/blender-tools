bl_info = {
    "name": "BT Batch Rename",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Rename selected objects by pattern, with numbering and find/replace",
    "category": "Object",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-batch_rename"
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
from bpy.props import BoolProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel


class BT_OT_batch_rename(Operator):
    bl_idname = "object.bt_batch_rename"
    bl_label = "Rename Selected"
    bl_options = {'REGISTER', 'UNDO'}

    pattern: StringProperty(
        name="Pattern", default="Asset_###",
        description="Use # as digit placeholders, e.g. Crate_###")
    start: IntProperty(name="Start At", default=1, min=0)
    rename_data: BoolProperty(
        name="Rename Mesh Data", default=True,
        description="Keep object data names in sync, which most exporters use")

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        # sort by name so the numbering is the same every run
        objects = sorted(context.selected_objects, key=lambda o: o.name)
        hashes = self.pattern.count("#")
        for index, obj in enumerate(objects):
            number = str(self.start + index).zfill(max(hashes, 1))
            name = (self.pattern.replace("#" * hashes, number) if hashes
                    else f"{self.pattern}_{number}")
            obj.name = name
            if self.rename_data and obj.data is not None:
                obj.data.name = name
        self.report({'INFO'}, f"Renamed {len(objects)} objects")
        return {'FINISHED'}


class BT_OT_find_replace(Operator):
    bl_idname = "object.bt_find_replace"
    bl_label = "Find & Replace"
    bl_options = {'REGISTER', 'UNDO'}

    find: StringProperty(name="Find", default="")
    replace: StringProperty(name="Replace", default="")
    rename_data: BoolProperty(name="Rename Mesh Data", default=True)

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        if not self.find:
            self.report({'WARNING'}, "Nothing to find")
            return {'CANCELLED'}
        changed = 0
        for obj in context.selected_objects:
            if self.find in obj.name:
                obj.name = obj.name.replace(self.find, self.replace)
                changed += 1
            if self.rename_data and obj.data and self.find in obj.data.name:
                obj.data.name = obj.data.name.replace(self.find, self.replace)
        self.report({'INFO'}, f"Changed {changed} names")
        return {'FINISHED'}


class BT_PT_batch_rename(Panel):
    bl_label = "Batch Rename"
    bl_idname = "BT_PT_batch_rename"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        col = self.layout.column(align=True)
        col.operator("object.bt_batch_rename", icon='SORTALPHA')
        col.operator("object.bt_find_replace", icon='VIEWZOOM')
        self.layout.label(text=f"{len(context.selected_objects)} selected")
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_batch_rename, BT_OT_find_replace, BT_PT_batch_rename)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
