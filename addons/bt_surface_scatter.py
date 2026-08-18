bl_info = {
    "name": "BT Surface Scatter",
    "author": "Tristan Muzzu",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > BTools",
    "description": "Scatter instances across a surface with slope limits and jitter",
    "category": "Object",
}

# One tagged link, so a sale that starts here can be told from one that did not.
# `?src=` survives referrer stripping; ops/watch_sales.py `channel_of()` reads it.
PANELFORGE_URL = (
    "https://tristaneer2.gumroad.com/l/panelforge?src=freetools-surface_scatter"
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
import random

import bmesh
import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel
from mathutils import Vector


class BT_OT_surface_scatter(Operator):
    bl_idname = "object.bt_surface_scatter"
    bl_label = "Scatter on Active"
    bl_description = ("Scatter the selected object across the active surface. "
                      "Select the instance first, then the surface last")
    bl_options = {'REGISTER', 'UNDO'}

    count: IntProperty(name="Count", default=200, min=1, max=20000)
    seed: IntProperty(name="Seed", default=0, min=0)
    max_slope: FloatProperty(name="Max Slope", default=math.radians(35),
                             min=0, max=math.pi / 2, subtype='ANGLE',
                             description="Skip faces steeper than this")
    scale_min: FloatProperty(name="Scale Min", default=0.8, min=0.01, soft_max=4)
    scale_max: FloatProperty(name="Scale Max", default=1.25, min=0.01, soft_max=4)
    align_normal: BoolProperty(name="Align to Normal", default=False)
    random_yaw: BoolProperty(name="Random Rotation", default=True)
    collection_name: StringProperty(name="Collection", default="BT_Scatter")

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None
                and context.active_object.type == 'MESH'
                and len(context.selected_objects) >= 2)

    def execute(self, context):
        surface = context.active_object
        sources = [o for o in context.selected_objects if o is not surface]
        if not sources:
            self.report({'ERROR'}, "Select an object to scatter, then the surface")
            return {'CANCELLED'}

        rng = random.Random(self.seed)

        bm = bmesh.new()
        bm.from_mesh(surface.data)
        bm.faces.ensure_lookup_table()

        # weight by area, or small faces get as many instances as big ones
        faces, weights, total = [], [], 0.0
        up = Vector((0, 0, 1))
        for face in bm.faces:
            normal = (surface.matrix_world.to_3x3() @ face.normal).normalized()
            if normal.angle(up) > self.max_slope:
                continue
            area = face.calc_area()
            if area <= 0:
                continue
            faces.append(face)
            total += area
            weights.append(total)

        if not faces:
            bm.free()
            self.report({'WARNING'}, "No faces within the slope limit")
            return {'CANCELLED'}

        coll = bpy.data.collections.get(self.collection_name)
        if coll is None:
            coll = bpy.data.collections.new(self.collection_name)
            context.scene.collection.children.link(coll)

        import bisect
        placed = 0
        for _ in range(self.count):
            face = faces[bisect.bisect_left(weights, rng.random() * total)]
            verts = [v.co for v in face.verts]
            # random point in the first tri
            a, b, c = verts[0], verts[1], verts[2 % len(verts)]
            u, v = rng.random(), rng.random()
            if u + v > 1:
                u, v = 1 - u, 1 - v
            local = a + (b - a) * u + (c - a) * v
            world = surface.matrix_world @ local

            inst = bpy.data.objects.new(f"{sources[0].name}_scatter",
                                        rng.choice(sources).data)
            coll.objects.link(inst)
            inst.location = world
            scale = rng.uniform(self.scale_min, self.scale_max)
            inst.scale = (scale, scale, scale)
            if self.align_normal:
                normal = (surface.matrix_world.to_3x3() @ face.normal).normalized()
                inst.rotation_euler = normal.to_track_quat('Z', 'Y').to_euler()
            if self.random_yaw:
                inst.rotation_euler.z += rng.uniform(0, math.tau)
            placed += 1

        bm.free()
        self.report({'INFO'}, f"Scattered {placed} instances")
        return {'FINISHED'}


class BT_PT_surface_scatter(Panel):
    bl_label = "Surface Scatter"
    bl_idname = "BT_PT_surface_scatter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BTools"

    def _bt_draw_body(self, context):
        self.layout.operator("object.bt_surface_scatter", icon='OUTLINER_OB_POINTCLOUD')
        self.layout.label(text="Select instance, then surface")
    def draw(self, context):
        self._bt_draw_body(context)
        _bt_footer(self.layout)


CLASSES = (BT_OT_surface_scatter, BT_PT_surface_scatter)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
