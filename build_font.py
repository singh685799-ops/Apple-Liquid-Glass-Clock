#!/usr/bin/env python3
"""
Generates AppleLiquidGlassClock.ttf with complete, smooth, ultra-tall iOS Liquid Glass
numerals (0-9) and colon glyphs with verified TrueType contour winding.
"""
import math
import os
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from shapely.geometry import LineString, Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

# Core typography geometry constants (Units Per Em = 1000)
# Designed for tall lock-screen display: CapHeight = 880, Stroke = 58 (radius = 29)
R = 29.0
X_LEFT = 74.0
X_RIGHT = 286.0
X_MID = 180.0
Y_BOT = 29.0
Y_TOP = 851.0
RAD = 106.0  # (X_RIGHT - X_LEFT) / 2.0


def arc_pts(cx, cy, rx, ry, deg_start, deg_end, steps=48):
    """Generates smooth parametric elliptical arc coordinates."""
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        ang = math.radians(deg_start + (deg_end - deg_start) * t)
        pts.append((cx + rx * math.cos(ang), cy + ry * math.sin(ang)))
    return pts


def cubic_bezier(p0, p1, p2, p3, steps=48):
    """Evaluates a smooth cubic Bezier curve."""
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        mt = 1.0 - t
        x = (mt**3)*p0[0] + 3*(mt**2)*t*p1[0] + 3*mt*(t**2)*p2[0] + (t**3)*p3[0]
        y = (mt**3)*p0[1] + 3*(mt**2)*t*p1[1] + 3*mt*(t**2)*p2[1] + (t**3)*p3[1]
        pts.append((x, y))
    return pts


def stroke_lines(lines_list, radius=R):
    """Buffers centerline paths into a single manifold polygon with round glass terminals."""
    shapes = [
        LineString(pts).buffer(radius, cap_style=1, join_style=1, quad_segs=24)
        for pts in lines_list
    ]
    merged = unary_union(shapes)
    return merged.simplify(0.35, preserve_topology=True)


def poly_to_ttglyph(geom):
    """
    Converts a Shapely Polygon/MultiPolygon into a TrueType glyph.
    Enforces Clockwise (CW) outer contours and Counter-Clockwise (CCW) inner counters.
    """
    pen = TTGlyphPen(None)
    if geom is None or geom.is_empty:
        return pen.glyph()

    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)

    for poly in polys:
        # sign=-1.0 in Cartesian (x-right, y-up) orients exterior CW and interiors CCW
        oriented = orient(poly, sign=-1.0)

        for ring in [oriented.exterior] + list(oriented.interiors):
            raw_coords = list(ring.coords)[:-1]
            pts = []
            for x, y in raw_coords:
                pt = (int(round(x)), int(round(y)))
                if not pts or pts[-1] != pt:
                    pts.append(pt)
            if len(pts) > 1 and pts[0] == pts[-1]:
                pts.pop()
            if len(pts) >= 3:
                pen.moveTo(pts[0])
                for pt in pts[1:]:
                    pen.lineTo(pt)
                pen.closePath()

    return pen.glyph()


def build_digit_0():
    top_cy = Y_TOP - RAD
    bot_cy = Y_BOT + RAD
    loop = (
        arc_pts(X_MID, top_cy, RAD, RAD, 180, 0)
        + arc_pts(X_MID, bot_cy, RAD, RAD, 0, -180)
        + [(X_LEFT, top_cy)]
    )
    return stroke_lines([loop])


def build_digit_1():
    # Sleek vertical stem with refined angled iOS top serif
    stem = [(96.0, 765.0), (166.0, Y_TOP), (166.0, Y_BOT)]
    return stroke_lines([stem])


