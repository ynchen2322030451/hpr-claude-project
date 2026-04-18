#!/usr/bin/env python3
"""
Parametric CAD model of the MegaPower-class micro-reactor core using
**CadQuery** — pure Python CAD. All geometry comes from the same
constants as draw_core_geometry.py so the illustration and the CAD
model are one source of truth.

Running this file (`python core_geometry_cadquery.py`) will:
    * build the reactor solid as a proper B-Rep model,
    * save it as STEP   (core_geometry.step)     — the CAD exchange format
    * save it as STL    (core_geometry.stl)      — a mesh for 3-D printing
    * save it as SVG    (core_geometry_view.svg) — a technical projection
    * save it as DXF    (core_geometry_top.dxf)  — the top cross-section

CadQuery ships in Conda (`conda install -c conda-forge cadquery`) or on
pip (`pip install cadquery`).  It wraps the OCCT CAD kernel, so the
STEP / STL it writes are full-fidelity CAD (not a triangle soup).

If CadQuery isn't installed the script prints a clear message and
exits — no import errors.
"""

import math
import sys
from pathlib import Path

try:
    import cadquery as cq
except Exception as exc:               # noqa: BLE001
    sys.exit(
        "CadQuery is not installed in this environment.\n"
        "Install it once with:\n"
        "    conda install -c conda-forge cadquery\n"
        "    # or\n"
        "    pip install cadquery\n"
        f"(Import error: {exc})"
    )

OUT = Path(__file__).parent

# -----------------------------------------------------------------
# Radial geometry (cm) — same constants as draw_core_geometry.py
# -----------------------------------------------------------------
WALL_1    = 8.84          # inner hex half-apothem (control-rod channel)
WALL_2    = 29.625        # outer hex half-apothem (monolith fuel slab)
R_REFL    = 55.625        # outer reflector radius / vessel radius
DRUM_CR   = (WALL_2 + R_REFL) / 2
DRUM_R    = (R_REFL - WALL_2) / 2 - 0.4
N_DRUMS   = 6

# Axial zones (z grows upward)
H_BASE    = 4.0
H_PINK    = 4.0
H_ABS     = 4.0
H_FUEL    = 116.5
H_MONO    = 3.5
H_TOTAL   = H_BASE + H_PINK + H_ABS + H_FUEL + H_MONO            # 132 cm

Z_BASE    = 0.0
Z_PINK    = Z_BASE + H_BASE
Z_ABS     = Z_PINK + H_PINK
Z_FUEL    = Z_ABS  + H_ABS
Z_MONOT   = Z_FUEL + H_FUEL                                      # top of slab
Z_TOP     = Z_MONOT + H_MONO                                     # 132 cm

# Wedge cut — 60° centred on +X (deg)
CUT_CENTER = 215
CUT_DELTA  = 60
CUT_A      = CUT_CENTER - CUT_DELTA / 2                         # 185°
CUT_B      = CUT_CENTER + CUT_DELTA / 2                         # 245°


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------
def hex_polygon(apothem: float):
    """List of (x, y) vertices of the regular hexagon centred at origin
    with flats at ±apothem, first vertex at angle 30°."""
    R = apothem * 2.0 / math.sqrt(3)
    return [(R * math.cos(math.radians(30 + 60 * k)),
             R * math.sin(math.radians(30 + 60 * k))) for k in range(6)]


def wedge_cut(model, angle_start_deg=CUT_A, angle_end_deg=CUT_B,
              radius=R_REFL * 1.1, z0=-1.0, h=H_TOTAL + 2.0):
    """Subtract a pie-wedge from model. Wedge extends from the z-axis
    outward in the angular range [angle_start_deg, angle_end_deg]."""
    pts = [(0, 0)]
    n = 24
    for i in range(n + 1):
        a = math.radians(angle_start_deg + (angle_end_deg - angle_start_deg) * i / n)
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    tool = (cq.Workplane("XY")
              .polyline(pts).close()
              .extrude(h)
              .translate((0, 0, z0)))
    return model.cut(tool)


def hex_prism(apothem: float, h: float, z0: float = 0.0):
    return (cq.Workplane("XY")
              .polyline(hex_polygon(apothem)).close()
              .extrude(h)
              .translate((0, 0, z0)))


