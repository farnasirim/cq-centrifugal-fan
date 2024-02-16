import os
import numpy as np
import cadquery as cq
import math

import cq_centrifugal_fan.debug as cf_debug
import cq_centrifugal_fan.shapes as cf_shapes


class PenMeasurements:
    OUTER_RADIUS = np.median([7.10, 7.10, 7.06, 7.12, 7.11])
    THICKNESS = np.median([0.85, 0.89, 0.93])


class Z1MotorMeasurements:
    DIAMETER = 8.06
    LENGTH = 16.0


def main():
    PM = PenMeasurements
    Z1 = Z1MotorMeasurements

    phb = cf_shapes.PenHolderBuilder(
        PM.THICKNESS * 2, PM.OUTER_RADIUS / 2, PM.OUTER_RADIUS * 3 / 4
    )
    fcb = cf_shapes.FanCompartmentBuilder(
        PM.OUTER_RADIUS * 1.2 - phb.thickness,
        PM.OUTER_RADIUS * 3,
        phb.thickness,
        phb.pen_radius * 3 / 4,
    )
    fmh = cf_shapes.FanMotorHolder(fcb, Z1.DIAMETER / 2, Z1.LENGTH)
    cb = cf_shapes.SplineConnectorBuilder(phb, fcb, PM.OUTER_RADIUS * 1)

    cent_b = cf_shapes.CentrifugeBuilder(
        fcb,
        phb.thickness * 1.2,
        PM.OUTER_RADIUS / 2,
        math.pi / 3.5,
        fan_length_offset=fcb.thickness * 3,
        holder_thickness=Z1.DIAMETER / 2 * 0.7,
    )

    cf_debug.monitor.show_object(phb.build().translate((0, 0, 0)), clear=True)
    cf_debug.monitor.show_object(cb.build().translate((0, 0, 20)))
    cf_debug.monitor.show_object(fcb.build().translate((0, 0, 40)))
    cf_debug.monitor.show_object(cent_b.build().translate((0, 0, 70)))
    cf_debug.monitor.show_object(fmh.build().translate((0, 0, 100)))


if __name__ == "__main__":
    main()
