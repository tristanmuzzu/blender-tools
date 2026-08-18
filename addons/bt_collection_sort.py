bl_info = {
    "name": "BT Collection Sort",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Sort objects into collections by type, name prefix, or material",
    "category": "Object",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-collection_sort"
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

import contextlib

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, Panel

TYPE_NAMES = {
    'MESH': "Meshes", 'LIGHT': "Lights", 'CAMERA': "Cameras",
    'EMPTY': "Empties", 'CURVE': "Curves", 'ARMATURE': "Armatures",
}


def _collection(scene, name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        scene.collection.children.link(coll)
    elif name not in {c.name for c in scene.collection.children}:
        with contextlib.suppress(RuntimeError):
            scene.collection.children.link(coll)
    return coll


class BT_OT_collection_sort(Operator):
    bl_idname = "object.bt_collection_sort"
    bl_label = "Sort Into Collections"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(
        name="Sort By",
        items=[('TYPE', "Object Type", "Meshes, lights, cameras..."),
               ('PREFIX', "Name Prefix", "Text before the separator"),
               ('MATERIAL', "First Material", "Material in slot 0")],
        default='TYPE')
    separator: StringProperty(name="Separator", default="_")
    selected_only: BoolProperty(name="Selected Only", default=True)

    def _target(self, obj):
        if self.mode == 'TYPE':
            return TYPE_NAMES.get(obj.type, obj.type.title())
        if self.mode == 'PREFIX':
            return obj.name.split(self.separator)[0] or "Unsorted"
        mats = getattr(obj.data, "materials", None)
        if mats and len(mats) and mats[0] is not None:
            return mats[0].name
        return "No Material"

    def execute(self, context):
        scene = context.scene
        objects = (context.selected_objects if self.selected_only
                   else list(scene.objects))
        if not objects:
            self.report({'WARNING'}, "Nothing to sort")
            return {'CANCELLED'}

        moved = 0
        for obj in objects:
            target = _collection(scene, self._target(obj))
            if target.name in {c.name for c in obj.users_collection}:
                continue
            for coll in list(obj.users_collection):
                coll.objects.unlink(obj)
            target.objects.link(obj)
            moved += 1

        self.report({'INFO'}, f"Moved {moved} objects")
        return {'FINISHED'}


class BT_PT_collection_sort(Panel):
    bl_label = "Collection Sort"
    bl_idname = "BT_PT_collection_sort"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        col = self.layout.column(align=True)
        for mode, label, icon in (('TYPE', "By Type", 'OUTLINER'),
                                  ('PREFIX', "By Name Prefix", 'SORTALPHA'),
                                  ('MATERIAL', "By Material", 'MATERIAL')):
            col.operator("object.bt_collection_sort", text=label,
                         icon=icon).mode = mode
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_collection_sort, BT_PT_collection_sort)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
