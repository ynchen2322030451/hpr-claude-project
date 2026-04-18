// ============================================================
//  MegaPower-class micro-reactor core — parametric CAD model
//  Matches the geometry constants in draw_core_geometry.py so
//  the 3D figure and the CAD part share one source of truth.
//
//  Render with OpenSCAD (free):    openscad core_geometry.scad
//  Export STL :  File → Export → Export as STL
//  Export STEP:  use the "experimental" CGAL-STEP pipeline, or
//                import the STL into FreeCAD and save as STEP.
//
//  All lengths are in cm (same units as the Python script).
// ============================================================

// -----------------------------------------------------------
// Resolution
// -----------------------------------------------------------
$fa = 1;   // min face angle
$fs = 0.6; // min face size (cm)
$fn = 96;  // default circle facets (overridable per-object)

// -----------------------------------------------------------
// Radial geometry (same as Python)
// -----------------------------------------------------------
WALL_1      = 8.84;       // inner hex half-apothem (control-rod channel)
WALL_2      = 29.625;     // outer hex half-apothem (monolith fuel slab)
R_REFL      = 55.625;     // outer reflector radius (vessel radius)
HP_D        = 1.575;      // heat-pipe diameter
FUEL_DO     = 1.425;      // fuel-rod diameter
P_FUEL      = 1.6;        // fuel-rod pitch
P_HP        = 1.6 * sqrt(3);  // heat-pipe pitch

DRUM_CR     = (WALL_2 + R_REFL) / 2;          // drum centre radius
DRUM_R      = (R_REFL - WALL_2) / 2 - 0.4;    // drum radius
DRUM_COUNT  = 6;
B4C_FRAC    = 0.22;                           // absorber arc thickness frac

// -----------------------------------------------------------
// Axial zones (z grows downward in Python; here use +Z up)
// Hence we negate: Z_TOP = 132, Z_BOT = 0.
// -----------------------------------------------------------
H_BASE      = 4.0;    // off-white base band
H_PINK      = 4.0;    // pink band
H_ABS       = 4.0;    // absorber band
H_FUEL      = 116.5;  // salmon fuel slab
H_MONO_CAP  = 3.5;    // gold upper monolith cap
H_TOTAL     = H_BASE + H_PINK + H_ABS + H_FUEL + H_MONO_CAP;   // 132

Z_BASE_BOT  = 0;
Z_PINK_BOT  = Z_BASE_BOT + H_BASE;
Z_ABS_BOT   = Z_PINK_BOT + H_PINK;
Z_FUEL_BOT  = Z_ABS_BOT  + H_ABS;
Z_FUEL_TOP  = Z_FUEL_BOT + H_FUEL;
Z_TOP       = Z_FUEL_TOP + H_MONO_CAP;     // = H_TOTAL

// -----------------------------------------------------------
// Wedge-cut parameters
// -----------------------------------------------------------
CUT_CENTER  = 0;     // wedge centre angle, degrees (0 = +X axis)
CUT_DELTA   = 60;    // wedge included angle, degrees

// -----------------------------------------------------------
// Build switches (tweak here to get different renders)
// -----------------------------------------------------------
BUILD_MAIN_BODY   = true;   // 5/6 cylinder (wedge removed) — "LEFT panel"
BUILD_WEDGE_PIECE = false;  // 60° wedge alone              — "RIGHT panel"
BUILD_DRUMS       = true;   // control drums inside reflector
BUILD_HEATPIPES   = false;  // heat-pipe rods (cosmetic, adds many facets)
BUILD_FUEL_RODS   = false;  // fuel rods (cosmetic)

// -----------------------------------------------------------
// Primitive helpers
// -----------------------------------------------------------

// Regular hex prism with apothem `a` (distance from centre to flat)
// centred at origin, axis = +Z.
module hex_prism(a, h) {
    r = a * 2 / sqrt(3);   // circumradius
    translate([0, 0, 0])
        linear_extrude(height = h)
            polygon([for (k = [0:5])
                      [r * cos(30 + 60*k), r * sin(30 + 60*k)]]);
}

// Wedge subtractor: a pie slice centred at CUT_CENTER, width CUT_DELTA,
// tall enough to slice any axial layer.
module wedge_cut(r_outer, h, z0) {
    pad = 2;
    translate([0, 0, z0 - pad])
        linear_extrude(height = h + 2*pad)
            polygon(concat(
                [[0, 0]],
                [for (k = [0 : 1 : 24])
                   let (t = CUT_CENTER - CUT_DELTA/2
                            + k * CUT_DELTA / 24)
                   [(r_outer + 1) * cos(t), (r_outer + 1) * sin(t)]]
            ));
}

// Annular slab between radii r1 and r2, height h starting at z = z0.
module tube_slab(r1, r2, h, z0) {
    translate([0, 0, z0])
        difference() {
            cylinder(h = h, r = r2);
            translate([0, 0, -0.01]) cylinder(h = h + 0.02, r = r1);
        }
}

// -----------------------------------------------------------
// Core solid: the un-cut reactor, built in axial zones.
// Each zone is tagged with a %color() so STL/STEP exports are
// clean per-zone — paint them in a CAD viewer if desired.
// -----------------------------------------------------------
module core_uncut() {
    // -- Base band (off-white)
    color([248/255, 238/255, 225/255])
        cylinder(h = H_BASE, r = R_REFL);

    // -- Pink band
    color([252/255, 220/255, 220/255])
        translate([0,0,Z_PINK_BOT])
            cylinder(h = H_PINK, r = R_REFL);

    // -- Absorber band (green)
    color([85/255, 200/255, 85/255])
        translate([0,0,Z_ABS_BOT])
            cylinder(h = H_ABS, r = R_REFL);

