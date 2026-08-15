bl_info = {
    "name": "BT Quick Export",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Export selection to glTF or FBX with Unity/Unreal-safe presets",
    "category": "Import-Export",
}

import os

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, Panel


class BT_OT_quick_export(Operator):
    bl_idname = "export_scene.bt_quick_export"
    bl_label = "Export Selection"
    bl_options = {'REGISTER'}

    directory: StringProperty(name="Folder", subtype='DIR_PATH', default="//")
    fmt: EnumProperty(
        name="Format",
        items=[('GLTF', "glTF (.glb)", "Portable, engine-neutral"),
               ('FBX', "FBX", "Widest engine support")],
        default='GLTF')
    target: EnumProperty(
        name="Target",
        items=[('GENERIC', "Generic", "No axis conversion"),
               ('UNITY', "Unity", "Y-up, +Z forward"),
               ('UNREAL', "Unreal", "Z-up, -Y forward")],
        default='GENERIC')
    separate: BoolProperty(
        name="One File Per Object", default=False,
        description="Export each selected object to its own file")
    apply_transform: BoolProperty(name="Apply Transform", default=True)

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def _axes(self):
        if self.target == 'UNITY':
            return 'Y', 'Z'
        if self.target == 'UNREAL':
            return 'Z', '-Y'
        return 'Y', '-Z'

    def _write(self, context, path, name):
        filepath = os.path.join(path, name)
        up, forward = self._axes()
        if self.fmt == 'GLTF':
            bpy.ops.export_scene.gltf(
                filepath=filepath + ".glb", export_format='GLB',
                use_selection=True, export_apply=self.apply_transform)
        else:
            bpy.ops.export_scene.fbx(
                filepath=filepath + ".fbx", use_selection=True,
                axis_up=up, axis_forward=forward,
                apply_unit_scale=True, bake_space_transform=self.apply_transform,
                mesh_smooth_type='FACE')

    def execute(self, context):
        directory = bpy.path.abspath(self.directory)
        if not os.path.isdir(directory):
            self.report({'ERROR'}, f"Not a folder: {directory}")
            return {'CANCELLED'}

        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        written = 0

        if self.separate:
            # Restore the original selection afterwards; silently changing it
            # is the kind of side effect that earns one-star reviews.
            original = list(context.selected_objects)
            active = context.view_layer.objects.active
            for obj in meshes:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                self._write(context, directory, obj.name)
                written += 1
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original:
                obj.select_set(True)
            context.view_layer.objects.active = active
        else:
            name = meshes[0].name if len(meshes) == 1 else "export"
            self._write(context, directory, name)
            written = 1

        self.report({'INFO'}, f"Exported {written} file(s) to {directory}")
        return {'FINISHED'}


class BT_PT_quick_export(Panel):
    bl_label = "Quick Export"
    bl_idname = "BT_PT_quick_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def draw(self, context):
        self.layout.operator("export_scene.bt_quick_export", icon='EXPORT')
        count = sum(1 for o in context.selected_objects if o.type == 'MESH')
        self.layout.label(text=f"{count} mesh objects selected")


CLASSES = (BT_OT_quick_export, BT_PT_quick_export)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
