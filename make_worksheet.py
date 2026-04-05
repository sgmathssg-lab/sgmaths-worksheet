from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, Image, KeepTogether, Flowable
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
import os, re

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY   = HexColor("#1e3a5f")
TEAL   = HexColor("#0e7490")
LGRAY  = HexColor("#f3f4f6")
MGRAY  = HexColor("#6b7280")
BORDER = HexColor("#e5e7eb")
GREEN  = HexColor("#166534")
AMBER  = HexColor("#854d0e")
RED    = HexColor("#991b1b")
GBG    = HexColor("#dcfce7")
ABG    = HexColor("#fef9c3")
RBG    = HexColor("#fee2e2")

BODY_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"

# ── Mixed text+fraction line renderer ────────────────────────────────────────
# Segment types: ('text', str) | ('frac', num_str, den_str, whole_str_or_None)
FRAC_RE = re.compile(r'(\b\d+\s+)?(\d+)\s*/\s*(\d+)')

def _parse_segs(line):
    """Return list of ('text'|'frac', ...) segments for one line."""
    segs, last = [], 0
    for m in FRAC_RE.finditer(line):
        pre = line[last:m.start()]
        if pre:
            segs.append(('text', pre))
        whole = m.group(1).strip() if m.group(1) else None
        segs.append(('frac', m.group(2), m.group(3), whole))
        last = m.end()
    tail = line[last:]
    if tail:
        segs.append(('text', tail))
    return segs or [('text', ' ')]


class MixedLine(Flowable):
    """
    Renders one line of text that may contain stacked fractions.
    Everything is drawn on a single canvas pass sharing one baseline —
    no table padding, no alignment drift.
    """
    def __init__(self, segs, fsize=10, bold_prefix=None, color=colors.black, leading=16):
        super().__init__()
        self.segs        = segs
        self.fsize       = fsize
        self.nsize       = fsize * 0.72          # fraction num/den size
        self.color       = color
        self.leading     = leading
        self.bold_prefix = bold_prefix           # e.g. "Q1." drawn bold before segs
        self._calc()

    # ── sizing ────────────────────────────────────────────────────────────────
    def _frac_metrics(self, num, den, whole):
        sw  = lambda s, sz: stringWidth(s, BODY_FONT, sz)
        nw  = sw(num, self.nsize)
        dw  = sw(den, self.nsize)
        fw  = max(nw, dw) + 4
        ww  = sw(whole + "\u2009", self.fsize) if whole else 0  # thin space after whole
        nh  = self.nsize * 1.1
        gap = 1.6
        # fraction total height above baseline = nh + gap + bar (bar at nh+gap from bottom of frac)
        # we position bar at TEXT_BASELINE + fsize*0.25  (midline of body text)
        return dict(nw=nw, dw=dw, fw=fw, ww=ww, nh=nh, gap=gap,
                    total_w=ww + fw + 2)

    def _calc(self):
        sw = lambda s, sz: stringWidth(s, BODY_FONT, sz)
        bw = stringWidth(self.bold_prefix, BOLD_FONT, self.fsize) + 4 if self.bold_prefix else 0
        total_w = bw
        has_frac = False
        for seg in self.segs:
            if seg[0] == 'text':
                total_w += sw(seg[1], self.fsize)
            else:
                _, num, den, whole = seg
                m = self._frac_metrics(num, den, whole)
                total_w += m['total_w']
                has_frac = True
        self._has_frac = has_frac
        self._bw       = bw
        self._total_w  = total_w
        # height: enough for fraction (num above bar + den below bar) or plain leading
        nh  = self.nsize * 1.1
        gap = 1.6
        frac_h = nh + gap + 0.7 + nh + gap   # above + below bar
        self.height = max(self.leading, frac_h + 2) if has_frac else self.leading

    def wrap(self, aw, ah):
        self._aw = aw
        return aw, self.height

    # ── drawing ───────────────────────────────────────────────────────────────
    def draw(self):
        c   = self.canv
        c.saveState()
        c.setFillColor(self.color)
        c.setStrokeColor(self.color)

        # baseline: sit text on lower quarter of cell height
        baseline = self.height * 0.22

        x = 0
        if self.bold_prefix:
            c.setFont(BOLD_FONT, self.fsize)
            c.drawString(x, baseline, self.bold_prefix + " ")
            x += self._bw

        sw = lambda s, sz: stringWidth(s, BODY_FONT, sz)

        for seg in self.segs:
            if seg[0] == 'text':
                c.setFont(BODY_FONT, self.fsize)
                c.drawString(x, baseline, seg[1])
                x += sw(seg[1], self.fsize)
            else:
                _, num, den, whole = seg
                m  = self._frac_metrics(num, den, whole)
                nh  = m['nh']
                gap = m['gap']
                fw  = m['fw']
                nw  = m['nw']
                dw  = m['dw']
                # whole number aligns baseline
                if whole:
                    c.setFont(BODY_FONT, self.fsize)
                    c.drawString(x, baseline, whole)
                    x += m['ww']
                # bar sits at text midline (cap-height midpoint ≈ baseline + fsize*0.3)
                bar_y = baseline + self.fsize * 0.30
                c.setLineWidth(0.65)
                c.line(x, bar_y, x + fw, bar_y)
                # numerator above bar
                c.setFont(BODY_FONT, self.nsize)
                c.drawString(x + (fw - nw) / 2, bar_y + gap, num)
                # denominator below bar
                c.drawString(x + (fw - dw) / 2, bar_y - nh - 0.5, den)
                x += fw + 2

        c.restoreState()


