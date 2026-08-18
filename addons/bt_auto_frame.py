bl_info = {
    "name": "BT Auto Frame",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Position the camera so the selection fills a chosen fraction of frame",
    "category": "Camera",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-auto_frame"
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
from bpy.props import FloatProperty, FloatVectorProperty
from bpy.types import Operator, Panel
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


class BT_OT_auto_frame(Operator):
    bl_idname = "object.bt_auto_frame"
    bl_label = "Frame Selection"
    bl_description = "Move the scene camera so the selection fills the frame"
    bl_options = {'REGISTER', 'UNDO'}

    fill: FloatProperty(name="Fill", default=0.85, min=0.1, max=1.0,
                        subtype='FACTOR',
                        description="Fraction of the frame the subject spans")
    direction: FloatVectorProperty(name="Direction", default=(0.8, -0.9, 0.45),
                                   size=3)

    @classmethod
    def poll(cls, context):
        return (context.scene.camera is not None
                and any(o.type == 'MESH' for o in context.selected_objects))

    def execute(self, context):
        scene = context.scene
        cam = scene.camera

        # bound_box corners usually aren't on the silhouette, so use real verts
        points = []
        for obj in [o for o in context.selected_objects if o.type == 'MESH']:
            points += [obj.matrix_world @ v.co for v in obj.data.vertices]
        if not points:
            self.report({'WARNING'}, "No geometry to frame")
            return {'CANCELLED'}
        if len(points) > 4000:
            points = points[::len(points) // 4000]

        centre = sum(points, Vector()) / len(points)
        radius = max((p - centre).length for p in points) or 1.0
        direction = Vector(self.direction).normalized()

        def span(distance):
            cam.location = centre + direction * distance
            cam.rotation_mode = 'QUATERNION'
            cam.rotation_quaternion = (centre - cam.location).to_track_quat('-Z', 'Y')
            context.view_layer.update()
            xs, ys = [], []
            for p in points:
                ndc = world_to_camera_view(scene, cam, p)
                if ndc.z <= 0:
                    return 99.0
                xs.append(ndc.x)
                ys.append(ndc.y)
            return max(max(xs) - min(xs), max(ys) - min(ys))

        low, high = radius * 0.4, radius * 25.0
        for _ in range(42):
            mid = (low + high) * 0.5
            if span(mid) > self.fill:
                low = mid
            else:
                high = mid
        span(high)
        self.report({'INFO'}, f"Framed at {high:.2f}m")
        return {'FINISHED'}


class BT_PT_auto_frame(Panel):
    bl_label = "Auto Frame"
    bl_idname = "BT_PT_auto_frame"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        self.layout.operator("object.bt_auto_frame", icon='CAMERA_DATA')
        if context.scene.camera is None:
            self.layout.label(text="No scene camera", icon='ERROR')
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_auto_frame, BT_PT_auto_frame)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