def build_digit_2():
    top_cy = Y_TOP - RAD
    arch = [(X_LEFT, 705.0)] + arc_pts(X_MID, top_cy, RAD, RAD, 180, -15)
    sweep = cubic_bezier(
        arch[-1],
        (X_RIGHT + 4.0, 545.0),
        (X_LEFT + 10.0, 265.0),
        (X_LEFT, Y_BOT),
    )
    base = [(X_LEFT, Y_BOT), (X_RIGHT, Y_BOT)]
    return stroke_lines([arch + sweep[1:], base])


def build_digit_3():
    waist_y = 456.0
    top_cy = Y_TOP - RAD
    bot_cy = Y_BOT + RAD

    upper = (
        [(X_LEFT + 4.0, 720.0)]
        + arc_pts(X_MID, top_cy, RAD, RAD, 175, 0)
        + [(X_RIGHT, 565.0)]
        + arc_pts(X_MID, 565.0, RAD, 109.0, 0, -90)
        + [(142.0, waist_y)]
    )
    lower = (
        [(142.0, waist_y)]
        + arc_pts(X_MID, 347.0, RAD, 109.0, 90, 0)
        + [(X_RIGHT, bot_cy)]
        + arc_pts(X_MID, bot_cy, RAD, RAD, 0, -175)
        + [(X_LEFT + 4.0, 160.0)]
    )
    return stroke_lines([upper, lower])


def build_digit_4():
    cross_y = 265.0
    stem_x = 236.0
    stem = [(stem_x, Y_BOT), (stem_x, Y_TOP)]
    diag_and_bar = [(stem_x, Y_TOP), (66.0, cross_y), (298.0, cross_y)]
    return stroke_lines([stem, diag_and_bar])


def build_digit_5():
    bot_cy = Y_BOT + RAD
    bowl_top_y = 515.0
    bowl_cy = 395.0
    top_and_drop = [(276.0, Y_TOP), (82.0, Y_TOP), (76.0, 470.0)]
    bowl = (
        [(76.0, 470.0)]
        + arc_pts(X_MID, bowl_cy, RAD, bowl_top_y - bowl_cy, 155, 0)
        + [(X_RIGHT, bot_cy)]
        + arc_pts(X_MID, bot_cy, RAD, RAD, 0, -175)
        + [(X_LEFT + 4.0, 165.0)]
    )
    return stroke_lines([top_and_drop, bowl])


def build_digit_6():
    top_cy = Y_TOP - RAD
    bot_cy = Y_BOT + RAD
    bowl_cy = 355.0
    outer_spine = (
        [(X_RIGHT - 6.0, 725.0)]
        + arc_pts(X_MID, top_cy, RAD, RAD, 15, 180)
        + [(X_LEFT, bot_cy)]
        + arc_pts(X_MID, bot_cy, RAD, RAD, 180, 360)
        + [(X_RIGHT, bowl_cy)]
        + arc_pts(X_MID, bowl_cy, RAD, 115.0, 0, 180)
    )
    return stroke_lines([outer_spine])


def build_digit_7():
    path = [
        (70.0, Y_TOP),
        (X_RIGHT, Y_TOP),
        (X_RIGHT, 815.0),
        (134.0, Y_BOT),
    ]
    return stroke_lines([path])


def build_digit_8():
    waist_y = 452.0
    top_cy = Y_TOP - 100.0
    bot_cy = Y_BOT + RAD
    top_rx = 100.0

    upper_loop = (
        arc_pts(X_MID, top_cy, top_rx, 100.0, 180, 0)
        + arc_pts(X_MID, waist_y + 98.0, top_rx, 98.0, 0, -180)
        + [(X_MID - top_rx, top_cy)]
    )
    lower_loop = (
        arc_pts(X_MID, waist_y - 102.0, RAD, 102.0, 180, 0)
        + arc_pts(X_MID, bot_cy, RAD, RAD, 0, -180)
        + [(X_LEFT, waist_y - 102.0)]
    )
    return stroke_lines([upper_loop, lower_loop])