def make_inline(text, style, fsize=10, total_width=13.3*cm, bold_prefix=None):
    """
    Convert a (possibly multi-line) string with n/d fractions into
    a list of MixedLine flowables — one per text line.
    Falls back to plain Paragraph for lines with no fractions.
    """
    result  = []
    leading = getattr(style, 'leading', fsize * 1.4)
    for line in text.split('\n'):
        segs     = _parse_segs(line)
        has_frac = any(s[0] == 'frac' for s in segs)
        if not has_frac and not bold_prefix:
            result.append(Paragraph(line or ' ', style))
        else:
            result.append(MixedLine(segs, fsize=fsize,
                                    bold_prefix=bold_prefix if result == [] else None,
                                    leading=leading))
    return result


# ── Question bank ─────────────────────────────────────────────────────────────
QUESTIONS = [
    dict(id=1,  topic="Fractions",          difficulty="Easy",   school="St Hilda's",     marks=1,
         text="Express 26/7 as a mixed number.",
         type="mcq", opts=["A.  2 6/7", "B.  3 5/7", "C.  5 3/7", "D.  7 3/5"], answer="B.  3 5/7"),
    dict(id=2,  topic="Fractions",          difficulty="Easy",   school="St Hilda's",     marks=1,
         text="What is 2/9 of 18?",
         type="mcq", opts=["A.  1", "B.  81", "C.  162", "D.  4"], answer="D.  4"),
    dict(id=3,  topic="Fractions",          difficulty="Medium", school="St Hilda's",     marks=2,
         text="Find the difference between 3/5 and 2/3.",
         type="mcq", opts=["A.  1/15", "B.  1/2", "C.  5/8", "D.  19/15"], answer="A.  1/15"),
    dict(id=4,  topic="Fractions",          difficulty="Medium", school="Red Swastika",   marks=2,
         text="Write 15/7 as a mixed number.",
         type="short", answer="2 1/7"),
    dict(id=5,  topic="Fractions",          difficulty="Medium", school="Red Swastika",   marks=2,
         text="Express 0.75 as a fraction in its simplest form.",
         type="short", answer="3/4"),
    dict(id=6,  topic="Fractions",          difficulty="Medium", school="Rosyth",         marks=2,
         text="Find the value of 11/12 - 2/3 in its simplest form.",
         type="short", answer="1/4"),
    dict(id=7,  topic="Fractions",          difficulty="Hard",   school="Paya Lebar MGS", marks=2,
         text="Which of the following is NOT an equivalent fraction of 1/4?",
         type="mcq", opts=["A.  2/8", "B.  3/12", "C.  4/12", "D.  5/20"], answer="C.  4/12"),
    dict(id=8,  topic="Fractions",          difficulty="Hard",   school="St Hilda's",     marks=3,
         text="A tank is 3/8 filled with water. 120 litres more are needed to fill it completely.\nWhat is the capacity of the tank?",
         type="short", answer="192 litres"),
    dict(id=9,  topic="Fractions",          difficulty="Hard",   school="St Hilda's",     marks=3,
         text="5/6 of the people at a carnival were children and the rest were adults.\nThere were 240 more children than adults.\nHow many people were there altogether?",
         type="short", answer="360"),
    dict(id=10, topic="Angles & Geometry",  difficulty="Medium", school="Red Swastika",   marks=2,
         text="In square ABCD, two lines from corner D make angles of 24 degrees and 35 degrees\nwith side DC. Find angle y (the angle between the two lines).",
         type="short", answer="31 degrees"),
    dict(id=11, topic="Angles & Geometry",  difficulty="Medium", school="St Hilda's",     marks=2,
         text="Angle EFG = 134 degrees. Draw the angle with the given line EF. Mark and label the angle.",
         type="draw", answer="Obtuse angle, 134 degrees"),
    dict(id=12, topic="Angles & Geometry",  difficulty="Medium", school="Rosyth",         marks=2,
         text="Ahmad walked directly from point A to point D in a straight line on a grid.\nD is one square up and one square to the left of A.\nIn which direction did Ahmad walk?",
         type="short", answer="North-West"),
    dict(id=13, topic="Whole Numbers",      difficulty="Easy",   school="Rosyth",         marks=1,
         text="Round 25 571 to the nearest hundred.",
         type="short", answer="25 600"),
    dict(id=14, topic="Whole Numbers",      difficulty="Medium", school="Rosyth",         marks=2,
         text="A number is 15 000 when rounded to the nearest thousand.\nWhat is the greatest possible value of the number?",
         type="short", answer="15 499"),
    dict(id=15, topic="Whole Numbers",      difficulty="Medium", school="Rosyth",         marks=2,
         text="Find the quotient and remainder when 4505 is divided by 6.",
         type="short", answer="Quotient: 750, Remainder: 5"),
    dict(id=16, topic="Whole Numbers",      difficulty="Medium", school="Paya Lebar MGS", marks=2,
         text="Using ALL the digits 5, 2, 7, 0, 4 — form the largest possible 5-digit number.",
         type="short", answer="75 420"),
    dict(id=17, topic="Decimals",           difficulty="Medium", school="Red Swastika",   marks=2,
         text="A number has 2 decimal places. It is 34.7 when rounded to 1 decimal place.\nWhat is the smallest possible value of the number?",
         type="mcq", opts=["A.  34.60", "B.  34.65", "C.  34.70", "D.  34.74"], answer="B.  34.65"),
    dict(id=18, topic="Decimals",           difficulty="Medium", school="Paya Lebar MGS", marks=2,
         text="What is the value of 4 divided by 7? Give your answer correct to 1 decimal place.",
         type="short", answer="0.6"),
    dict(id=19, topic="Data & Tables",      difficulty="Medium", school="St Hilda's",     marks=2,
         text="A table shows P4 students across 3 classes.\n4A: total 38, wear spectacles 15\n4B: total 41, do not wear spectacles 19\n4C: total 40, wear spectacles 27\n\nHow many students in 4B wear spectacles?",
         type="short", answer="22"),
    dict(id=20, topic="Data & Tables",      difficulty="Medium", school="Paya Lebar MGS", marks=2,
         text="The table shows times P4 students jog per week:\n1 time = 61 students, 2 times = 50, 3 times = 42, 4 times = 75, 5 times = 80.\n\nHow many students jogged more than 2 times in a week?",
         type="short", answer="197"),
    dict(id=21, topic="Word Problems",      difficulty="Hard",   school="Rosyth",         marks=4,
         text="Janice had twice as many stamps as Kenneth at first.\nAfter Kenneth gave away 24 stamps, Janice had 5 times as many stamps as Kenneth.\nHow many stamps did Kenneth have at first?",
         type="short", answer="40"),
    dict(id=22, topic="Word Problems",      difficulty="Hard",   school="Rosyth",         marks=4,
         text="Giresh had $108 more than Beng Huat.\nAfter both of them spent an equal amount of money to buy some stationery,\nthe amount of money Giresh had left was 3 times as much as Beng Huat.\nGiven that Giresh had $198 at first, how much did each of them spend?",
         type="short", answer="$36"),
]

