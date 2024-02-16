import numpy as np
import os
import typing as t
import math

import cadquery as cq



class MathUtils:
    @staticmethod
    def rotate_around_origin(point, angle):
        x, y = point
        return np.array(
            [
                x * math.cos(angle) - y * math.sin(angle),
                x * math.sin(angle) + y * math.cos(angle),
            ]
        )


class PartBuilder:
    def __init__(self) -> None:
        self.property_router = None

    def build(self):
        raise NotImplementedError("no build method")

    def build_for_print(self, built=None):
        if not built:
            built = self.build()
        return built, [built]

    def add_to_side(self, obj, scene, translate_amount=None, extra=None):
        if translate_amount is None:
            try:
                xmax = scene.findSolid().BoundingBox().xmax
            except:
                xmax = 0
            try:
                obj_bb = obj.val().BoundingBox()
            except:
                obj_bb = obj.BoundingBox()

            translate_amount = xmax - obj_bb.xmin
            translate_amount = xmax - obj_bb.xmin

        scene = scene.add(
            obj.translate((translate_amount + extra if extra else 0, 0, 0))
        )
        return scene, translate_amount


class PenHolderBuilder(PartBuilder):
    def __init__(self, thickness, pen_radius, pen_connection_length):
        self.thickness = thickness
        self.pen_radius = pen_radius
        self.pen_connection_length = pen_connection_length
        self.slack = 0

    def build(self):
        cyl = cq.Workplane("XY").cylinder(
            height=self.pen_connection_length, radius=self.pen_radius + self.thickness
        )
        cyl = (
            cyl.faces(">Z")
            .workplane()
            .hole(diameter=(self.pen_radius * (1 + self.slack)) * 2)
        )

        return cyl


class FanMotorHolder(PartBuilder):
    def __init__(self, fcb, motor_radius, motor_length):
        self.fcb = fcb
        self.thickness = self.fcb.thickness
        self.motor_radius = motor_radius
        self.motor_length = motor_length
        self.slack = 0.08
        self.tighten = 1.03

    def arc_around(self, one, two, three, thickness, base=None):
        if base is None:
            base = cq.Workplane("XY")

        def out(p):
            norm = p / np.linalg.norm(p)
            return p + norm * thickness

        return (
            base.moveTo(*one)
            .threePointArc(two, three)
            .moveTo(*three)
            .lineTo(*out(three))
            .threePointArc(out(two), out(one))
            .close()
        )

    def build(self):
        scene = cq.Workplane("XY")

        slack = self.thickness * 0.95
        self.fcb.fan_hull_radius += slack

        around2d, base = self.fcb.get_around_base()

        around = around2d.extrude(self.thickness)
        around2d, _ = self.fcb.get_around_base(cap=True)
        around = around.add(around2d.extrude(-self.thickness * 3))
        base = base.extrude(self.thickness)

        fill = (
            cq.Workplane("XY")
            .sketch()
            .circle(self.fcb.fan_hull_radius)
            .circle(self.motor_radius * self.tighten, mode="s")
            .finalize()
            .extrude(self.thickness)
        )

        self.fcb.fan_hull_radius -= slack

        base_radius = self.motor_radius * self.tighten * 1.4

        # md = MathUtils.rotate_around_origin(np.array([0, base_radius]), math.pi/4)
        # dist = math.pi * .99
        # bridge_length = self.motor_length/5 * 1.5
        # # lower = cq.sketch().circle(base_radius).circle(base_radius - self.thickness, mode="s").finalize()

        # md = MathUtils.rotate_around_origin(np.array([0, self.motor_radius * self.tighten]), math.pi/4)
        # dist = math.pi * .99
        # upper = lower.circle(self.motor_radius * self.tighten)

        # upper_rad = self.motor_radius * self.tighten
        # upper = lower.sketch().circle(upper_rad).circle(upper_rad- self.thickness, mode="s").finalize()
        # bridge = upper.loft(ruled=True)

        parallel = (
            cq.Workplane("XY")
            .sketch()
            .circle(base_radius)
            .circle(self.motor_radius * self.tighten, mode="s")
            .finalize()
            .extrude(self.motor_length)
        )

        # scene = scene.add(base).add(around).add(fill).add(bridge).add(parallel)
        scene = scene.union(base).union(around).union(fill).union(parallel)
        scene.name = "fan_motor_holder"

        return scene

    def build_for_print(self):
        built = self.build()
        built = built.rotate((0, 0, 0), (0, 1, 0), 180)
        return super().build_for_print(built)


