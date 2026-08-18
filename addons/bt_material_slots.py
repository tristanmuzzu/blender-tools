bl_info = {
    "name": "BT Material Slots",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Remove unused material slots and merge duplicate materials",
    "category": "Material",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-material_slots"
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

import re

import bpy
from bpy.types import Operator, Panel

# Blender's duplicate suffix: "Metal.001", "Metal.002"
DUPLICATE = re.compile(r"^(.*)\.\d{3}$")


class BT_OT_clean_slots(Operator):
    bl_idname = "object.bt_clean_slots"
    bl_label = "Remove Unused Slots"
    bl_description = "Delete material slots no face actually uses"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        removed = 0
        active = context.view_layer.objects.active
        for obj in [o for o in context.selected_objects if o.type == 'MESH']:
            if len(obj.data.materials) <= 1:
                continue
            used = {p.material_index for p in obj.data.polygons}
            context.view_layer.objects.active = obj
            # backwards, removing a slot shifts the ones above it
            for index in range(len(obj.data.materials) - 1, -1, -1):
                if index not in used:
                    obj.active_material_index = index
                    bpy.ops.object.material_slot_remove()
                    removed += 1
        context.view_layer.objects.active = active
        self.report({'INFO'}, f"Removed {removed} unused slots")
        return {'FINISHED'}


class BT_OT_merge_duplicates(Operator):
    bl_idname = "object.bt_merge_duplicates"
    bl_label = "Merge Duplicate Materials"
    bl_description = ("Point Metal.001, Metal.002 etc. back at Metal. "
                      "Only merges by name, never by appearance")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        merged = 0
        for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
            for slot in obj.material_slots:
                if slot.material is None:
                    continue
                match = DUPLICATE.match(slot.material.name)
                if not match:
                    continue
                original = bpy.data.materials.get(match.group(1))
                if original is not None and original is not slot.material:
                    slot.material = original
                    merged += 1
        self.report({'INFO'}, f"Repointed {merged} slots")
        return {'FINISHED'}


class BT_PT_material_slots(Panel):
    bl_label = "Material Slots"
    bl_idname = "BT_PT_material_slots"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        col = self.layout.column(align=True)
        col.operator("object.bt_clean_slots", icon='TRASH')
        col.operator("object.bt_merge_duplicates", icon='AUTOMERGE_ON')
        obj = context.active_object
        if obj and obj.type == 'MESH':
            self.layout.label(text=f"{len(obj.data.materials)} slots on active")
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_clean_slots, BT_OT_merge_duplicates, BT_PT_material_slots)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
