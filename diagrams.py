"""
diagrams.py — ReportLab vector diagram library for SGMaths worksheets.
Each function returns a ReportLab Drawing() that can be inserted into the story.
"""
from reportlab.graphics.shapes import (
    Drawing, Line, Rect, Polygon, Ellipse, Circle,
    String, Group, PolyLine, Path
)
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.graphics import renderPDF

NAVY  = HexColor("#1e3a5f")
LGRAY = HexColor("#f3f4f6")
GRAY  = HexColor("#9ca3af")
BLACK = colors.black
WHITE = colors.white

def _label(x, y, text, size=8, bold=False, anchor="middle", color=BLACK):
    s = String(x, y, text, fontSize=size, fillColor=color,
               textAnchor=anchor,
               fontName="Helvetica-Bold" if bold else "Helvetica")
    return s

# ─────────────────────────────────────────────────────────────────────────────
# P3 DIAGRAMS
# ─────────────────────────────────────────────────────────────────────────────

def number_pattern_diamond(w=220, h=170):
    """P3 Q5 — Diamond number pattern with 72 centre, 18/9/12/? around it."""
    import math
    d = Drawing(w, h)
    cx, cy = 110, 85

    # Centre square
    d.add(Rect(cx - 22, cy - 22, 44, 44,
               strokeColor=BLACK, strokeWidth=1.2, fillColor=WHITE))
    d.add(_label(cx, cy - 7, "72", size=15, bold=True))

    # (outer_x, outer_y, value, multiplier_label, arrow direction)
    nodes = [
        (cx,       cy + 68, "18", "4",  "top"),
        (cx - 68,  cy,      "9",  "8",  "left"),
        (cx + 68,  cy,      "12", "6",  "right"),
        (cx,       cy - 68, "?",  "3",  "bottom"),
    ]

    for ox, oy, val, mult, direction in nodes:
        # Outer circle
        d.add(Circle(ox, oy, 20,
                     strokeColor=BLACK, strokeWidth=1.2, fillColor=WHITE))
        d.add(_label(ox, oy - 6, val, size=12, bold=True))

        # Arrow line between circle edge and centre square edge
        if direction == "top":
            lx1, ly1 = cx, cy + 22          # top of centre square
            lx2, ly2 = cx, oy - 20          # bottom of outer circle
            mx, my   = cx + 6, cy + 45
        elif direction == "bottom":
            lx1, ly1 = cx, cy - 22
            lx2, ly2 = cx, oy + 20
            mx, my   = cx + 6, cy - 45
        elif direction == "left":
            lx1, ly1 = cx - 22, cy
            lx2, ly2 = ox + 20, cy
            mx, my   = cx - 45, cy + 8
        else:  # right
            lx1, ly1 = cx + 22, cy
            lx2, ly2 = ox - 20, cy
            mx, my   = cx + 45, cy + 8

        d.add(Line(lx1, ly1, lx2, ly2,
                   strokeColor=BLACK, strokeWidth=0.9))

        # Multiplier label alongside arrow
        d.add(_label(mx, my, mult, size=8, bold=True))

    return d