class FanCompartmentBuilder(PartBuilder):
    def __init__(
        self,
        fan_hull_radius,
        fan_hull_length,
        thickness,
        outward_overhang,
        hotfix_length=False,
    ):
        self.fan_hull_radius = fan_hull_radius + thickness * 2
        self.fan_hull_length = fan_hull_length
        self.thickness = thickness
        self.outward_overhang = outward_overhang
        self.hotfix_length = hotfix_length

    def get_around_base(self, cap=False):
        def rev(x, y=None, z=None):
            if type(x) == tuple:
                return rev(*x)
            if z is not None:
                return (x, y, z)
            return (x, y)

        cap_add = 0 if not cap else self.thickness * 2.0

        if self.hotfix_length:
            self.thickness /= 2
        around = (
            cq.Workplane("XY")
            .sketch()
            .circle(self.fan_hull_radius)
            .circle(self.fan_hull_radius - self.thickness, mode="s", tag="inner")
            .reset()
            .push([rev(self.fan_hull_radius / 2, self.fan_hull_radius / 2, 0)])
            .rect(*rev(self.fan_hull_radius, self.fan_hull_radius + cap_add), mode="s")
            .reset()
            .push(
                [
                    rev(
                        self.fan_hull_radius / 2 + self.outward_overhang / 2,
                        self.fan_hull_radius / 2,
                        0,
                    )
                ]
            )
            .rect(
                *rev(self.fan_hull_radius + self.outward_overhang, self.fan_hull_radius)
            )
            .reset()
            .push(
                [
                    rev(
                        self.fan_hull_radius / 2 + self.outward_overhang / 2,
                        self.fan_hull_radius / 2 - self.thickness / 2,
                        0,
                    )
                ]
            )
            .rect(
                *rev(
                    self.fan_hull_radius + self.outward_overhang,
                    self.fan_hull_radius - self.thickness,
                ),
                mode="s",
            )
        )
        if not cap:
            around = (
                around.reset()
                .push(
                    [
                        rev(
                            self.fan_hull_radius
                            + self.outward_overhang / 2
                            - self.thickness / 4,
                            -self.thickness / 2,
                            0,
                        )
                    ]
                )
                .rect(*rev(self.outward_overhang + self.thickness / 2, self.thickness))
            )
        around = around.finalize()
        base = (
            cq.Workplane("XY")
            .sketch()
            .push(
                [
                    rev(
                        self.fan_hull_radius / 2 + self.outward_overhang / 2,
                        self.fan_hull_radius / 2,
                        0,
                    )
                ]
            )
            .rect(
                *rev(self.fan_hull_radius + self.outward_overhang, self.fan_hull_radius)
            )
            .reset()
            .push([(0, 0, 0)])
            .circle(self.fan_hull_radius - self.thickness, mode="s", tag="inner")
            .finalize()
        )
        if self.hotfix_length:
            self.thickness *= 2
        return around, base

    def build_with_sketch(self):
        scene = cq.Workplane("XY")
        around, base = self.get_around_base()

        addition = 0 if not self.hotfix_length else 3.5 * self.thickness
        fc = (around.extrude(self.fan_hull_length + addition)).union(
            base.extrude(self.thickness)
        )
        return fc

    def build(self):
        # result = (
        #     cq.Workplane("XY")
        #     .threePointArc((1.0, 1.5), (0.0, 1.0))
        #     .extrude(0.25)
        # )
        # cyl = cq.Workplane("XY").cylinder(height=self.fan_hull_length, radius=self.fan_hull_radius)
        # cyl = cyl.faces(">Z").workplane().hole(diameter=(self.fan_hull_radius - self.thickness) * 2)
        # return result
        result = self.build_with_sketch()
        result.name = "fan_compartment_builder"
        return result

    def build_for_print(self):
        built = self.build()
        built = built.rotate((0, 0, 0), (0, 1, 0), 180)
        return super().build_for_print(built)


