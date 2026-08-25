bl_info = {
    "name": "BT Turntable",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "One-click turntable: orbits the camera around the selection",
    "category": "Animation",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-turntable"
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

import math

import bpy
from bpy.props import BoolProperty, IntProperty
from bpy.types import Operator, Panel
from mathutils import Vector

PIVOT_NAME = "BT_Turntable_Pivot"


def _fcurves(action):
    """Every F-curve of an action, on both Action APIs.

    `Action.fcurves` is gone from 5.0 on, where the curves moved into
    layers -> strips -> channelbags. 4.5 answers to both. Returns an empty list
    rather than raising if neither shape is there, because the caller's job is
    to set interpolation and a missing curve is not worth taking a tool down
    for.
    """
    curves = getattr(action, "fcurves", None)
    if curves is not None:
        return list(curves)
    out = []
    slots = list(getattr(action, "slots", []))
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            bags = []
            if hasattr(strip, "channelbag"):
                bags = [strip.channelbag(slot) for slot in slots]
            elif hasattr(strip, "channelbags"):
                bags = list(strip.channelbags)
            out += [fc for bag in bags if bag is not None for fc in bag.fcurves]
    return out


class BT_OT_turntable(Operator):
    bl_idname = "object.bt_turntable"
    bl_label = "Build Turntable"
    bl_options = {'REGISTER', 'UNDO'}

    frames: IntProperty(name="Frames", default=120, min=8, max=1000)
    clockwise: BoolProperty(name="Clockwise", default=True)
    set_range: BoolProperty(name="Set Scene Range", default=True)

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None and context.selected_objects

    def execute(self, context):
        scene = context.scene
        cam = scene.camera

        points = []
        for obj in context.selected_objects:
            points += [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        centre = sum(points, Vector()) / len(points)

        # reuse the pivot, otherwise re-running piles up empties
        pivot = bpy.data.objects.get(PIVOT_NAME)
        if pivot is None:
            pivot = bpy.data.objects.new(PIVOT_NAME, None)
            scene.collection.objects.link(pivot)
        pivot.location = centre
        pivot.rotation_euler = (0, 0, 0)
        pivot.animation_data_clear()

        if cam.parent != pivot:
            matrix = cam.matrix_world.copy()
            cam.parent = pivot
            cam.matrix_world = matrix

        turn = -math.tau if self.clockwise else math.tau

        # Needs linear, or the spin eases in and out and the loop stutters.
        #
        # This used to set `preferences.edit.keyframe_new_interpolation_type`
        # and trust it, because `action.fcurves` is gone from 5.0 on. That
        # preference does not reach `keyframe_insert()` at all: measured on
        # 3.6.23, 4.2.23 and 5.2.1, the keys come out BEZIER with the pref
        # reading LINEAR, and the turntable eased on every version for its
        # whole life. Frame 2 of 48 sat at 0.0084 radians where linear is
        # 0.1337. So set it on the keyframes, through `_fcurves`, which knows
        # both Action layouts.
        pivot.rotation_euler = (0, 0, 0)
        pivot.keyframe_insert("rotation_euler", frame=1)
        pivot.rotation_euler = (0, 0, turn)
        pivot.keyframe_insert("rotation_euler", frame=self.frames)
        action = pivot.animation_data.action if pivot.animation_data else None
        if action is not None:
            for curve in _fcurves(action):
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'
                curve.update()

        if self.set_range:
            scene.frame_start = 1
            # -1 because frame 1 and frame N are the same pose
            scene.frame_end = self.frames - 1

        self.report({'INFO'}, f"Turntable over {self.frames} frames")
        return {'FINISHED'}


class BT_OT_turntable_clear(Operator):
    bl_idname = "object.bt_turntable_clear"
    bl_label = "Clear Turntable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pivot = bpy.data.objects.get(PIVOT_NAME)
        if pivot is None:
            self.report({'INFO'}, "No turntable found")
            return {'CANCELLED'}
        for child in list(pivot.children):
            matrix = child.matrix_world.copy()
            child.parent = None
            child.matrix_world = matrix
        bpy.data.objects.remove(pivot, do_unlink=True)
        return {'FINISHED'}


class BT_PT_turntable(Panel):
    bl_label = "Turntable"
    bl_idname = "BT_PT_turntable"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        col = self.layout.column(align=True)
        col.operator("object.bt_turntable", icon='FILE_MOVIE')
        col.operator("object.bt_turntable_clear", icon='TRASH')
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_turntable, BT_OT_turntable_clear, BT_PT_turntable)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