DIFF_COLORS = {"Easy": (GBG, GREEN), "Medium": (ABG, AMBER), "Hard": (RBG, RED)}

# ── Styles ─────────────────────────────────────────────────────────────────────
def make_styles():
    return {
        "section":   ParagraphStyle("section",   fontName=BOLD_FONT, fontSize=11,
                                    textColor=NAVY, spaceBefore=14, spaceAfter=6),
        "qtext":     ParagraphStyle("qtext",     fontName=BODY_FONT, fontSize=10,
                                    textColor=colors.black, leading=15, spaceAfter=4),
        "qbold":     ParagraphStyle("qbold",     fontName=BOLD_FONT, fontSize=10,
                                    textColor=colors.black, leading=15, spaceAfter=4),
        "opt":       ParagraphStyle("opt",       fontName=BODY_FONT, fontSize=10,
                                    textColor=colors.black, leading=14, leftIndent=12),
        "ans_label": ParagraphStyle("ans_label", fontName=BODY_FONT, fontSize=9,
                                    textColor=MGRAY),
        "ans":       ParagraphStyle("ans",       fontName=BOLD_FONT, fontSize=10,
                                    textColor=GREEN),
        "footer":    ParagraphStyle("footer",    fontName=BODY_FONT, fontSize=8,
                                    textColor=MGRAY, alignment=TA_CENTER),
        "fl":        ParagraphStyle("fl",        fontName=BODY_FONT, fontSize=10,
                                    textColor=colors.black),
    }