class CentrifugeBuilder(PartBuilder):
    def __init__(
        self,
        fcb: FanCompartmentBuilder,
        inside_slack,
        inner_ring_radius,
        blade_angle,
        fan_length_offset=0,
        top_height=None,
        holder_thickness=None,
    ) -> None:
        super().__init__()
        self.fcb: FanCompartmentBuilder = fcb
        self.inside_slack = inside_slack
        self.inner_ring_radius = inner_ring_radius
        self.fan_radius = (
            self.fcb.fan_hull_radius - self.fcb.thickness - self.inside_slack
        )
        self.blade_angle = blade_angle

        self.blade_midpoint_deviation_radius_ratio = 1 / 3.2
        self.blade_follower_midpoint_deviation_radius_ratio = 1 / 2.3

        self.num_blades = 8

        self.base_height = self.fcb.thickness / 2

        self.fan_length_offset = fan_length_offset

        self.top_height = top_height

        if self.top_height is None:
            self.top_height = self.fcb.thickness / 2

        self.fan_height = (
            fcb.fan_hull_length
            - 5 * self.fcb.thickness
            - self.base_height * 2
            + self.top_height
            + self.fan_length_offset
        )

        self.holder_thickness = holder_thickness

    def build(self):
        result = self.build_fan_and_bottom().union(self.build_top())
        result.name = "centrifuge_builder"
        return result

    def build_for_print(self):
        return

    def build_top(self):
        scene = cq.Workplane("XY")
        scene = scene.add(
            cq.Workplane("XY")
            .sketch()
            .circle(self.fan_radius)
            .finalize()
            .extrude(self.top_height)
            .translate((0, 0, self.fan_height))
        )
        if self.holder_thickness is None:
            self.holder_thickness = self.fcb.thickness * 2

        scene.add(
            Z1MotorJoint.no_screw(self.holder_thickness, 6)
            .build()
            .translate((0, 0, self.fan_height))
        )
        return scene

    def build_fan_and_bottom(self):
        initial_start = blade_end = np.array([0, self.fan_radius])
        # print(f"{blade_end=}, {self.blade_angle=}")
        blade_end = MathUtils.rotate_around_origin(blade_end, self.blade_angle)
        # print(f"{blade_end=}, {self.blade_angle=}")
        # print("")

        blade_perpendacular = MathUtils.rotate_around_origin(blade_end, math.pi / 2)
        blade_perpendacular /= np.linalg.norm(blade_perpendacular)

        blade_midpoint = blade_end / 2

        left_arc_midpoint = (
            blade_midpoint
            - blade_perpendacular
            * self.fan_radius
            * self.blade_midpoint_deviation_radius_ratio
        )
        right_arc_midpoint = (
            blade_midpoint
            - blade_perpendacular
            * self.fan_radius
            * self.blade_follower_midpoint_deviation_radius_ratio
        )

        left_start = (
            initial_start / np.linalg.norm(initial_start) * self.inner_ring_radius
        )
        # right_start = right_arc_midpoint/np.linalg.norm(right_arc_midpoint) * self.inner_ring_radius
        right_start = left_start

        blade = (
            cq.Workplane("XY")
            .moveTo(left_start[0], left_start[1])
            .threePointArc(left_arc_midpoint, blade_end, forConstruction=False)
            .moveTo(blade_end[0], blade_end[1])
            .threePointArc(right_arc_midpoint, right_start, forConstruction=False)
            .close()
            .moveTo(0, 0)
            # .circle(self.inner_ring_radius)
            .extrude(self.fan_height)
        )

        scene = cq.Workplane("XY")

        for i in range(self.num_blades):
            scene = scene.add(
                blade.rotate((0, 0, 0), (0, 0, 1), i * 360 / self.num_blades)
            )

        scene = scene.union(
            cq.Workplane("XY")
            .sketch()
            .circle(self.fan_radius)
            .circle(self.inner_ring_radius, mode="s", tag="inner")
            .finalize()
            .extrude(self.base_height)
        )

        return scene


class ConnectorBuilder(PartBuilder):
    pass


