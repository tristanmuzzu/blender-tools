bl_info = {
    "name": "BT Quick Export",
    "author": "Tristan Muzzu",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Export selection to glTF or FBX with Unity/Unreal-safe presets",
    "category": "Import-Export",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-quick_export"
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

import os

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, Panel


class ExporterTooOld(Exception):
    """Blender's own exporter on this build cannot do what was asked.

    Measured on 2026-09-13. Blender 5.0.1 ships an FBX exporter whose operator
    registers **4** settable properties -- `axis_forward`, `axis_up`,
    `check_existing`, `filepath` -- against **42** on 4.2.23, 4.5.12, 4.5.13,
    5.2.0 and 5.2.1 and **41** on 3.6.23. That is F-017 seen from the caller's
    side. Passing `use_selection` to it raises `TypeError: keyword
    "use_selection" unrecognized` straight out of the operator, and before this
    change the traceback was what a user got: no file, no message of ours, and
    a red line in the console.
    """

    def __init__(self, fmt):
        super().__init__(fmt)
        self.fmt = fmt


def _settable(op):
    """Which keywords this build's exporter will actually accept.

    Read off the operator rather than off `bpy.app.version`, because the thing
    that varies is which add-on registered and how, not the version number.
    `bpy.types.EXPORT_SCENE_OT_fbx.bl_rna` is the wrong door: under
    `--factory-startup` it reports the same 7 base properties on every build,
    including the ones where the export works.
    """
    try:
        return {prop.identifier for prop in op.get_rna_type().properties
                if not prop.is_readonly}
    except (AttributeError, RuntimeError):
        return set()


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
            op = bpy.ops.export_scene.gltf
            wanted = {"filepath": filepath + ".glb", "export_format": 'GLB',
                      "use_selection": True,
                      "export_apply": self.apply_transform}
        else:
            op = bpy.ops.export_scene.fbx
            wanted = {"filepath": filepath + ".fbx", "use_selection": True,
                      "axis_up": up, "axis_forward": forward,
                      "apply_unit_scale": True,
                      "bake_space_transform": self.apply_transform,
                      "mesh_smooth_type": 'FACE'}
        have = _settable(op)
        # `use_selection` is not a preference. Without it the exporter writes
        # the whole scene, and this operator is called Export Selection.
        if "use_selection" not in have:
            raise ExporterTooOld(self.fmt)
        op(**{k: v for k, v in wanted.items() if k in have})
        return filepath

    def execute(self, context):
        directory = bpy.path.abspath(self.directory)
        if not os.path.isdir(directory):
            self.report({'ERROR'}, f"Not a folder: {directory}")
            return {'CANCELLED'}

        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        written = 0

        try:
            if self.separate:
                # put the selection back when we're done
                original = list(context.selected_objects)
                active = context.view_layer.objects.active
                try:
                    for obj in meshes:
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                        self._write(context, directory, obj.name)
                        written += 1
                finally:
                    # the selection goes back even if the export gave up
                    # partway, because losing it is a worse surprise than the
                    # missing file the user is about to be told about
                    bpy.ops.object.select_all(action='DESELECT')
                    for obj in original:
                        obj.select_set(True)
                    context.view_layer.objects.active = active
            else:
                name = meshes[0].name if len(meshes) == 1 else "export"
                self._write(context, directory, name)
                written = 1
        except ExporterTooOld as exc:
            # The glTF branch has never fired on any build here and is not
            # expected to. It has its own sentence anyway, because control B
            # of this fix stubbed every exporter as unsupported and produced
            # "cut-down GLTF exporter ... Use glTF", which is nonsense a user
            # would have had to read.
            if exc.fmt == 'FBX':
                advice = ("Use glTF, or a Blender where File > Export > FBX "
                          "has its full options panel")
            else:
                advice = ("Export it with File > Export > glTF 2.0 instead; "
                          "this build's glTF exporter is missing options this "
                          "add-on relies on")
            self.report(
                {'ERROR'},
                f"This Blender ({bpy.app.version_string}) ships a cut-down "
                f"{exc.fmt} exporter that cannot export a selection. "
                f"Nothing was written. {advice}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Exported {written} file(s) to {directory}")
        return {'FINISHED'}


class BT_PT_quick_export(Panel):
    bl_label = "Quick Export"
    bl_idname = "BT_PT_quick_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        self.layout.operator("export_scene.bt_quick_export", icon='EXPORT')
        count = sum(1 for o in context.selected_objects if o.type == 'MESH')
        self.layout.label(text=f"{count} mesh objects selected")
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_quick_export, BT_PT_quick_export)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