    // -- Main fuel zone (salmon slab inside monolith hex,
    //    pale-pink channel inside inner hex, gold reflector outside
    //    outer hex — everything between Z_FUEL_BOT and Z_FUEL_TOP).
    translate([0,0,Z_FUEL_BOT]) {
        // Reflector (gold) — annulus between outer hex and vessel wall
        color([218/255, 165/255, 32/255])
            difference() {
                cylinder(h = H_FUEL, r = R_REFL);
                hex_prism(WALL_2, H_FUEL + 0.01);
            }
        // Monolith fuel slab (salmon) — annulus between inner and outer hex
        color([220/255, 130/255, 120/255])
            difference() {
                hex_prism(WALL_2, H_FUEL);
                translate([0,0,-0.005])
                    hex_prism(WALL_1, H_FUEL + 0.01);
            }
        // Control-rod channel (pale pink) — inside inner hex
        color([250/255, 210/255, 210/255])
            hex_prism(WALL_1, H_FUEL);
    }

    // -- Upper monolith cap (gold)
    translate([0,0,Z_FUEL_TOP]) {
        // gold over full reflector + monolith
        color([218/255, 165/255, 32/255])
            difference() {
                cylinder(h = H_MONO_CAP, r = R_REFL);
                translate([0,0,-0.005])
                    hex_prism(WALL_1, H_MONO_CAP + 0.01);
            }
        color([250/255, 210/255, 210/255])
            hex_prism(WALL_1, H_MONO_CAP);
    }
}

// -----------------------------------------------------------
// Control drums — six cylinders embedded in the reflector ring.
// -----------------------------------------------------------
module drums() {
    for (k = [0 : DRUM_COUNT - 1]) {
        ang = 60 * k;
        translate([DRUM_CR * cos(ang), DRUM_CR * sin(ang), Z_FUEL_BOT]) {
            // Drum body (bright gold)
            color([235/255, 190/255, 55/255])
                cylinder(h = H_FUEL, r = DRUM_R);
            // B4C absorber crescent facing inward
            inward = ang + 180;
            rotate([0, 0, inward - 60])
                color([50/255, 205/255, 50/255])
                translate([0, 0, 0])
                    difference() {
                        cylinder(h = H_FUEL + 0.01, r = DRUM_R);
                        translate([0, 0, -0.005])
                            cylinder(h = H_FUEL + 0.02, r = DRUM_R * 0.78);
                        // keep only 120° arc
                        rotate([0, 0, 120])
                            translate([-DRUM_R*2, -DRUM_R*2, -0.01])
                                cube([DRUM_R*4, DRUM_R*4, H_FUEL + 0.03]);
                    }
        }
    }
}

// -----------------------------------------------------------
// Heat-pipe / fuel-rod lattices (optional — expensive).
// Positions are re-computed from the same recurrences used in the
// Python script, replicated 6× around the centre.
// -----------------------------------------------------------
function hp_one_sector() = [
    for (i = [4 : 12])
      for (j = [0 : i - 1])
        let (xs = [for (q = [0 : 40]) WALL_1 + HP_D/2 + q * P_FUEL*1.5],
             ys = [for (q = [0 : 40]) -P_HP*1.5 - q * P_HP/2])
        [ xs[i - 4], ys[i - 4] + j * P_HP ]
];

function fuel_one_sector_a() = [
    for (i = [3 : 10])
      for (j = [0 : i - 1])
        let (xs = [for (q = [0 : 40]) WALL_1 + HP_D/2 + P_FUEL/2
                                      + q * P_FUEL*1.5],
             ys = [for (q = [0 : 40]) -P_HP*1.5 + P_FUEL*sqrt(3)/2
                                      - q * P_FUEL*sqrt(3)/2])
        [ xs[i - 3], ys[i - 3] + j * P_HP ]
];

function fuel_one_sector_b() = [
    for (i = [4 : 11])
      for (j = [0 : i - 1])
        let (xs = [for (q = [0 : 40]) WALL_1 + P_FUEL/2 + HP_D/2
                                      + P_FUEL/2 + q * P_FUEL*1.5],
             ys = [for (q = [0 : 40]) -P_HP*1.5 - q * P_FUEL*sqrt(3)/2])
        [ xs[i - 4], ys[i - 4] + j * P_HP ]
];

module lattice(points, diameter, height, z0, col) {
    for (k = [0 : DRUM_COUNT - 1]) {
        rotate([0, 0, 60 * k])
            for (p = points)
                translate([p[0], p[1], z0])
                    color(col)
                        cylinder(h = height, r = diameter / 2);
    }
}

// -----------------------------------------------------------
// Top-level assembly
// -----------------------------------------------------------
module main_assembly() {
    core_uncut();
    if (BUILD_DRUMS)        drums();
    if (BUILD_HEATPIPES)    lattice(hp_one_sector(), HP_D, H_FUEL,
                                    Z_FUEL_BOT,
                                    [255/255, 215/255, 45/255]);
    if (BUILD_FUEL_RODS) {
        lattice(fuel_one_sector_a(), FUEL_DO, H_FUEL, Z_FUEL_BOT,
                [192/255, 57/255, 43/255]);
        lattice(fuel_one_sector_b(), FUEL_DO, H_FUEL, Z_FUEL_BOT,
                [192/255, 57/255, 43/255]);
    }
}

// -----------------------------------------------------------
// Drive the build
// -----------------------------------------------------------
if (BUILD_MAIN_BODY) {
    difference() {
        main_assembly();
        wedge_cut(R_REFL, H_TOTAL, 0);
    }
}

if (BUILD_WEDGE_PIECE) {
    intersection() {
        main_assembly();
        wedge_cut(R_REFL, H_TOTAL, 0);
    }
}