def build_digit_9():
    top_cy = Y_TOP - RAD
    bot_cy = Y_BOT + RAD
    bowl_cy = 525.0
    outer_spine = (
        [(X_LEFT + 6.0, 155.0)]
        + arc_pts(X_MID, bot_cy, RAD, RAD, 195, 360)
        + [(X_RIGHT, top_cy)]
        + arc_pts(X_MID, top_cy, RAD, RAD, 0, 180)
        + [(X_LEFT, bowl_cy)]
        + arc_pts(X_MID, bowl_cy, RAD, 115.0, 180, 360)
    )
    return stroke_lines([outer_spine])


def build_colon():
    top_dot = Point(80.0, 600.0).buffer(34.0, quad_segs=24)
    bot_dot = Point(80.0, 280.0).buffer(34.0, quad_segs=24)
    return unary_union([top_dot, bot_dot]).simplify(0.35, preserve_topology=True)


def build_notdef():
    frame = LineString([(50, 20), (50, 860), (250, 860), (250, 20), (50, 20)]).buffer(
        16.0, cap_style=1, join_style=1
    )
    return frame


def create_apple_liquid_font():
    glyph_order = [
        ".notdef",
        "space",
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "colon",
    ]

    # Map standard digits and all Unicode colon variants used by Android/One UI lock screens
    cmap = {
        0x0020: "space",
        0x0030: "zero",
        0x0031: "one",
        0x0032: "two",
        0x0033: "three",
        0x0034: "four",
        0x0035: "five",
        0x0036: "six",
        0x0037: "seven",
        0x0038: "eight",
        0x0039: "nine",
        0x003A: "colon",  # Standard colon ':'
        0x2236: "colon",  # Unicode Ratio colon '∶' (used in many Android lockscreen clocks)
        0xA789: "colon",  # Modifier letter colon '꞉'
        0xFE55: "colon",  # Small colon
        0xFF1A: "colon",  # Fullwidth colon
    }

    glyphs = {
        ".notdef": poly_to_ttglyph(build_notdef()),
        "space": TTGlyphPen(None).glyph(),
        "zero": poly_to_ttglyph(build_digit_0()),
        "one": poly_to_ttglyph(build_digit_1()),
        "two": poly_to_ttglyph(build_digit_2()),
        "three": poly_to_ttglyph(build_digit_3()),
        "four": poly_to_ttglyph(build_digit_4()),
        "five": poly_to_ttglyph(build_digit_5()),
        "six": poly_to_ttglyph(build_digit_6()),
        "seven": poly_to_ttglyph(build_digit_7()),
        "eight": poly_to_ttglyph(build_digit_8()),
        "nine": poly_to_ttglyph(build_digit_9()),
        "colon": poly_to_ttglyph(build_colon()),
    }

    metrics = {
        ".notdef": (300, 34),
        "space": (180, 0),
        "zero": (360, 45),
        "one": (250, 67),
        "two": (360, 45),
        "three": (360, 45),
        "four": (360, 37),
        "five": (360, 45),
        "six": (360, 45),
        "seven": (360, 41),
        "eight": (360, 45),
        "nine": (360, 45),
        "colon": (160, 46),
    }

    fb = FontBuilder(unitsPerEm=1000, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=940, descent=-120)
    fb.setupNameTable(
        {
            "familyName": "AppleLiquidGlassClock",
            "styleName": "Regular",
            "uniqueFontIdentifier": "AppleLiquidGlassClock-Regular",
            "fullName": "AppleLiquidGlassClock",
            "version": "Version 1.0",
            "psName": "AppleLiquidGlassClock-Regular",
        }
    )
    fb.setupOS2(
        sTypoAscender=940,
        sTypoDescender=-120,
        sTypoLineGap=0,
        usWinAscent=940,
        usWinDescent=120,
        sxHeight=520,
        sCapHeight=880,
        fsType=0,
    )
    fb.setupPost()

    out_path = os.path.join("assets", "fonts", "AppleLiquidGlassClock.ttf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fb.save(out_path)
    print(f"Successfully generated TTF: {out_path} ({os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    create_apple_liquid_font()
