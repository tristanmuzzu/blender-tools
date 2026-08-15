bl_info = {
    "name": "BT Material Slots",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Remove unused material slots and merge duplicate materials",
    "category": "Material",
}

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
            # Walk backwards: removing a slot shifts every index above it.
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

    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator("object.bt_clean_slots", icon='TRASH')
        col.operator("object.bt_merge_duplicates", icon='AUTOMERGE_ON')
        obj = context.active_object
        if obj and obj.type == 'MESH':
            self.layout.label(text=f"{len(obj.data.materials)} slots on active")


CLASSES = (BT_OT_clean_slots, BT_OT_merge_duplicates, BT_PT_material_slots)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
