bl_info = {
    "name": "BT Seam by Angle",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Mark UV seams on sharp edges, then unwrap in one step",
    "category": "UV",
}

import math

import bmesh
import bpy
from bpy.props import BoolProperty, FloatProperty
from bpy.types import Operator, Panel


class BT_OT_seam_by_angle(Operator):
    bl_idname = "mesh.bt_seam_by_angle"
    bl_label = "Seam by Angle"
    bl_options = {'REGISTER', 'UNDO'}

    angle: FloatProperty(name="Angle", default=math.radians(45),
                         min=0, max=math.pi, subtype='ANGLE',
                         description="Edges sharper than this become seams")
    clear_existing: BoolProperty(name="Clear Existing Seams", default=True)
    mark_sharp: BoolProperty(name="Also Mark Sharp", default=False)
    unwrap: BoolProperty(name="Unwrap After", default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        started_in_edit = obj.mode == 'EDIT'
        if started_in_edit:
            bpy.ops.object.mode_set(mode='OBJECT')

        bm = bmesh.new()
        bm.from_mesh(obj.data)

        marked = 0
        for edge in bm.edges:
            if self.clear_existing:
                edge.seam = False
            if len(edge.link_faces) != 2:
                # boundaries already act as seams
                continue
            if edge.calc_face_angle(0.0) >= self.angle:
                edge.seam = True
                if self.mark_sharp:
                    edge.smooth = False
                marked += 1

        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()

        if self.unwrap:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            try:
                bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.002)
            except RuntimeError as exc:
                self.report({'WARNING'}, f"Unwrap failed: {exc}")
            if not started_in_edit:
                bpy.ops.object.mode_set(mode='OBJECT')
        elif started_in_edit:
            bpy.ops.object.mode_set(mode='EDIT')

        self.report({'INFO'}, f"Marked {marked} seam edges")
        return {'FINISHED'}


class BT_PT_seam_by_angle(Panel):
    bl_label = "Seam by Angle"
    bl_idname = "BT_PT_seam_by_angle"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def draw(self, context):
        self.layout.operator("mesh.bt_seam_by_angle", icon='UV_EDGESEL')


CLASSES = (BT_OT_seam_by_angle, BT_PT_seam_by_angle)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