class JointBuilder(PartBuilder):
    def __init__(
        self,
        diameter,
        thickness,
        num_screws,
        screw_inner,
        nut_side,
        is_socket,
        decrease_ratio: float,
        from_outside,
    ) -> None:
        super().__init__()
        self.diameter = diameter
        self.thickness = thickness
        self.num_screws = num_screws
        self.screw_inner = screw_inner
        self.nut_side = nut_side
        self.screw_step_height = self.thickness / 2
        self.is_socket = is_socket
        self.decrease_ratio = decrease_ratio
        self.from_outside = from_outside

        self.screw_center = np.array(
            [0, self.diameter - self.from_outside],
            dtype=np.float32,
        )
        # self.decrease = self.screw_outer * (self.decrease_ratio if not self.is_socket else 0)

    @classmethod
    def m3_5(cls):
        return cls(
            10,
            2.1,
            3,
            3 / 2,
            6.5 / 2,
            issubclass(cls, JointBuilder),
            decrease_ratio=0.05,
            from_outside=4,
        )

    def build_base(self):
        base = cq.Workplane("XY").sketch().circle(self.diameter)

        screw_center = self.screw_center.copy()
        for i in range(self.num_screws):
            base = base.reset()
            base = base.push([(screw_center[0], screw_center[1], 0.0)])
            # print(self, self.screw_outer, self.screw_outer - self.decrease)
            base = base.regularPolygon(self.nut_side, 6, mode="s")
            screw_center = MathUtils.rotate_around_origin(
                screw_center, math.pi * 2 / self.num_screws
            )
        base = self.on_finish(base)

        return base.finalize().extrude(self.thickness)

    def on_finish(self, base):
        return base

    def build_connections(self):
        base = cq.Workplane("XY").sketch()

        screw_center = self.screw_center.copy()
        for i in range(self.num_screws):
            base = base.reset()
            base = base.push([(screw_center[0], screw_center[1], 0.0)])
            base = base.regularPolygon(self.nut_side, 6, mode="a")
            screw_center = MathUtils.rotate_around_origin(
                screw_center, math.pi * 2 / self.num_screws
            )

        screw_center = self.screw_center.copy()
        for i in range(self.num_screws):
            base = base.reset()
            base = base.push([(screw_center[0], screw_center[1], 0.0)])
            base = base.circle(self.screw_inner, mode="s")
            screw_center = MathUtils.rotate_around_origin(
                screw_center, math.pi * 2 / self.num_screws
            )

        sgn = -1  # if self.is_socket else 1
        base = base.finalize().extrude(self.thickness + sgn * self.thickness / 2.3)
        return base

    def build(self):
        scene = cq.Workplane("XY")

        scene = scene.add(self.build_base())
        if self.num_screws:
            scene.add(self.build_connections())

        return scene