# ── Build PDF ──────────────────────────────────────────────────────────────────
def build_pdf(output_path, selected_topics=None, include_answers=False):
    S = make_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    qs = [q for q in QUESTIONS if selected_topics is None or q["topic"] in selected_topics]
    total_marks = sum(q["marks"] for q in qs)
    story = []

    # ── Logo ───────────────────────────────────────────────────────────────────
    LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sgmaths_logo.png")
    logo_img = Image(LOGO_PATH, width=8*cm, height=2.2*cm, kind="proportional")
    story.append(logo_img)
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY))
    story.append(Spacer(1, 0.35*cm))

    # Name / Class / Date
    name_data = [[
        Paragraph("Name: ________________________________", S["fl"]),
        Paragraph("Class: __________", S["fl"]),
        Paragraph("Date: ______________", S["fl"]),
    ]]
    name_tbl = Table(name_data, colWidths=[8.5*cm, 4*cm, 5*cm])
    name_tbl.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(name_tbl)
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    # ── Questions by topic ─────────────────────────────────────────────────────
    current_topic = None
    q_counter = 0
    PAGE_W = 16.5*cm   # usable width inside margins

    def make_ans_box():
        """Right-aligned answer rectangle."""
        ans_row = Table(
            [[Paragraph("Answer:", S["ans_label"]), Paragraph("", S["ans_label"])]],
            colWidths=[2*cm, 4.5*cm]
        )
        ans_row.setStyle(TableStyle([
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",   (0,0), (-1,-1), 0),
            ("RIGHTPADDING",  (0,0), (-1,-1), 0),
            ("BOX",           (1,0), (1,0),   1, NAVY),
            ("TOPPADDING",    (1,0), (1,0),   15),
            ("BOTTOMPADDING", (1,0), (1,0),   15),
        ]))
        outer = Table([[Paragraph("", S["ans_label"]), ans_row]],
                      colWidths=[10*cm, 6.5*cm])
        outer.setStyle(TableStyle([
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ]))
        return outer

    for q in qs:
        if q["topic"] != current_topic:
            current_topic = q["topic"]
            story.append(Paragraph(current_topic.upper(), S["section"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=TEAL))
            story.append(Spacer(1, 0.2*cm))

        q_counter += 1
        diff_bg, diff_fg = DIFF_COLORS[q["difficulty"]]

        # ── Badge (right-side pill) ────────────────────────────────────────────
        badge = Paragraph(
            f"{q['difficulty']}  |  {q['marks']} mark{'s' if q['marks']>1 else ''}",
            ParagraphStyle("b", fontName=BODY_FONT, fontSize=8,
                           textColor=diff_fg, alignment=TA_CENTER))
        badge_tbl = Table([[badge]], colWidths=[3.2*cm])
        badge_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), diff_bg),
            ("ROUNDEDCORNERS",[4]),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))

        # ── Question text: Q-number bold-prefix, then inline fractions ─────────
        # All lines of the question rendered as MixedLine on single canvas pass
        TEXT_W = PAGE_W - 3.5*cm   # leave room for badge on first line
        all_lines = q["text"].split("\n")

        first_segs = _parse_segs(all_lines[0])
        first_line = MixedLine(first_segs, fsize=10,
                               bold_prefix=f"Q{q_counter}.",
                               leading=18)

        # First line + badge in a table (badge floats right, no padding interference)
        header_tbl = Table([[first_line, badge_tbl]],
                           colWidths=[TEXT_W + 0.3*cm, 3.2*cm])
        header_tbl.setStyle(TableStyle([
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",   (0,0), (-1,-1), 0),
            ("RIGHTPADDING",  (0,0), (-1,-1), 0),
            ("TOPPADDING",    (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))

        q_block = [header_tbl]

        # Remaining lines of question text
        for extra in all_lines[1:]:
            if extra.strip():
                q_block.append(MixedLine(_parse_segs(extra), fsize=10, leading=16))
            else:
                q_block.append(Spacer(1, 0.2*cm))

        # ── MCQ options ────────────────────────────────────────────────────────
        if q["type"] == "mcq":
            q_block.append(Spacer(1, 0.1*cm))
            for opt in q["opts"]:
                q_block.append(MixedLine(_parse_segs(opt), fsize=10, leading=16))
            q_block.append(Spacer(1, 0.15*cm))
            q_block.append(make_ans_box())

        elif q["type"] == "draw":
            q_block.append(Spacer(1, 0.2*cm))
            draw_tbl = Table([[Paragraph("Drawing space:", S["ans_label"])]], colWidths=[PAGE_W])
            draw_tbl.setStyle(TableStyle([
                ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
                ("BACKGROUND",    (0,0), (-1,-1), LGRAY),
                ("TOPPADDING",    (0,0), (-1,-1), 40),
                ("BOTTOMPADDING", (0,0), (-1,-1), 40),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ]))
            q_block.append(draw_tbl)

        else:
            q_block.append(Spacer(1, 0.15*cm))
            work_tbl = Table(
                [[Paragraph("Working:", S["ans_label"])],
                 [Paragraph("", S["ans_label"])],
                 [Paragraph("", S["ans_label"])]],
                colWidths=[PAGE_W]
            )
            work_tbl.setStyle(TableStyle([
                ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
                ("BACKGROUND",    (0,0), (-1,-1), LGRAY),
                ("TOPPADDING",    (0,0), (-1,-1), 3),
                ("BOTTOMPADDING", (0,0), (-1,-1), 22),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ]))
            q_block.append(work_tbl)
            q_block.append(Spacer(1, 0.1*cm))
            q_block.append(make_ans_box())

        # ── Answer key ─────────────────────────────────────────────────────────
        if include_answers:
            ak_segs  = _parse_segs(str(q["answer"]))
            ak_line  = MixedLine(ak_segs, fsize=10, bold_prefix="Answer:", leading=18,
                                 color=GREEN)
            ak_outer = Table([[ak_line]], colWidths=[PAGE_W])
            ak_outer.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), GBG),
                ("BOX",           (0,0), (-1,-1), 0.5, HexColor("#86efac")),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ]))
            q_block.append(ak_outer)

        story.append(KeepTogether(q_block))
        story.append(Spacer(1, 0.4*cm))

    # ── Footer ──────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("sgmaths.sg  |  P4 Mathematics  |  End of Paper", S["footer"]))

    doc.build(story)
    print(f"PDF saved: {output_path}")


if __name__ == "__main__":
    build_pdf("sgmaths_p4_worksheet.pdf",         include_answers=False)
    build_pdf("sgmaths_p4_worksheet_answers.pdf", include_answers=True)