def bar_chart_library(w=260, h=160):
    """P3 Q6 — Bar chart: number of P1 pupils vs library visits (1-5 times)."""
    d = Drawing(w, h)
    data = [("1", 65), ("2", 35), ("3", 80), ("4", 40), ("5", 28)]
    max_v = 90
    ox, oy = 50, 22
    chart_w, chart_h = 192, 112
    bar_w = 28

    # Axes
    d.add(Line(ox, oy, ox, oy + chart_h, strokeColor=BLACK, strokeWidth=0.9))
    d.add(Line(ox, oy, ox + chart_w, oy, strokeColor=BLACK, strokeWidth=0.9))

    # Y gridlines and numeric labels
    for v in range(0, 100, 10):
        y = oy + (v / max_v) * chart_h
        d.add(Line(ox, y, ox + chart_w, y, strokeColor=GRAY, strokeWidth=0.3))
        d.add(_label(ox - 4, y - 3, str(v), size=6, anchor="end"))

    # Bars
    for i, (label, val) in enumerate(data):
        bx = ox + 10 + i * 36
        bh = (val / max_v) * chart_h
        d.add(Rect(bx, oy, bar_w, bh,
                   strokeColor=BLACK, strokeWidth=0.6,
                   fillColor=HexColor("#b0c4d8")))
        d.add(_label(bx + bar_w // 2, oy - 11, label, size=7))

    # X-axis title
    d.add(_label(ox + chart_w // 2, 4, "Number of visits to the library", size=6.5))

    # Y-axis title rotated 90 degrees
    ylabel = String(0, 0, "Number of pupils", fontSize=6.5,
                    fillColor=BLACK, textAnchor="middle", fontName="Helvetica")
    g = Group(ylabel)
    g.transform = (0, 1, -1, 0, 10, oy + chart_h // 2)
    d.add(g)

    # Chart title
    d.add(_label(ox + chart_w // 2, oy + chart_h + 8,
                 "Number of Times P1 Pupils Went to the Library", size=6.5, bold=True))

    return d


def bar_chart_hairdryers(w=260, h=160):
    """P3 Q9 — Grouped bar chart: Brand A & B hair dryers sold Mon-Fri."""
    d = Drawing(w, h)
    days    = ["Mon", "Tues", "Wed", "Thurs", "Fri"]
    brand_a = [12, 8, 7, 15, 11]
    brand_b = [8, 10, 13, 3, 6]
    max_v   = 18
    ox, oy  = 50, 28
    chart_w = 195
    chart_h = 105
    bar_w   = 14
    group_w = 38

    # Axes
    d.add(Line(ox, oy, ox, oy + chart_h, strokeColor=BLACK, strokeWidth=0.9))
    d.add(Line(ox, oy, ox + chart_w, oy, strokeColor=BLACK, strokeWidth=0.9))

    # Y gridlines and numeric labels (every 2)
    for v in range(0, max_v + 1, 2):
        y = oy + (v / max_v) * chart_h
        d.add(Line(ox, y, ox + chart_w, y, strokeColor=GRAY, strokeWidth=0.3))
        d.add(_label(ox - 4, y - 3, str(v), size=6, anchor="end"))

    # Grouped bars
    for i, day in enumerate(days):
        gx = ox + 8 + i * group_w
        bh_a = (brand_a[i] / max_v) * chart_h
        d.add(Rect(gx, oy, bar_w, bh_a,
                   strokeColor=BLACK, strokeWidth=0.5,
                   fillColor=HexColor("#5b7faa")))
        bh_b = (brand_b[i] / max_v) * chart_h
        d.add(Rect(gx + bar_w + 2, oy, bar_w, bh_b,
                   strokeColor=BLACK, strokeWidth=0.5,
                   fillColor=HexColor("#c8d8e8")))
        d.add(_label(gx + bar_w + 1, oy - 11, day, size=6.5))

    # Legend
    lx = ox + 20
    ly = oy + chart_h + 10
    d.add(Rect(lx, ly, 10, 8, fillColor=HexColor("#5b7faa"),
               strokeColor=BLACK, strokeWidth=0.5))
    d.add(_label(lx + 13, ly + 2, "Brand A", size=6.5, anchor="start"))
    d.add(Rect(lx + 65, ly, 10, 8, fillColor=HexColor("#c8d8e8"),
               strokeColor=BLACK, strokeWidth=0.5))
    d.add(_label(lx + 78, ly + 2, "Brand B", size=6.5, anchor="start"))

    # Y-axis title rotated 90 degrees
    ylabel = String(0, 0, "No. of hair dryers sold", fontSize=6.5,
                    fillColor=BLACK, textAnchor="middle", fontName="Helvetica")
    g = Group(ylabel)
    g.transform = (0, 1, -1, 0, 10, oy + chart_h // 2)
    d.add(g)

    # Chart title
    d.add(_label(ox + chart_w // 2, oy + chart_h + 24,
                 "Number of Hair Dryers Sold at Sunshine Shop", size=6.5, bold=True))

    return d


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY DIAGRAMS
# ─────────────────────────────────────────────────────────────────────────────

def cuboid_8x3(w=120, h=90):
    """P5 Q2 / P5 Q11 — Cuboid with height 8 cm, square base 3 cm."""
    d = Drawing(w, h)
    ox, oy = 20, 10
    fw, fh = 50, 65   # front face width, height
    off = 22           # isometric offset

    # back face
    d.add(Rect(ox+off, oy+off, fw, fh, strokeColor=BLACK, strokeWidth=0.8,
               fillColor=HexColor("#e8edf2")))
    # front face
    d.add(Rect(ox, oy, fw, fh, strokeColor=BLACK, strokeWidth=0.8,
               fillColor=WHITE))
    # top face (parallelogram)
    top = Polygon([ox, oy+fh, ox+off, oy+fh+off, ox+off+fw, oy+fh+off, ox+fw, oy+fh],
                  strokeColor=BLACK, strokeWidth=0.8, fillColor=HexColor("#d1dae5"))
    d.add(top)
    # right face
    right = Polygon([ox+fw, oy, ox+fw+off, oy+off, ox+fw+off, oy+fh+off, ox+fw, oy+fh],
                    strokeColor=BLACK, strokeWidth=0.8, fillColor=HexColor("#c8d4e0"))
    d.add(right)
    # dimension labels
    d.add(_label(ox + fw + off + 6, oy + fh//2 + off//2, "8 cm", size=8, anchor="start"))
    d.add(_label(ox + fw//2, oy - 10, "3 cm", size=8, anchor="middle"))
    return d

def shaded_triangle_16x15(w=160, h=100):
    """P5 Q3 / Ai Tong — Shaded triangle with base 25m, sides 16m and 15m."""
    d = Drawing(w, h)
    # Large outer triangle
    pts = [10, 10, 150, 10, 110, 90]
    d.add(Polygon(pts, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    # Shaded inner triangle (lower left portion)
    shade = Polygon([10, 10, 110, 10, 80, 55],
                    strokeColor=BLACK, strokeWidth=0.8,
                    fillColor=HexColor("#c8c8c8"))
    d.add(shade)
    d.add(_label(60, 3, "25 m", size=7))
    d.add(_label(3, 55, "16 m", size=7, anchor="start"))
    d.add(_label(115, 55, "15 m", size=7, anchor="start"))
    d.add(_label(43, 22, "4 m", size=7))
    return d

def rectangle_aceh(w=170, h=110):
    """P5 Q10 — Rectangle ACEH with triangles GKD and AKD shaded."""
    d = Drawing(w, h)
    # Main rectangle
    d.add(Rect(10, 10, 150, 90, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    # Internal structure: AC=21cm, DE=6cm, so KD splits it
    # K is at x=60 from left, y=top-6 from bottom of right portion
    kx, ky = 70, 46  # K position in drawing coords
    # Shaded triangles
    # Triangle GKD (left shaded)
    d.add(Polygon([10, 10, kx, ky, 10, 90],
                  strokeColor=BLACK, strokeWidth=0.5,
                  fillColor=HexColor("#b0b8c8")))
    # Triangle AKD (right shaded, crosshatch approx)
    d.add(Polygon([kx, ky, 160, 46, 160, 10, 100, 10],
                  strokeColor=BLACK, strokeWidth=0.5,
                  fillColor=HexColor("#d0d8e8")))
    # Labels
    d.add(_label(85, 100, "21 cm", size=7))
    d.add(_label(163, 28, "6 cm", size=7, anchor="start"))
    d.add(_label(7, 90, "H", size=7, anchor="end"))
    d.add(_label(7, 10, "A", size=7, anchor="end"))
    d.add(_label(163, 10, "C", size=7, anchor="start"))
    d.add(_label(163, 46, "D", size=7, anchor="start"))
    d.add(_label(163, 100, "E", size=7, anchor="start"))
    d.add(_label(kx-3, ky-8, "K", size=7))
    d.add(_label(10, 46, "G", size=7, anchor="end"))
    d.add(_label(40, 10, "F", size=7))
    return d

def rectangular_container_45x38x40(w=180, h=110):
    """P5 Q7 — Rectangular container 45×38×40 cm."""
    d = Drawing(w, h)
    ox, oy = 15, 8
    fw, fh = 100, 75
    off = 30
    # back
    d.add(Rect(ox+off, oy+off, fw, fh, strokeColor=BLACK, strokeWidth=0.7,
               fillColor=HexColor("#dde4ec")))
    # water fill (5/8) on front face
    water_h = int(fh * 5 / 8)
    d.add(Rect(ox, oy, fw, water_h, strokeColor=None,
               fillColor=HexColor("#bfd6e8")))
    # front
    d.add(Rect(ox, oy, fw, fh, strokeColor=BLACK, strokeWidth=0.7, fillColor=None))
    # top
    top = Polygon([ox, oy+fh, ox+off, oy+fh+off, ox+off+fw, oy+fh+off, ox+fw, oy+fh],
                  strokeColor=BLACK, strokeWidth=0.7, fillColor=HexColor("#c8d8e8"))
    d.add(top)
    # right
    right = Polygon([ox+fw, oy, ox+fw+off, oy+off, ox+fw+off, oy+fh+off, ox+fw, oy+fh],
                    strokeColor=BLACK, strokeWidth=0.7, fillColor=HexColor("#b8ccde"))
    d.add(right)
    d.add(_label(ox+fw//2, oy-8, "45 cm", size=7))
    d.add(_label(ox+fw+off+4, oy+fh//2+off//2, "40 cm", size=7, anchor="start"))
    d.add(_label(ox+fw+off//2+4, oy+off//2-4, "38 cm", size=7, anchor="start"))
    d.add(_label(ox+fw//2, oy+6, "Container", size=7))
    return d

def garden_rectangle_lightbulbs(w=200, h=130):
    """P5 Q11 — Rectangular garden ABCD with light bulbs."""
    d = Drawing(w, h)
    d.add(Rect(20, 20, 160, 90, strokeColor=BLACK, strokeWidth=1, fillColor=WHITE))
    # Corner labels
    d.add(_label(15, 112, "A", size=8, bold=True, anchor="end"))
    d.add(_label(185, 112, "B", size=8, bold=True))
    d.add(_label(185, 16, "C", size=8, bold=True))
    d.add(_label(15, 16, "D", size=8, bold=True, anchor="end"))
    # Dots along bottom DC
    for i in range(17):
        x = 20 + i * 10
        d.add(Circle(x, 20, 2, fillColor=BLACK, strokeColor=None))
    # Dots along right BC (fewer)
    for i in range(1, 6):
        d.add(Circle(180, 20 + i * 15, 2, fillColor=BLACK, strokeColor=None))
    d.add(_label(100, 10, "17 light bulbs", size=7))
    d.add(_label(100, 65, "GARDEN", size=9, color=GRAY))
    return d

def parallelogram_angles(w=180, h=110):
    """P6 Q20 — Parallelogram ABCD with angles 112° and 95°."""
    d = Drawing(w, h)
    pts = [20, 20, 80, 90, 170, 90, 110, 20]
    d.add(Polygon(pts, strokeColor=BLACK, strokeWidth=1, fillColor=WHITE))
    d.add(_label(18, 18, "D", size=8, anchor="end"))
    d.add(_label(18, 90, "A", size=8, anchor="end"))
    d.add(_label(172, 92, "B", size=8))
    d.add(_label(112, 18, "C", size=8))
    d.add(_label(85, 95, "G", size=7))
    d.add(_label(140, 95, "F", size=7))
    d.add(_label(145, 105, "E", size=7))
    d.add(_label(35, 80, "112°", size=7))
    d.add(_label(138, 80, "95°", size=7))
    d.add(Line(80, 90, 155, 25, strokeColor=BLACK, strokeWidth=0.8))
    d.add(Line(20, 20, 155, 25, strokeColor=BLACK, strokeWidth=0.8))
    return d

def rhombus_angles(w=150, h=150):
    """P6 Q21 — Rhombus ABCD with angles 25° and 55°."""
    d = Drawing(w, h)
    pts = [75, 140, 130, 90, 75, 15, 20, 65]
    d.add(Polygon(pts, strokeColor=BLACK, strokeWidth=1, fillColor=WHITE))
    d.add(_label(75, 145, "A", size=8, anchor="middle"))
    d.add(_label(135, 90, "B", size=8))
    d.add(_label(75, 8, "C", size=8, anchor="middle"))
    d.add(_label(12, 65, "D", size=8, anchor="end"))
    fx, fy = 80, 80
    d.add(_label(fx, fy+4, "F", size=7))
    d.add(_label(fx-20, fy+15, "E", size=7))
    d.add(_label(28, 78, "25°", size=7))
    d.add(_label(118, 100, "55°", size=7))
    d.add(Line(75, 140, 75, 15, strokeColor=BLACK, strokeWidth=0.7))
    d.add(Line(20, 65, 130, 90, strokeColor=BLACK, strokeWidth=0.7))
    return d

def rectangle_folded_prs23(w=180, h=100):
    """P6 Q19 — Rectangle PQRS folded along diagonal PR, angle PRS=23°."""
    d = Drawing(w, h)
    d.add(Rect(10, 40, 70, 50, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    d.add(_label(8, 92, "P", size=8, anchor="end"))
    d.add(_label(83, 92, "Q", size=8))
    d.add(_label(83, 38, "R", size=8))
    d.add(_label(8, 38, "S", size=8, anchor="end"))
    d.add(Line(10, 90, 80, 40, strokeColor=BLACK, strokeWidth=0.8, strokeDashArray=[3,2]))
    d.add(_label(50, 42, "23°", size=7))
    d.add(_label(100, 65, "→", size=14))
    d.add(Rect(115, 40, 55, 50, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    d.add(Polygon([115, 90, 170, 90, 145, 55],
                  strokeColor=BLACK, strokeWidth=0.8,
                  fillColor=HexColor("#d0d8e8")))
    d.add(_label(113, 92, "P", size=8, anchor="end"))
    d.add(_label(172, 92, "R", size=8))
    d.add(_label(172, 38, "Q", size=8))
    d.add(_label(113, 38, "S", size=8, anchor="end"))
    return d


# ─────────────────────────────────────────────────────────────────────────────
# AREA & PERIMETER DIAGRAMS
# ─────────────────────────────────────────────────────────────────────────────

def semicircles_figure(w=120, h=100):
    """P6 Q25 — Two identical semicircles of diameter 14 cm, joined."""
    import math
    d = Drawing(w, h)
    cx, cy, r = 60, 50, 38
    steps = 24
    pts_l = [cx, cy]
    for i in range(steps + 1):
        ang = math.radians(90 + 180 * i / steps)
        pts_l += [cx + r * math.cos(ang), cy + r * math.sin(ang)]
    d.add(Polygon(pts_l, fillColor=HexColor("#dde8f0"), strokeColor=BLACK, strokeWidth=0.8))
    pts_r = [cx, cy]
    for i in range(steps + 1):
        ang = math.radians(-90 + 180 * i / steps)
        pts_r += [cx + r * math.cos(ang), cy + r * math.sin(ang)]
    d.add(Polygon(pts_r, fillColor=HexColor("#dde8f0"), strokeColor=BLACK, strokeWidth=0.8))
    d.add(_label(cx, cy - r - 8, "14 cm", size=7))
    d.add(Line(cx, cy - r, cx, cy + r, strokeColor=BLACK, strokeWidth=0.5, strokeDashArray=[2,2]))
    d.add(_label(cx + 3, cy, "5 cm", size=7, anchor="start"))
    return d

def shaded_triangle_rectangle(w=180, h=100):
    """P6 Q26 — Shaded triangle inside rectangle, 5cm+9cm wide, 8cm tall."""
    d = Drawing(w, h)
    d.add(Rect(10, 10, 160, 80, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    shade = Polygon([10, 10, 60, 90, 170, 90],
                    strokeColor=BLACK, strokeWidth=0.8,
                    fillColor=HexColor("#c0c8d0"))
    d.add(shade)
    d.add(Line(10, 95, 60, 95, strokeColor=BLACK, strokeWidth=0.5))
    d.add(Line(60, 95, 170, 95, strokeColor=BLACK, strokeWidth=0.5))
    d.add(_label(35, 98, "5 cm", size=7))
    d.add(_label(115, 98, "9 cm", size=7))
    d.add(_label(3, 50, "8 cm", size=7, anchor="end"))
    return d

def quarter_circle_square(w=120, h=110):
    """P6 Q29 / Catholic High — Quarter circle + square, side 6 cm."""
    import math
    d = Drawing(w, h)
    r = 68
    ox, oy = 18, 10
    steps = 20
    pts = [ox, oy + r]
    for i in range(steps + 1):
        ang = math.radians(0 + 90 * i / steps)
        pts += [ox - r * math.sin(ang), oy + r * math.cos(ang)]
    d.add(Polygon(pts, fillColor=HexColor("#dde8f0"), strokeColor=BLACK, strokeWidth=0.8))
    d.add(Rect(ox, oy, r, r, strokeColor=BLACK, strokeWidth=0.8, fillColor=None))
    d.add(_label(ox + r//2, oy - 8, "6 cm", size=7))
    d.add(_label(ox + r + 3, oy + r//2, "6 cm", size=7, anchor="start"))
    return d

def rectangle_two_semicircles(w=200, h=80):
    """P6 Q30 / Catholic High — Rectangle 24m with semicircles radius 4m on each end."""
    import math
    d = Drawing(w, h)
    ox, oy = 30, 10
    rw, rh = 130, 55
    r = rh // 2
    cx_l = ox
    cx_r = ox + rw
    cy = oy + r

    steps = 20
    p_l = Path(fillColor=WHITE, strokeColor=BLACK, strokeWidth=0.8)
    pts_l = [(cx_l + r*math.cos(math.pi/2 + math.pi*i/steps),
              cy + r*math.sin(math.pi/2 + math.pi*i/steps)) for i in range(steps+1)]
    p_l.moveTo(pts_l[0][0], pts_l[0][1])
    for px, py in pts_l[1:]:
        p_l.lineTo(px, py)
    d.add(p_l)

    pts_r = [(cx_r + r*math.cos(-math.pi/2 + math.pi*i/steps),
              cy + r*math.sin(-math.pi/2 + math.pi*i/steps)) for i in range(steps+1)]
    p_r = Path(fillColor=WHITE, strokeColor=BLACK, strokeWidth=0.8)
    p_r.moveTo(pts_r[0][0], pts_r[0][1])
    for px, py in pts_r[1:]:
        p_r.lineTo(px, py)
    d.add(p_r)

    d.add(Rect(ox, oy, rw, rh, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    d.add(Line(ox, oy + rh + 8, ox + rw, oy + rh + 8, strokeColor=BLACK, strokeWidth=0.5))
    d.add(_label(ox + rw//2, oy + rh + 11, "24 m", size=7))
    d.add(_label(cx_r + 4, cy, "4 m", size=7, anchor="start"))
    d.add(Line(cx_r, cy, cx_r + r, cy, strokeColor=BLACK, strokeWidth=0.5,
               strokeDashArray=[2, 2]))
    return d

def circle_diagram(w=120, h=120, label="r = 21 cm"):
    """Generic circle with radius label."""
    d = Drawing(w, h)
    cx, cy, r = 60, 60, 48
    d.add(Circle(cx, cy, r, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    d.add(Line(cx, cy, cx + r, cy, strokeColor=BLACK, strokeWidth=0.6,
               strokeDashArray=[2, 2]))
    d.add(_label(cx + r//2 + 2, cy + 4, label, size=7))
    d.add(Circle(cx, cy, 2, fillColor=BLACK, strokeColor=None))
    return d

def circle_diameter(w=120, h=120, label="d = 70 cm"):
    """Circle with diameter label."""
    d = Drawing(w, h)
    cx, cy, r = 60, 60, 48
    d.add(Circle(cx, cy, r, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    d.add(Line(cx - r, cy, cx + r, cy, strokeColor=BLACK, strokeWidth=0.6,
               strokeDashArray=[2, 2]))
    d.add(_label(cx, cy + 6, label, size=7))
    return d


# ─────────────────────────────────────────────────────────────────────────────
# DATA DIAGRAMS
# ─────────────────────────────────────────────────────────────────────────────

def bar_chart_pets(w=200, h=130):
    """P6 Q31 — Bar chart: pets per household."""
    d = Drawing(w, h)
    data = [(0, 15), (1, 22), (2, 40), (3, 30), (4, 11)]
    max_v = 45
    ox, oy = 30, 15
    chart_w, chart_h = 155, 90
    bar_w = 22

    d.add(Line(ox, oy, ox, oy + chart_h, strokeColor=BLACK, strokeWidth=0.8))
    d.add(Line(ox, oy, ox + chart_w, oy, strokeColor=BLACK, strokeWidth=0.8))

    for v in [0, 10, 20, 30, 40]:
        y = oy + (v / max_v) * chart_h
        d.add(Line(ox, y, ox + chart_w, y, strokeColor=GRAY, strokeWidth=0.3))
        d.add(_label(ox - 3, y - 3, str(v), size=6, anchor="end"))

    for i, (label, val) in enumerate(data):
        bx = ox + 10 + i * 30
        bh = (val / max_v) * chart_h
        d.add(Rect(bx, oy, bar_w, bh, strokeColor=BLACK, strokeWidth=0.5,
                   fillColor=HexColor("#b0c4d8")))
        d.add(_label(bx + bar_w // 2, oy - 9, str(label), size=6))

    d.add(_label(ox + chart_w // 2, 3, "Number of pets per household", size=6))
    d.add(_label(8, oy + chart_h // 2, "Households", size=6, anchor="middle"))
    return d

def pie_chart_lilian(w=160, h=140):
    """P6 Q14 — Pie chart: Food (50%), Transport (15%), Books, Entertainment."""
    import math
    d = Drawing(w, h)
    cx, cy, r = 70, 75, 55
    d.add(Circle(cx, cy, r, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))

    segments = [
        ("Food",          0.50, HexColor("#c8d8e8")),
        ("Transport",     0.15, HexColor("#b0c4d8")),
        ("Entertainment", 0.10, HexColor("#e8e0d0")),
        ("Books\n$80",    0.25, HexColor("#d0d8c8")),
    ]
    start = 90
    for name, pct, col in segments:
        steps = max(4, int(abs(pct) * 36))
        pts = [cx, cy]
        for s in range(steps + 1):
            ang = math.radians(start - pct * 360 * s / steps)
            pts += [cx + r * math.cos(ang), cy + r * math.sin(ang)]
        d.add(Polygon(pts, fillColor=col, strokeColor=BLACK, strokeWidth=0.5))
        mid_ang = math.radians(start - pct * 180)
        lx = cx + (r * 0.65) * math.cos(mid_ang)
        ly = cy + (r * 0.65) * math.sin(mid_ang)
        short = name.split("\n")[0]
        d.add(_label(lx, ly, short, size=6))
        start -= pct * 360

    d.add(_label(cx, 8, "15% Transport", size=6))
    return d

def symmetry_grid(w=130, h=130):
    """P6 Q5 — Grid with diagonal line PQ for symmetry question."""
    d = Drawing(w, h)
    for i in range(7):
        d.add(Line(10 + i*18, 10, 10 + i*18, 118, strokeColor=GRAY, strokeWidth=0.5))
        d.add(Line(10, 10 + i*18, 118, 10 + i*18, strokeColor=GRAY, strokeWidth=0.5))
    shaded = [(0,5),(1,4),(1,5),(2,3),(2,4),(3,2),(3,3),(4,1),(4,2)]
    for col, row in shaded:
        x = 10 + col * 18
        y = 10 + row * 18
        d.add(Rect(x, y, 18, 18, fillColor=HexColor("#b8b8b8"), strokeColor=BLACK,
                   strokeWidth=0.3))
    d.add(Line(10, 118, 118, 10, strokeColor=BLACK, strokeWidth=1.2))
    d.add(_label(120, 8, "P", size=8, bold=True))
    d.add(_label(5, 120, "Q", size=8, bold=True, anchor="end"))
    return d

def six_cubes_cuboid(w=140, h=80):
    """P6 Q37 — 6 unit cubes in 3×2×1 arrangement."""
    d = Drawing(w, h)
    cw, ch, off = 30, 30, 12
    for col in range(3):
        for row in range(2):
            ox = 10 + col * cw + row * off//2
            oy = 8 + row * ch//2
            d.add(Rect(ox, oy, cw, ch, strokeColor=BLACK, strokeWidth=0.7,
                       fillColor=WHITE))
            top = Polygon([ox, oy+ch, ox+off, oy+ch+off//2,
                            ox+cw+off, oy+ch+off//2, ox+cw, oy+ch],
                          strokeColor=BLACK, strokeWidth=0.7,
                          fillColor=HexColor("#d8e0e8"))
            d.add(top)
    d.add(_label(20, 5, "1 cm", size=7))
    d.add(Line(10, 8, 40, 8, strokeColor=BLACK, strokeWidth=0.5))
    return d

def parallelogram_EFGH(w=200, h=130):
    """P6 Q24 / Catholic High — Parallelogram EFGH + trapezium EBHA."""
    d = Drawing(w, h)
    pts_efgh = [25, 20, 80, 110, 185, 110, 130, 20]
    d.add(Polygon(pts_efgh, strokeColor=BLACK, strokeWidth=0.8, fillColor=WHITE))
    pts_ebha = [25, 20, 60, 110, 80, 110, 60, 20]
    d.add(Polygon(pts_ebha, strokeColor=BLACK, strokeWidth=0.8,
                  fillColor=HexColor("#e0e8f0")))
    d.add(_label(25, 115, "E", size=8, bold=True, anchor="middle"))
    d.add(_label(130, 115, "F", size=8, bold=True))
    d.add(_label(185, 113, "G", size=8, bold=True))
    d.add(_label(80, 113, "H", size=8, bold=True))
    d.add(_label(60, 113, "B", size=8, bold=True))
    d.add(_label(25, 18, "A", size=8, bold=True, anchor="end"))
    d.add(_label(30, 80, "34°", size=7))
    d.add(_label(62, 95, "76°", size=7))
    d.add(_label(153, 105, "108°", size=7))
    return d


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM REGISTRY — maps question (level, id) to a drawing function
# ─────────────────────────────────────────────────────────────────────────────

DIAGRAM_REGISTRY = {
    # P3
    ("P3", 5):  number_pattern_diamond,
    ("P3", 6):  bar_chart_library,
    ("P3", 9):  bar_chart_hairdryers,
    # P5
    ("P5", 5):  shaded_triangle_16x15,
    ("P5", 6):  rectangle_aceh,
    ("P5", 11): cuboid_8x3,
    ("P5", 12): rectangular_container_45x38x40,
    ("P5", 25): garden_rectangle_lightbulbs,
    # P6
    ("P6", 5):  symmetry_grid,
    ("P6", 14): pie_chart_lilian,
    ("P6", 19): rectangle_folded_prs23,
    ("P6", 20): parallelogram_angles,
    ("P6", 21): rhombus_angles,
    ("P6", 24): parallelogram_EFGH,
    ("P6", 25): semicircles_figure,
    ("P6", 26): shaded_triangle_rectangle,
    ("P6", 27): lambda: circle_diagram(label="r = 21 cm"),
    ("P6", 28): lambda: circle_diameter(label="d = 70 cm"),
    ("P6", 29): quarter_circle_square,
    ("P6", 30): rectangle_two_semicircles,
    ("P6", 31): bar_chart_pets,
    ("P6", 37): six_cubes_cuboid,
}

def get_diagram(level, qid):
    """Return a Drawing for the given question, or None if no diagram exists."""
    fn = DIAGRAM_REGISTRY.get((level, qid))
    if fn is None:
        return None
    try:
        return fn()
    except Exception as e:
        print(f"Diagram error ({level}, {qid}): {e}")
        return None