class Z1MotorJoint(JointBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def no_screw(cls, radius, motor_length=6):
        return cls(
            radius,
            motor_length,
            0,
            3 / 2,
            6.5 / 2,
            issubclass(cls, JointBuilder),
            decrease_ratio=0.05,
            from_outside=4,
        )

    def on_finish(self, base):
        base = base.reset()
        base = base.push([(0, 0, 0.0)])
        base = base.circle(0.65, mode="s")
        return base


class FanBuilder(PartBuilder):
    def __init__(
        self,
        phb: PenHolderBuilder,
        fcb: FanCompartmentBuilder,
        cb: ConnectorBuilder,
        cent_b: CentrifugeBuilder,
        fmh: FanMotorHolder,
    ) -> None:
        self.phb = phb
        self.fcb = fcb
        self.cb = cb
        self.cent_b = cent_b
        self.fmh = fmh

    def get_part_builders(self):
        for attr in dir(self):
            if isinstance(getattr(self, attr), PartBuilder):
                yield getattr(self, attr)

    def add_to_top(self, obj, scene, translate_amount=None):
        if translate_amount is None:
            try:
                zlen = scene.findSolid().BoundingBox().zlen
                zmax = scene.findSolid().BoundingBox().zmax
            except:
                zmax = 0
                zlen = 0
            try:
                obj_bb = obj.val().BoundingBox()
            except:
                obj_bb = obj.BoundingBox()

            translate_amount = zmax - obj_bb.zmin

        scene = scene.add(obj.translate((0, 0, translate_amount)))
        return scene, translate_amount

    def build(self):
        scene = cq.Workplane("XY")

        self.add_to_top(self.phb.build(), scene)
        self.add_to_top(self.cb.build(), scene)
        _, fcb_trans = self.add_to_top(self.fcb.build(), scene)

        self.add_to_top(self.cent_b.build(), scene, fcb_trans)
        self.add_to_top(self.fmh.build(), scene)

        return scene

    def build_for_print(self):
        parts = []

        component_builders = [self.phb, self.cb, self.fcb, self.cent_b]
        for builder in component_builders:
            for part in builder.build_for_print()[1]:
                parts.append(part)

        full_scene = cq.Workplane("XY")
        for part in parts:
            full_scene = self.add_to_side(part, full_scene)[0]

        return full_scene, parts


class TestFanBuilder(FanBuilder):
    def build_for_print(self, only_build=None):
        if only_build is not None:
            if isinstance(only_build, str):
                only_build = [only_build]

            parts = []
            for attr in only_build:
                parts.append(getattr(self, attr).build())
            full_scene = cq.Workplane("XY")
            for part in parts:
                full_scene, _ = self.add_to_top(part, full_scene)
            return full_scene, parts
        print("not inside")

        parts = []

        bottom_part = cq.Workplane("XY")
        for builder in [
            self.phb,
            self.cb,
        ]:
            self.add_to_top(builder.build(), bottom_part)

        bottom_part = bottom_part.rotate((0, 0, 0), (0, 1, 0), 180)

        component_builders = [
            # CylindricalHolderBuilder(PM.OUTER_RADIUS/2, Z1.DIAMETER/2, PM.THICKNESS * 3, 130),
            self.fcb,
            # self.fmh,
            # self.phb,
            self.cb,
            self.phb,
            # Z1MotorJoint.m3_5(),
            # JointBuilder.m3_5(),
        ]
        ##
        # parts.append(bottom_part)
        for builder in component_builders:
            for part in builder.build_for_print()[1]:
                parts.append(part)

        full_scene = cq.Workplane("XY")
        for part in parts:
            # full_scene.add(part)
            full_scene = self.add_to_top(part, full_scene)[0]

        hull = full_scene.rotate((0, 0, 0), (0, 1, 0), 180)

        full_scene = cq.Workplane("XY")

        full_scene = self.add_to_top(self.cent_b.build(), full_scene)[0]
        full_scene, zz = self.add_to_top(self.fmh.build(), full_scene)
        full_scene = self.add_to_top(hull, full_scene, zz)[0]

        parts = [hull]
        parts.append(self.fmh.build_for_print()[0])
        # parts.append(self.cent_b.build().rotate((0, 0, 0), (0, 1, 0), 180))
        parts.append(self.cent_b.build())

        # # parallels:
        # full_scene = cq.Workplane("XY")
        # parts = []
        # parallels = [ParallelBuilder(Z1.LENGTH, Z1.DIAMETER/2, 0.98 + i/100) for i in range(10)]
        # for p in parallels:
        #     part = p.build()
        #     full_scene = self.add_to_side(part, full_scene, extra = 2)[0]
        #     parts.append(part)

        # # ... end

        print("done build for print: ", len(parts), parts, full_scene)
        return full_scene, parts


class SplineConnectorBuilder(ConnectorBuilder):
    def __init__(
        self, phb: PenHolderBuilder, fcb: FanCompartmentBuilder, connector_length
    ) -> None:
        super().__init__()
        self.connector_length = connector_length
        self.phb = phb
        self.fcb = fcb

    def build(self):
        points = []
        points.append((0, 0))
        points.append((1, -0.25))
        points.append((2, -1))
        points.append((3, -1.75))
        points.append((4, -2))
        points = [(x, z) for z, x in points]

        points = np.array(points)
        points[:, 1] /= 4
        points[:, 0] /= -2

        points[:, 1] *= self.connector_length
        points[:, 0] *= (
            self.fcb.fan_hull_radius - self.phb.pen_radius - self.fcb.thickness
        )

        points[:, 0] += self.phb.pen_radius

        path = cq.Workplane("XZ").spline(points)
        face = (
            cq.Workplane("XY")
            .moveTo(self.phb.pen_radius + self.phb.thickness / 2)
            .rect(self.phb.thickness, 2e-3)
            .sweep(path)
            .translate((0, 1e-3, 0))
            .faces("<Y")
        )

        scene = cq.Workplane("XZ")

        half = (
            face.first()
            .wires()
            .toPending()
            .revolve(180, axisStart=(0, 0, 0), axisEnd=(0, 0, 1))
            .rotate(axisStartPoint=(0, 0, 0), axisEndPoint=(0, 0, 1), angleDegrees=180)
        )
        other_half = (
            face.first()
            .wires()
            .toPending()
            .revolve(180, axisStart=(0, 0, 0), axisEnd=(0, 0, 1))
            .rotate(axisStartPoint=(0, 0, 0), axisEndPoint=(0, 0, 1), angleDegrees=0)
        )

        return half.union(other_half)

        # # p = scene.spline(points, forConstruction=True).toPending().wire().toPending()
        # p = scene.lineTo(points[0][0], points[0][1])
        # p = cq.Workplane("XZ").polyline(points)
        # # obj = p.copyWorkplane(cq.Workplane("YZ")).extrude(-self.phb.thickness)
        # obj = cq.Workplane("XY").circle(2.0).extrude(0.5).sweep(p)
        # # obj = scene.copyWorkplane(cq.Workplane("XY")).circle(self.phb.thickness).toPending().extrude(-self.connector_length)

        # print(obj.loft())
        # def debug_print_faces(obj):
        #     for i, face in enumerate(obj.faces().vals()):
        #         bb = face.BoundingBox()
        #         print(f"Face {i}:")
        #         print(f"  - Area: {face.Area()}")
        #         print(f"  - Center: {bb.center}")
        #         print(f"  - Lengths: (x: {bb.xlen}, y: {bb.ylen}, z: {bb.zlen})")
        #         print(f"  - Bounds: {bb}")

        # debug_print_faces(obj)

        # obj = obj.faces(">Y").workplane()

        return scene

    def build_for_print(self):
        built = self.build()
        built = built.rotate((0, 0, 0), (0, 1, 0), 180)
        return built, [built]


class CylindricalHolderBuilder(PartBuilder):
    def __init__(self, bottom_radius, top_radius, thickness, length):
        self.bottom_radius = bottom_radius
        self.top_radius = top_radius
        self.thickness = thickness
        self.length = length
        self.deviation_ratio = 1 / 1.5
        self.length = self.thickness * 4
        self.inner_ratio = 0.85

    def add_handle(self, scene, bottom, top):
        md = (bottom + top) / 2
        md[0] += self.deviation_ratio * self.length
        scene = scene.add(
            cq.Workplane("YZ")
            .moveTo(bottom[0], bottom[1])
            .threePointArc((md[0], md[1]), (top[0], top[1]))
            .moveTo(top[0], top[1])
            .lineTo(top[0] * (1 + self.inner_ratio) / 2, top[1])
            # .threePointArc((top[0], top[1]), (top[0], top[1]))
            .close()
            # .reset()
            # .circle(rad)
            # .circle(rad * 0.85, mode="s")
            # .reset()
            # .push([(rad/1.1, 0, 0)])
            # .rect(rad/2, rad, mode="s")
            .extrude(self.thickness)
            .translate((-self.thickness / 2, 0, -self.thickness / 2))
        )
        return scene

    def build(self):
        scene = cq.Workplane("XY")

        rad = self.bottom_radius
        scene = scene.add(
            cq.Workplane("XY")
            .sketch()
            .reset()
            .circle(rad)
            .circle(rad * self.inner_ratio, mode="s")
            .reset()
            .push([(rad / 1.1, 0, 0)])
            .rect(rad / 2, rad, mode="s")
            .finalize()
            .extrude(self.thickness)
            .translate((0, 0, -self.thickness / 2))
        )

        rad = self.top_radius
        scene = scene.add(
            cq.Workplane("XY")
            .sketch()
            .circle(rad)
            .circle(rad * self.inner_ratio, mode="s")
            .reset()
            .push([(rad / 1.1, 0, 0)])
            .rect(rad / 2, rad, mode="s")
            .finalize()
            .extrude(self.thickness)
            .translate((0, 0, self.length))
            .translate((0, 0, -self.thickness / 2))
        )

        scene = self.add_handle(
            scene,
            np.array([self.bottom_radius, self.thickness / 2]),
            np.array([self.top_radius, self.length + self.thickness / 2]),
        )

        # scene.add(
        #     cq.Workplane("YZ")
        #     .moveTo(self.bottom_radius * 0.9, 0)
        #     .threePointArc((self.length * (self.deviation_ratio), self.length / 2), (self.top_radius * 0.9, self.length))
        #     .moveTo(self.top_radius * 0.9, self.length)
        #     # .lineTo(self.top_radius * 0.9, self.length)
        #     .threePointArc((self.length * (self.deviation_ratio), self.length / 2), (self.bottom_radius* 0.9, 0))
        #     .close()
        #     .extrude(self.thickness)
        # )

        return scene