# -----------------------------------------------------------------
# Build the axial layers as separate solids then combine / tag.
# Using separate Workplanes so each zone can carry its own "name"
# for nicer STEP import into downstream CAD tools.
# -----------------------------------------------------------------
def core_assembly(with_wedge_cut: bool = True, wedge_only: bool = False):
    """Returns a cq.Assembly of the core.
    with_wedge_cut=True and wedge_only=False → 5/6 piece (main panel).
    wedge_only=True                          → 1/6 wedge piece alone."""

    asm = cq.Assembly(name="MegaPowerCore")

    # ---- Helpers to add an annular slab
    def tube(r_in, r_out, h, z0):
        return (cq.Workplane("XY")
                  .circle(r_out).circle(r_in)
                  .extrude(h)
                  .translate((0, 0, z0)))

    def cyl(r, h, z0):
        return cq.Workplane("XY").circle(r).extrude(h).translate((0, 0, z0))

    # ---- Bottom three bands (full disc, all zones)
    base = cyl(R_REFL, H_BASE, Z_BASE)
    pink = cyl(R_REFL, H_PINK, Z_PINK)
    absorber = cyl(R_REFL, H_ABS, Z_ABS)

    # ---- Fuel zone: reflector annulus (gold) + monolith slab (salmon)
    #      + inner channel (pale pink)
    refl = tube(WALL_2, R_REFL, H_FUEL, Z_FUEL)
    # Carve 6 drum bores into the reflector and fill with "drum" solids
    drums = cq.Workplane("XY")
    for k in range(N_DRUMS):
        a = math.radians(60 * k)
        drums = drums.union(
            cq.Workplane("XY")
              .center(DRUM_CR * math.cos(a), DRUM_CR * math.sin(a))
              .circle(DRUM_R)
              .extrude(H_FUEL)
              .translate((0, 0, Z_FUEL))
        )
    refl = refl.cut(drums)

    outer_hex = hex_prism(WALL_2, H_FUEL, Z_FUEL)
    inner_hex = hex_prism(WALL_1, H_FUEL, Z_FUEL)
    monolith = outer_hex.cut(inner_hex)
    channel  = inner_hex

    # ---- Top monolith cap (gold over reflector + monolith, channel stays)
    top_disc = cyl(R_REFL, H_MONO, Z_MONOT)
    top_cap  = top_disc.cut(hex_prism(WALL_1, H_MONO, Z_MONOT))
    top_chan = hex_prism(WALL_1, H_MONO, Z_MONOT)

    # ---- Optional wedge cut on every piece
    def maybe_cut(solid):
        if wedge_only:
            # Keep only the wedge — complement cut
            return solid.cut(_complement_wedge(solid))
        if with_wedge_cut:
            return wedge_cut(solid)
        return solid

    def _complement_wedge(solid):
        # Everything EXCEPT the 60° wedge
        pts = [(0, 0)]
        n = 120
        start = CUT_B
        end = CUT_B + (360 - CUT_DELTA)
        for i in range(n + 1):
            a = math.radians(start + (end - start) * i / n)
            pts.append((R_REFL * 1.1 * math.cos(a), R_REFL * 1.1 * math.sin(a)))
        tool = (cq.Workplane("XY").polyline(pts).close()
                  .extrude(H_TOTAL + 2).translate((0, 0, -1)))
        return tool

    # ---- Assemble
    asm.add(maybe_cut(base),     name="base_band",
            color=cq.Color(248/255, 238/255, 225/255))
    asm.add(maybe_cut(pink),     name="pink_band",
            color=cq.Color(252/255, 220/255, 220/255))
    asm.add(maybe_cut(absorber), name="absorber_band",
            color=cq.Color( 85/255, 200/255,  85/255))
    asm.add(maybe_cut(refl),     name="reflector",
            color=cq.Color(218/255, 165/255,  32/255))
    asm.add(maybe_cut(monolith), name="monolith_fuel_slab",
            color=cq.Color(220/255, 130/255, 120/255))
    asm.add(maybe_cut(channel),  name="control_rod_channel",
            color=cq.Color(250/255, 210/255, 210/255))
    asm.add(maybe_cut(top_cap),  name="monolith_cap",
            color=cq.Color(218/255, 165/255,  32/255))
    asm.add(maybe_cut(top_chan), name="channel_cap",
            color=cq.Color(250/255, 210/255, 210/255))
    # Drums (only in the main-body case)
    if not wedge_only:
        for k in range(N_DRUMS):
            a = math.radians(60 * k)
            drum_body = (cq.Workplane("XY")
                           .center(DRUM_CR * math.cos(a), DRUM_CR * math.sin(a))
                           .circle(DRUM_R - 0.05)
                           .extrude(H_FUEL)
                           .translate((0, 0, Z_FUEL)))
            drum_body = maybe_cut(drum_body)
            asm.add(drum_body, name=f"control_drum_{k}",
                    color=cq.Color(235/255, 190/255, 55/255))
    return asm


# -----------------------------------------------------------------
# Build and export
# -----------------------------------------------------------------
def main():
    print("Building 5/6 main body …")
    main_body = core_assembly(with_wedge_cut=True, wedge_only=False)
    main_body.save(str(OUT / "core_geometry_main.step"))
    cq.exporters.export(main_body.toCompound(),
                        str(OUT / "core_geometry_main.stl"))

    print("Building 1/6 wedge piece …")
    wedge = core_assembly(with_wedge_cut=False, wedge_only=True)
    wedge.save(str(OUT / "core_geometry_wedge.step"))
    cq.exporters.export(wedge.toCompound(),
                        str(OUT / "core_geometry_wedge.stl"))

    # A technical SVG projection of the main body
    print("Writing SVG projection …")
    cq.exporters.export(
        main_body.toCompound(),
        str(OUT / "core_geometry_view.svg"),
        opt={
            "width":  900,
            "height": 900,
            "marginLeft":  10,
            "marginTop":   10,
            "showAxes":    True,
            "projectionDir": (1, -1, 0.8),  # iso-ish
            "strokeWidth": 0.5,
            "strokeColor": (0, 0, 0),
            "hiddenColor": (160, 160, 160),
            "showHidden":  False,
        }
    )

    # DXF of the top cross-section plane
    print("Writing DXF of top cross-section …")
    top_section = (cq.Workplane("XY")
                     .add(main_body.toCompound())
                     .section())
    cq.exporters.export(top_section.val(),
                        str(OUT / "core_geometry_top.dxf"))

    print("Done. Outputs:")
    for f in sorted(OUT.glob("core_geometry_*")):
        print("  ", f.name)


if __name__ == "__main__":
    main()
