from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, Image, KeepTogether, Flowable
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
import os, re

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

# ── Inline stacked fraction ───────────────────────────────────────────────────
class InlineFrac(Flowable):
    def __init__(self, num, den, whole=None, fsize=10, color=colors.black):
        super().__init__()
        self.num = str(num); self.den = str(den)
        self.whole = str(whole) if whole else None
        self.fsize = fsize; self.nsize = fsize * 0.72; self.color = color
        self._calc()
    def _calc(self):
        sw = lambda s, sz: stringWidth(s, BODY_FONT, sz)
        self.num_w  = sw(self.num, self.nsize); self.den_w = sw(self.den, self.nsize)
        self.frac_w = max(self.num_w, self.den_w) + 5
        self.whole_w = sw(self.whole + " ", self.fsize) if self.whole else 0
        self.width  = self.whole_w + self.frac_w + 3
        self.nh = self.nsize * 1.15; self.gap = 1.8
        self.height = self.nh * 2 + self.gap * 2 + 2
    def wrap(self, aw, ah): return self.width, self.height
    def draw(self):
        c = self.canv; c.saveState()
        c.setFillColor(self.color); c.setStrokeColor(self.color)
        x = 0; bar_y = self.nh + self.gap
        if self.whole:
            c.setFont(BODY_FONT, self.fsize)
            c.drawString(x, bar_y - self.fsize * 0.28, self.whole); x = self.whole_w
        c.setLineWidth(0.7); c.line(x, bar_y, x + self.frac_w, bar_y)
        c.setFont(BODY_FONT, self.nsize)
        c.drawString(x + (self.frac_w - self.num_w) / 2, bar_y + self.gap + 0.5, self.num)
        c.drawString(x + (self.frac_w - self.den_w) / 2, bar_y - self.nh - 0.5, self.den)
        c.restoreState()

FRAC_RE = re.compile(r'(\b\d+\s+)?([\d?□_]+[a-zA-Z]?[\d]*)\s*/\s*(\d+)')

def _parse_segs(line):
    segs, last = [], 0
    for m in FRAC_RE.finditer(line):
        pre = line[last:m.start()]
        if pre: segs.append(('text', pre))
        whole = m.group(1).strip() if m.group(1) else None
        segs.append(('frac', m.group(2), m.group(3), whole))
        last = m.end()
    tail = line[last:]
    if tail: segs.append(('text', tail))
    return segs or [('text', ' ')]

class MixedLine(Flowable):
    def __init__(self, segs, fsize=10, bold_prefix=None, color=colors.black, leading=16):
        super().__init__()
        self.segs = segs; self.fsize = fsize; self.nsize = fsize * 0.72
        self.color = color; self.leading = leading; self.bold_prefix = bold_prefix
        self._calc()
    def _frac_metrics(self, num, den, whole):
        sw = lambda s, sz: stringWidth(s, BODY_FONT, sz)
        nw = sw(num, self.nsize); dw = sw(den, self.nsize); fw = max(nw, dw) + 4
        ww = sw(whole + "\u2009", self.fsize) if whole else 0
        nh = self.nsize * 1.1; gap = 1.6
        return dict(nw=nw, dw=dw, fw=fw, ww=ww, nh=nh, gap=gap, total_w=ww + fw + 2)
    def _calc(self):
        bw = stringWidth(self.bold_prefix, BOLD_FONT, self.fsize) + 4 if self.bold_prefix else 0
        total_w = bw; has_frac = False
        for seg in self.segs:
            if seg[0] == 'text': total_w += stringWidth(seg[1], BODY_FONT, self.fsize)
            else:
                _, num, den, whole = seg
                total_w += self._frac_metrics(num, den, whole)['total_w']; has_frac = True
        self._has_frac = has_frac; self._bw = bw; self._total_w = total_w
        nh = self.nsize * 1.1; gap = 1.6
        frac_h = nh + gap + 0.7 + nh + gap
        self.height = max(self.leading, frac_h + 2) if has_frac else self.leading
    def wrap(self, aw, ah): self._aw = aw; return aw, self.height
    def draw(self):
        c = self.canv; c.saveState()
        c.setFillColor(self.color); c.setStrokeColor(self.color)
        baseline = self.height * 0.22; x = 0
        if self.bold_prefix:
            c.setFont(BOLD_FONT, self.fsize)
            c.drawString(x, baseline, self.bold_prefix + " "); x += self._bw
        for seg in self.segs:
            if seg[0] == 'text':
                c.setFont(BODY_FONT, self.fsize)
                c.drawString(x, baseline, seg[1])
                x += stringWidth(seg[1], BODY_FONT, self.fsize)
            else:
                _, num, den, whole = seg
                m = self._frac_metrics(num, den, whole)
                nh = m['nh']; gap = m['gap']; fw = m['fw']; nw = m['nw']; dw = m['dw']
                if whole:
                    c.setFont(BODY_FONT, self.fsize); c.drawString(x, baseline, whole); x += m['ww']
                bar_y = baseline + self.fsize * 0.30
                c.setLineWidth(0.65); c.line(x, bar_y, x + fw, bar_y)
                c.setFont(BODY_FONT, self.nsize)
                c.drawString(x + (fw - nw) / 2, bar_y + gap, num)
                c.drawString(x + (fw - dw) / 2, bar_y - nh - 0.5, den)
                x += fw + 2
        c.restoreState()

def make_inline(text, style, fsize=10, total_width=13.3*cm, bold_prefix=None):
    result = []; leading = getattr(style, 'leading', fsize * 1.4)
    for line in text.split('\n'):
        segs = _parse_segs(line); has_frac = any(s[0] == 'frac' for s in segs)
        if not has_frac and not bold_prefix:
            result.append(Paragraph(line or ' ', style))
        else:
            result.append(MixedLine(segs, fsize=fsize,
                                    bold_prefix=bold_prefix if result == [] else None,
                                    leading=leading))
    return result

# ── Question banks ────────────────────────────────────────────────────────────

P1_QUESTIONS = [
    # Numbers to 10
    dict(id=1,  topic="Numbers to 10", difficulty="Easy", school="Henry Park", marks=1,
         text="Count and write the number of balls in the box.",
         diagram=("P1", 1),
         type="short", answer="6"),
    dict(id=2,  topic="Numbers to 10", difficulty="Easy", school="Henry Park", marks=1,
         text="Count and write the number of dots in words.",
         diagram=("P1", 2),
         type="short", answer="eight"),
    dict(id=3,  topic="Numbers to 10", difficulty="Easy", school="Henry Park", marks=1,
         text="Which set has more?\n\nSet ___ has more.",
         diagram=("P1", 3),
         type="short", answer="Set A"),
    dict(id=4,  topic="Numbers to 10", difficulty="Easy", school="Henry Park", marks=1,
         text="Count the number of objects in the pictures.\nCompare and write the numbers in the boxes.\n\n___ is smaller than ___.",
         diagram=("P1", 4),
         type="short", answer="3 is smaller than 8"),
    # Addition
    dict(id=5,  topic="Addition & Subtraction", difficulty="Easy", school="Henry Park", marks=1,
         text="Fill in the box with the correct answer.\n\n5 + 4 =",
         diagram=("P1", 5),
         type="short", answer="9"),
    dict(id=6,  topic="Addition & Subtraction", difficulty="Easy", school="Henry Park", marks=1,
         text="Use the numbers below to form an addition equation.\n\n___ + ___ = ___",
         diagram=("P1", 6),
         type="short", answer="7 + 3 = 10"),
    dict(id=7,  topic="Addition & Subtraction", difficulty="Easy", school="Henry Park", marks=1,
         text="Write the correct number in the box.\n\n4 + ___ = 7",
         type="short", answer="3"),
    dict(id=8,  topic="Addition & Subtraction", difficulty="Easy", school="Henry Park", marks=1,
         text="6 - 2 =",
         diagram=("P1", 8),
         type="short", answer="4"),
    dict(id=9,  topic="Addition & Subtraction", difficulty="Easy", school="Henry Park", marks=1,
         text="Complete the subtraction equation.\n\n8 - ___ = 5",
         diagram=("P1", 9),
         type="short", answer="3"),
    dict(id=10, topic="Addition & Subtraction", difficulty="Easy", school="Henry Park", marks=1,
         text="Write the number sentence for the following picture.\n\n___ - ___ = ___",
         diagram=("P1", 10),
         type="short", answer="10 - 4 = 6"),
    dict(id=11, topic="Addition & Subtraction", difficulty="Easy", school="Henry Park", marks=1,
         text="Circle the cloud that has the same answer as 4 + 6.",
         diagram=("P1", 11),
         type="short", answer="2 + 8"),
    # Word Problems
    dict(id=12, topic="Word Problems", difficulty="Easy", school="Henry Park", marks=1,
         text="Mother bakes 7 cupcakes.\n5 cupcakes are eaten by her children.\nHow many cupcakes are left?\n\nThere are ___ cupcakes left.",
         diagram=("P1", 12),
         type="short", answer="2"),
    dict(id=13, topic="Numbers to 10", difficulty="Easy", school="Henry Park", marks=1,
         text="Study the number pattern below.\n\nThe missing number is ___.",
         diagram=("P1", 13),
         type="short", answer="5"),
    dict(id=14, topic="Word Problems", difficulty="Easy", school="Henry Park", marks=1,
         text="Julie has 6 stickers on her book.\nHer mother puts 1 more sticker on her book.\nHow many stickers does Julie have now?\n\n___ + ___ = ___\n\nJulie has ___ stickers now.",
         type="short", answer="7"),
    dict(id=15, topic="Word Problems", difficulty="Easy", school="Henry Park", marks=1,
         text="Harry has 4 toy cars and 2 toy trains.\nHow many toys does he have altogether?\n\n___ + ___ = ___\n\nHarry has ___ toys altogether.",
         type="short", answer="6"),
    dict(id=16, topic="Word Problems", difficulty="Easy", school="Henry Park", marks=1,
         text="There are 9 pencils altogether.\n6 pencils are short.\nHow many pencils are longer?\n\n___ - ___ = ___\n\n___ pencils are longer.",
         type="short", answer="3"),
]

P2_QUESTIONS = [
    # ── Numbers to 1000 ────────────────────────────────────────────────────────
    dict(id=1,  topic="Numbers to 1000", difficulty="Easy", school="Rosyth", marks=1,
         text="In 652, the digit ___ is in the ones place.",
         type="mcq",
         opts=["(1)  1", "(2)  2", "(3)  5", "(4)  6"],
         answer="(2)  2"),
    dict(id=2,  topic="Numbers to 1000", difficulty="Easy", school="Rosyth", marks=1,
         text="What is the missing number in the pattern?\n145,  165,  ___,  205,  225",
         type="mcq",
         opts=["(1)  170", "(2)  175", "(3)  185", "(4)  200"],
         answer="(3)  185"),
    dict(id=7,  topic="Numbers to 1000", difficulty="Easy", school="Rosyth", marks=1,
         text="Write seven hundred and thirteen in numerals.",
         type="short", answer="713"),
    dict(id=8,  topic="Numbers to 1000", difficulty="Easy", school="Rosyth", marks=1,
         text="Add 10 tens to 880. The answer is ___.",
         type="short", answer="980"),
    dict(id=9,  topic="Numbers to 1000", difficulty="Easy", school="Rosyth", marks=1,
         text="10 less than 596 is ___.",
         type="short", answer="586"),
    # ── Addition & Subtraction within 1000 ─────────────────────────────────────
    dict(id=3,  topic="Addition & Subtraction", difficulty="Easy", school="Rosyth", marks=1,
         text="32 + 544 = ___",
         type="mcq",
         opts=["(1)  512", "(2)  516", "(3)  576", "(4)  864"],
         answer="(2)  576"),
    dict(id=4,  topic="Addition & Subtraction", difficulty="Easy", school="Rosyth", marks=1,
         text="267 − 132 = ___",
         type="mcq",
         opts=["(1)  135", "(2)  199", "(3)  335", "(4)  399"],
         answer="(1)  135"),
    dict(id=5,  topic="Addition & Subtraction", difficulty="Easy", school="Rosyth", marks=1,
         text="Subtract 438 from 908. The answer is ___.",
         type="mcq",
         opts=["(1)  470", "(2)  500", "(3)  530", "(4)  538"],
         answer="(1)  470"),
    dict(id=6,  topic="Addition & Subtraction", difficulty="Easy", school="Rosyth", marks=1,
         text="Find the sum of 365 and 329. The answer is ___.",
         type="mcq",
         opts=["(1)  36", "(2)  44", "(3)  684", "(4)  694"],
         answer="(4)  694"),
    dict(id=10, topic="Addition & Subtraction", difficulty="Easy", school="Rosyth", marks=1,
         text="Find the difference between 502 and 348.",
         type="short", answer="154"),
    dict(id=11, topic="Addition & Subtraction", difficulty="Medium", school="Rosyth", marks=1,
         text="Fill in the blanks.\n\n  Hundreds | Tens | Ones\n     2     |  6   | ___\n  +  6     | ___  |  2\n  ─────────────────────\n     9     |  1   |  1",
         type="short", answer="Ones: 9,  Tens: 4"),
    dict(id=12, topic="Addition & Subtraction", difficulty="Medium", school="Rosyth", marks=1,
         text="Which two numbers below add up to 374?\n324,  334,  50,  60\n\n___ + ___ = 374",
         type="short", answer="324 + 50 = 374"),
    # ── Word Problems ───────────────────────────────────────────────────────────
    dict(id=13, topic="Word Problems", difficulty="Easy", school="Rosyth", marks=1,
         text="Uncle Samy delivered 127 pizzas in the afternoon.\nHe delivered 60 pizzas at night.\nHow many pizzas did Uncle Samy deliver altogether?",
         type="short", answer="187 pizzas"),
    dict(id=14, topic="Word Problems", difficulty="Easy", school="Rosyth", marks=1,
         text="Mrs Koh baked 758 cookies for Christmas.\nShe gave 446 cookies to her friends.\nHow many cookies did she have left?",
         type="short", answer="312 cookies"),
    dict(id=15, topic="Word Problems", difficulty="Medium", school="Rosyth", marks=2,
         text="There are 527 books on a shelf.\nThe librarian puts 283 more books on the shelf.\nHow many books are there altogether on the shelf?",
         type="short", answer="810 books"),
    dict(id=16, topic="Word Problems", difficulty="Medium", school="Rosyth", marks=2,
         text="A shop sold 56 toy cars.\nThere were 651 toy cars left in the shop.\nHow many toy cars did the shop have at first?",
         type="short", answer="707 toy cars"),
    dict(id=17, topic="Word Problems", difficulty="Medium", school="Rosyth", marks=2,
         text="Siti has 499 buttons.\nShe has 194 more buttons than Amy.\nHow many buttons does Amy have?",
         type="short", answer="305 buttons"),
]

P3_QUESTIONS = [
    # Multiplication & Division
    dict(id=1,  topic="Multiplication & Division", difficulty="Easy",   school="Nan Hua",    marks=1,
         text="6 fours is the same as ___.",
         type="mcq", opts=["A.  6 + 6 + 6 + 6", "B.  6 x 6 x 6 x 6", "C.  4 x 4 x 4 x 4 x 4 x 4", "D.  4 + 4 + 4 + 4 + 4 + 4"], answer="D.  4 + 4 + 4 + 4 + 4 + 4"),
    dict(id=2,  topic="Multiplication & Division", difficulty="Easy",   school="Nan Hua",    marks=1,
         text="5 x 7 is 14 more than ___.",
         type="mcq", opts=["A.  2 x 7", "B.  3 x 7", "C.  4 x 7", "D.  7 x 7"], answer="B.  3 x 7"),
    dict(id=3,  topic="Multiplication & Division", difficulty="Easy",   school="Nan Hua",    marks=1,
         text="Bala bought a roll of string that is 420 cm long. He cut the string equally into 7 cm long pieces. How many pieces of 7 cm string did he get?",
         type="mcq", opts=["A.  6", "B.  8", "C.  60", "D.  80"], answer="C.  60"),
    dict(id=4,  topic="Multiplication & Division", difficulty="Easy",   school="Nan Hua",    marks=1,
         text="Liming has 65 curry puffs. He packs 9 curry puffs in each container. How many containers does he need to pack all the curry puffs?",
         type="mcq", opts=["A.  5", "B.  6", "C.  7", "D.  8"], answer="D.  8"),
    dict(id=5,  topic="Multiplication & Division", difficulty="Medium",  school="Nan Hua",    marks=2,
         text="Look at the number pattern. What is the missing number?",
         diagram=("P3", 5),
         type="mcq", opts=["A.  12", "B.  15", "C.  22", "D.  24"], answer="D.  24"),
    dict(id=55, topic="Multiplication & Division", difficulty="Medium",  school="Nan Hua",    marks=2,
         text="Find the quotient and remainder when 803 is divided by 5.",
         type="short", answer="Quotient: 160, Remainder: 3"),
    dict(id=6,  topic="Multiplication & Division", difficulty="Medium",  school="Nan Hua",    marks=2,
         text="Six children visited the chocolate factory. Mr Wonka gave eight chocolate candies to each child and kept four for himself. How many chocolate candies did he have at first?",
         type="short", answer="52"),
    dict(id=7,  topic="Multiplication & Division", difficulty="Hard",   school="Henry Park", marks=2,
         text="Mr Bala prepared some gift bags. He packed 4 pens and 7 stickers in each gift bag. There was a total of 144 pens in the gift bags.\n(a) How many gift bags did he prepare?\n(b) How many stickers were there altogether?",
         type="short", answer="(a) 36 bags  (b) 252 stickers"),
    dict(id=8,  topic="Multiplication & Division", difficulty="Hard",   school="Nan Hua",    marks=3,
         text="Charlie and Augustus made 90 paper planes. Augustus made 5 times as many paper planes as Charlie. How many more paper planes did Augustus make than Charlie?",
         type="short", answer="60"),
    # Fractions
    dict(id=9,  topic="Fractions", difficulty="Easy",   school="Henry Park", marks=1,
         text="5/9 = __/72. What is the missing numerator?",
         type="mcq", opts=["A.  10", "B.  18", "C.  40", "D.  68"], answer="C.  40"),
    dict(id=10, topic="Fractions", difficulty="Medium",  school="Maha Bodhi", marks=2,
         text="Write 14/42 in its simplest form.",
         type="short", answer="1/3"),
    dict(id=11, topic="Fractions", difficulty="Medium",  school="Maha Bodhi", marks=2,
         text="Arrange these fractions from greatest to smallest: 1/2, 3/8, 7/9.",
         type="mcq", opts=["A.  3/8, 1/2, 7/9", "B.  1/2, 3/8, 7/9", "C.  7/9, 1/2, 3/8", "D.  7/9, 3/8, 1/2"], answer="C.  7/9, 1/2, 3/8"),
    dict(id=12, topic="Fractions", difficulty="Medium",  school="Henry Park", marks=1,
         text="Arrange the fractions in order, beginning with the smallest: 7/12, 3/7, 1/2.",
         type="short", answer="7/12, 3/7, 1/2"),
    dict(id=13, topic="Fractions", difficulty="Medium",  school="Maha Bodhi", marks=2,
         text="Amber ate 1/8 of a pizza and Danny ate 1/4 of the same pizza.\nWhat fraction of the pizza was left?",
         type="short", answer="5/8"),
    dict(id=14, topic="Fractions", difficulty="Medium",  school="Maha Bodhi", marks=2,
         text="What is the missing fraction in the box?\n___ + 1/10 = 2/5",
         type="short", answer="3/10"),
    dict(id=15, topic="Fractions", difficulty="Hard",   school="Henry Park", marks=2,
         text="Siti spent 1/5 of her money on a cake and some of her money on a cookie.\nAfter buying both items, she had 3/10 of her money left.\nWhat fraction of her money did she spend on the cookie? Express your answer in simplest form.",
         type="short", answer="1/2"),
    # Angles & Lines
    dict(id=16, topic="Angles & Lines", difficulty="Easy",   school="Maha Bodhi", marks=2,
         text="How many acute angles are there inside a pentagon-like figure with 2 acute angles at the bottom?",
         type="mcq", opts=["A.  6", "B.  2", "C.  3", "D.  4"], answer="B.  2"),
    dict(id=17, topic="Angles & Lines", difficulty="Medium",  school="Henry Park", marks=1,
         text="In the figure shown, how many of the marked angles are obtuse angles?",
         diagram=("P3", 17),
         type="short", answer="4"),
    dict(id=18, topic="Angles & Lines", difficulty="Medium",  school="Maha Bodhi", marks=2,
         text="A line PQ is drawn in the square grid. Draw a line parallel to PQ passing through point R.\nHow many right angles does the shape in Q7 have?",
         diagram=("P3", 18),
         type="short", answer="2"),
    dict(id=19, topic="Angles & Lines", difficulty="Medium",  school="Henry Park", marks=1,
         text="Which of the following figures have more than 2 right angles?",
         diagram=("P3", 19),
         type="mcq", opts=["A.  (d) only", "B.  (a) and (d) only", "C.  (d) and (e) only", "D.  (a), (b) and (c) only"], answer="B.  (a) and (d) only"),
    dict(id=20, topic="Angles & Lines", difficulty="Medium",  school="Henry Park", marks=1,
         text="Identify the pair of parallel lines in a figure with lines AB, BC, AF, ED and DC on a grid.",
         diagram=("P3", 20),
         type="mcq", opts=["A.  AB // DC", "B.  AF // BC", "C.  AF // ED", "D.  BC // ED"], answer="C.  AF // ED"),
    # Data & Graphs
    dict(id=21, topic="Data & Graphs", difficulty="Medium",  school="Nan Hua",    marks=2,
         text="The graph shows the number of times P1 pupils went to the library during the June holidays. Study the graph carefully and answer the question below.\nHow many P1 pupils went to the library more than 3 times?",
         diagram=("P3", 6),
         type="mcq", opts=["A.  65", "B.  145", "C.  180", "D.  245"], answer="A.  65"),
    dict(id=22, topic="Data & Graphs", difficulty="Medium",  school="Nan Hua",    marks=2,
         text="The graph shows the number of hair dryers sold at Sunshine Shop in 5 days.\nStudy the graph carefully and answer the questions (a) and (b).\n(a) Which day had the most number of hair dryers sold?\n(b) How many more Brand A hair dryers were sold compared to Brand B?",
         diagram=("P3", 9),
         type="short", answer="(a) Thursday  (b) 13"),
    dict(id=23, topic="Data & Graphs", difficulty="Medium",  school="Henry Park", marks=2,
         text="The bar graph shows the number of fruits sold by Grocer Pan.\n(a) How many apples and durians did Grocer Pan sell in total?\n(b) Grocer Pan sold twice as many watermelons as peaches. How many watermelons were sold?",
         diagram=("P3", 23),
         type="short", answer="(a) 75  (b) 30"),
    dict(id=24, topic="Data & Graphs", difficulty="Medium",  school="Maha Bodhi", marks=2,
         text="A bar graph shows paper clips in four boxes: Box A=12, Box B=44, Box C=32, Box D=20.\nHow many paper clips must be taken from Box B and placed in Box D so that the two boxes have the same number?",
         diagram=("P3", 24),
         type="short", answer="12"),
    # Word Problems
    dict(id=25, topic="Word Problems", difficulty="Medium",  school="Nan Hua",    marks=3,
         text="580 people visited the cinema on a weekend. There were 168 fewer people who visited on Sunday than on Saturday. How many people visited the cinema on Sunday?",
         type="short", answer="206"),
    dict(id=26, topic="Word Problems", difficulty="Hard",   school="Maha Bodhi", marks=3,
         text="Mr Lim packed some muffins and fruit tarts into boxes.\nHe packed 3 muffins and 6 fruit tarts into each box.\nThere was a total of 174 fruit tarts in all the boxes.\nHow many muffins did Mr Lim pack altogether?",
         type="short", answer="87"),
    dict(id=27, topic="Word Problems", difficulty="Hard",   school="Maha Bodhi", marks=3,
         text="Marvin had 278 more cards than Sally at first.\nAfter Sally gave 87 cards to Marvin, Marvin had 3 times as many cards as Sally.\nHow many cards did Sally have in the end?",
         type="short", answer="226"),
    dict(id=28, topic="Word Problems", difficulty="Hard",   school="Henry Park",  marks=3,
         text="A school had some flags for National Day. The school gave out 378 flags to students. After that, the school bought another 1386 flags. In the end, there were 2953 flags altogether. How many flags did the school have at first?",
         type="short", answer="1945"),
    dict(id=29, topic="Word Problems", difficulty="Hard",   school="Henry Park",  marks=2,
         text="Leo bought a toy car that cost $13.85. He paid an additional $1.50 for a box.\n(a) How much did he spend in all?\n(b) He paid with two $10 notes. How much change did he receive?",
         type="short", answer="(a) $15.35  (b) $4.65"),
]

P4_QUESTIONS = [
    dict(id=1,  topic="Fractions",         difficulty="Easy",   school="St Hilda's",     marks=1,
         text="Express 26/7 as a mixed number.",
         type="mcq", opts=["A.  2 6/7", "B.  3 5/7", "C.  5 3/7", "D.  7 3/5"], answer="B.  3 5/7"),
    dict(id=2,  topic="Fractions",         difficulty="Easy",   school="St Hilda's",     marks=1,
         text="What is 2/9 of 18?",
         type="mcq", opts=["A.  1", "B.  81", "C.  162", "D.  4"], answer="D.  4"),
    dict(id=3,  topic="Fractions",         difficulty="Medium", school="St Hilda's",     marks=2,
         text="Find the difference between 3/5 and 2/3.",
         type="mcq", opts=["A.  1/15", "B.  1/2", "C.  5/8", "D.  19/15"], answer="A.  1/15"),
    dict(id=4,  topic="Fractions",         difficulty="Medium", school="Red Swastika",   marks=2,
         text="Write 15/7 as a mixed number.",
         type="short", answer="2 1/7"),
    dict(id=5,  topic="Fractions",         difficulty="Medium", school="Red Swastika",   marks=2,
         text="Express 0.75 as a fraction in its simplest form.",
         type="short", answer="3/4"),
    dict(id=6,  topic="Fractions",         difficulty="Medium", school="Rosyth",         marks=2,
         text="Find the value of 11/12 - 2/3 in its simplest form.",
         type="short", answer="1/4"),
    dict(id=7,  topic="Fractions",         difficulty="Hard",   school="Paya Lebar MGS", marks=2,
         text="Which of the following is NOT an equivalent fraction of 1/4?",
         type="mcq", opts=["A.  2/8", "B.  3/12", "C.  4/12", "D.  5/20"], answer="C.  4/12"),
    dict(id=8,  topic="Fractions",         difficulty="Hard",   school="St Hilda's",     marks=3,
         text="A tank is 3/8 filled with water. 120 litres more are needed to fill it completely.\nWhat is the capacity of the tank?",
         type="short", answer="192 litres"),
    dict(id=9,  topic="Fractions",         difficulty="Hard",   school="St Hilda's",     marks=3,
         text="5/6 of the people at a carnival were children and the rest were adults.\nThere were 240 more children than adults.\nHow many people were there altogether?",
         type="short", answer="360"),
    dict(id=10, topic="Angles & Geometry", difficulty="Medium", school="Red Swastika",   marks=2,
         text="In square ABCD, two lines from corner D make angles of 24 degrees and 35 degrees with side DC. Find angle y (the angle between the two lines).",
         type="short", answer="31 degrees"),
    dict(id=11, topic="Angles & Geometry", difficulty="Medium", school="St Hilda's",     marks=2,
         text="Angle EFG = 134 degrees. Draw the angle with the given line EF. Mark and label the angle.",
         type="draw", answer="Obtuse angle, 134 degrees"),
    dict(id=12, topic="Angles & Geometry", difficulty="Medium", school="Rosyth",         marks=2,
         text="Ahmad walked directly from point A to point D in a straight line on a grid.\nD is one square up and one square to the left of A.\nIn which direction did Ahmad walk?",
         type="short", answer="North-West"),
    dict(id=13, topic="Whole Numbers",     difficulty="Easy",   school="Rosyth",         marks=1,
         text="Round 25 571 to the nearest hundred.",
         type="short", answer="25 600"),
    dict(id=14, topic="Whole Numbers",     difficulty="Medium", school="Rosyth",         marks=2,
         text="A number is 15 000 when rounded to the nearest thousand.\nWhat is the greatest possible value of the number?",
         type="short", answer="15 499"),
    dict(id=15, topic="Whole Numbers",     difficulty="Medium", school="Rosyth",         marks=2,
         text="Find the quotient and remainder when 4505 is divided by 6.",
         type="short", answer="Quotient: 750, Remainder: 5"),
    dict(id=16, topic="Whole Numbers",     difficulty="Medium", school="Paya Lebar MGS", marks=2,
         text="Using ALL the digits 5, 2, 7, 0, 4 — form the largest possible 5-digit number.",
         type="short", answer="75 420"),
    dict(id=17, topic="Decimals",          difficulty="Medium", school="Red Swastika",   marks=2,
         text="A number has 2 decimal places. It is 34.7 when rounded to 1 decimal place.\nWhat is the smallest possible value of the number?",
         type="mcq", opts=["A.  34.60", "B.  34.65", "C.  34.70", "D.  34.74"], answer="B.  34.65"),
    dict(id=18, topic="Decimals",          difficulty="Medium", school="Paya Lebar MGS", marks=2,
         text="What is the value of 4 divided by 7? Give your answer correct to 1 decimal place.",
         type="short", answer="0.6"),
    dict(id=19, topic="Data & Tables",     difficulty="Medium", school="St Hilda's",     marks=2,
         text="A table shows P4 students across 3 classes.\n4A: total 38, wear spectacles 15\n4B: total 41, do not wear spectacles 19\n4C: total 40, wear spectacles 27\n\nHow many students in 4B wear spectacles?",
         type="short", answer="22"),
    dict(id=20, topic="Data & Tables",     difficulty="Medium", school="Paya Lebar MGS", marks=2,
         text="The table shows times P4 students jog per week:\n1 time=61, 2 times=50, 3 times=42, 4 times=75, 5 times=80.\n\nHow many students jogged more than 2 times in a week?",
         type="short", answer="197"),
    dict(id=21, topic="Word Problems",     difficulty="Hard",   school="Rosyth",         marks=4,
         text="Janice had twice as many stamps as Kenneth at first.\nAfter Kenneth gave away 24 stamps, Janice had 5 times as many stamps as Kenneth.\nHow many stamps did Kenneth have at first?",
         type="short", answer="40"),
    dict(id=22, topic="Word Problems",     difficulty="Hard",   school="Rosyth",         marks=4,
         text="Giresh had $108 more than Beng Huat.\nAfter both of them spent an equal amount of money to buy some stationery,\nthe amount of money Giresh had left was 3 times as much as Beng Huat.\nGiven that Giresh had $198 at first, how much did each of them spend?",
         type="short", answer="$36"),
]

P5_QUESTIONS = [
    # ── Triangles & Area ────────────────────────────────────────────────────────
    dict(id=1, topic="Triangles & Area", difficulty="Easy", school="Raffles Girls'", marks=1,
         text="VWX is a triangle. If the base is VX, the height is ___.\n(Refer to diagram for points W, Z, V, Y, X.)",
         image="img_p5_q1a_triangle.png",
         type="short", answer="YW"),
    dict(id=2, topic="Triangles & Area", difficulty="Easy", school="Raffles Girls'", marks=1,
         text="DCB is a straight line.\nD is 3 cm to the left of C, and C is 9 cm to the left of B.\nA is 5 cm above D. Find the area of triangle ABC.",
         image="img_p5_q1b_triangle.png",
         type="short", answer="22.5 cm²"),
    dict(id=3, topic="Triangles & Area", difficulty="Medium", school="Raffles Girls'", marks=2,
         text="ABCD is a square of side 18 m. E is the midpoint of AB and F is the midpoint of DC.\nFind the total area of the shaded parts.",
         image="img_p5_q8_square.png",
         type="short", answer="162 m²"),
    dict(id=4, topic="Triangles & Area", difficulty="Hard", school="Raffles Girls'", marks=4,
         text="The figure is made up of a rectangle ABFG and a square CDEF.\nAH = HG and GF = FE.\nFind the area of the shaded part.",
         image="img_p5_q9_rect.png",
         type="short", answer="252 cm²"),
    dict(id=5, topic="Triangles & Area", difficulty="Medium", school="Ai Tong", marks=2,
         text="Find the area of the shaded triangle with base 25 m and perpendicular height 16 m.\n(Note: The 15 m and 4 m are other sides, not the height.)",
         image="img_p5_aitong_q5_triangle.png", img_height=4.5,
         type="short", answer="200 m²"),
    dict(id=6, topic="Triangles & Area", difficulty="Hard", school="Ai Tong", marks=4,
         text="Rectangle ACEH is made up of two identical rectangles BCDK and KDEF and two identical squares ABKJ and JKFH.\nAC = 21 cm and DE = 6 cm.\n(a) Find the area of triangle GKD.\n(b) Find the total area of the shaded parts.",
         image="img_p5_aitong_q6_aceh.png", img_height=5.5,
         type="short", answer="(a) 45 cm²  (b) 162 cm²"),
    # ── Volume ──────────────────────────────────────────────────────────────────
    dict(id=7, topic="Volume", difficulty="Easy", school="Raffles Girls'", marks=1,
         text="Find the volume of the cube shown.",
         image="img_p5_q2a_cube.png",
         type="short", answer="343 cm³"),
    dict(id=8, topic="Volume", difficulty="Easy", school="Raffles Girls'", marks=1,
         text="The figure shows some cubes in a glass tank.\nThe tank is 5 cubes long, 3 cubes wide and 3 cubes tall. 25 cubes are already placed.\nHow many more cubes are needed to fill the tank completely?",
         image="img_p5_q2b_tank.png",
         type="short", answer="20"),
    dict(id=9, topic="Volume", difficulty="Medium", school="Raffles Girls'", marks=2,
         text="The figure shows a solid made up of 1-cm cubes.\nHow many more cubes must be added to make a solid of 30 cm³?",
         image="img_p5_q6_solid.png",
         type="short", answer="18"),
    dict(id=10, topic="Volume", difficulty="Hard", school="Raffles Girls'", marks=5,
         text="The figure shows a rectangular tank P and an empty cubical tank Q.\nTank P was 1/5 filled with water. Johan then poured another 1.3 l into tank P.\n(a) What was the total volume of water in tank P?\n(b) Johan poured all the water from tank P into tank Q.\nHow much more water was needed to fill tank Q? Leave your answer in litres.",
         image="img_p5_q10_tanks.png",
         type="short", answer="(a) 3.892 l  (b) 1.94 l"),
    dict(id=11, topic="Volume", difficulty="Easy", school="Ai Tong", marks=2,
         text="The cuboid has a height of 8 cm and a square base of side 3 cm. Find its volume.",
         image="img_p5_aitong_q11_cuboid.png", img_height=4.0,
         type="short", answer="72 cm³"),
    dict(id=12, topic="Volume", difficulty="Hard", school="Ai Tong", marks=3,
         text="At a party, a rectangular container (45 cm × 38 cm × 40 cm) was 5/8 filled with fruit punch.\nEach guest was served a 550 ml cup of fruit punch.\nWhat was the greatest possible number of cups served?",
         image="img_p5_aitong_q12_container.png", img_height=5.0,
         type="short", answer="77 cups"),
    # ── Decimals & Measurement ─────────────────────────────────────────────────
    dict(id=13, topic="Decimals & Measurement", difficulty="Easy", school="Raffles Girls'", marks=1,
         text="Write down a decimal between 6.2 and 6.3.",
         type="short", answer="Any decimal such as 6.21, 6.25, etc."),
    dict(id=14, topic="Decimals & Measurement", difficulty="Easy", school="Raffles Girls'", marks=1,
         text="Arrange these decimals from the smallest to the largest:\n1.09,  1.609,  1.069",
         type="short", answer="1.069,  1.09,  1.609"),
    dict(id=15, topic="Decimals & Measurement", difficulty="Easy", school="Raffles Girls'", marks=1,
         text="Convert the following:\n(a) 21.5 m = ___ cm\n(b) 3 kg 80 g = ___ kg",
         type="short", answer="(a) 2150 cm  (b) 3.08 kg"),
    dict(id=16, topic="Decimals & Measurement", difficulty="Medium", school="Raffles Girls'", marks=2,
         text="Mr Bala bought 4.5 kg of meat. He packed them into smaller bags of 0.15 kg each.\nHow many bags of meat did he pack?",
         type="short", answer="30"),
    dict(id=17, topic="Decimals & Measurement", difficulty="Easy", school="Ai Tong", marks=2,
         text="(a) Express 6095 cm³ in l and ml.\n(b) Express 8 kg 20 g in kg.",
         type="short", answer="(a) 6 l 95 ml  (b) 8.02 kg"),
    dict(id=18, topic="Decimals & Measurement", difficulty="Easy", school="Ai Tong", marks=2,
         text="A wire is 2.5 m long. Some of it is used to form an equilateral triangle with each side 75 cm.\nWhat is the length of wire that is left unused?",
         type="short", answer="25 cm"),
    # ── 3D Solids & Views ───────────────────────────────────────────────────────
    dict(id=19, topic="3D Solids & Views", difficulty="Medium", school="Raffles Girls'", marks=2,
         text="Nisha built a solid using 10 unit cubes.\n(a) Draw the top view of the solid on the given square grid.\n(b) Nisha has 4 more unit cubes. What is the greatest number of unit cubes she can add without changing the top view and front view?",
         image="img_p5_q7_solid_grid.png",
         type="short", answer="(a) See diagram  (b) 2"),
    dict(id=20, topic="3D Solids & Views", difficulty="Medium", school="Ai Tong", marks=2,
         text="7 unit cubes were stacked and glued together to form a solid.\nDraw the side view and the top view of the solid on the grid provided.",
         image="img_p5_aitong_q20_cubes.png", img_height=13.0,
         type="draw", answer="Side view: 3 rows (3-wide, 2-wide, 1-wide). Top view: 3×1 + 1 extra = L-shape"),
    # ── Fractions (Word Problems) ───────────────────────────────────────────────
    dict(id=21, topic="Fractions", difficulty="Hard", school="Ai Tong", marks=3,
         text="In a competition, 3/5 of the participants were men.\n1/3 of the remaining participants were women and the rest were children.\nThere were 225 more men than children.\nHow many participants were there in the competition?",
         type="short", answer="675"),
    dict(id=22, topic="Fractions", difficulty="Hard", school="Ai Tong", marks=3,
         text="Amanda went shopping with some money.\nShe spent 1/3 of her money on a table, 1/4 of it on a sofa and $54 on a lamp.\nThen she had 1/6 of her money left.\nHow much did she spend on the table?",
         type="short", answer="$72"),
    # ── Word Problems ───────────────────────────────────────────────────────────
    dict(id=23, topic="Word Problems", difficulty="Medium", school="Raffles Girls'", marks=2,
         text="At a bookshop, pencils are sold in boxes of 12 for $9.60 and erasers in boxes of 7 for $3.50.\n(a) Mrs Lee needs 42 pencils and 20 erasers. What is the least amount she needs to spend?\n(b) Mr Ali bought 8 more pencils than erasers. The total number was fewer than 70. How much did he spend altogether?",
         image="img_p5_q11_pencils.png",
         type="short", answer="(a) $48.90  (b) $42.80"),
    dict(id=24, topic="Word Problems", difficulty="Medium", school="Ai Tong", marks=3,
         text="The cost of 2 pens and 4 files is $23.90. The cost of a file is $1.40 more than the cost of a pen.\nFind the cost of a pen.",
         type="short", answer="$3.05"),
    dict(id=25, topic="Word Problems", difficulty="Hard", school="Ai Tong", marks=5,
         text="A total of 60 light bulbs are set up at equal distance around a rectangular garden ABCD.\nA light bulb is placed at each corner. The distance between every two bulbs is 30 cm.\n17 light bulbs are set up along side DC.\n(a) Find the length of DC.\n(b) How many light bulbs are placed along BC?",
         image="img_p5_aitong_q25_garden.png", img_height=4.5,
         type="short", answer="(a) 480 cm  (b) 15 light bulbs"),
    dict(id=26, topic="Word Problems", difficulty="Hard", school="Ai Tong", marks=4,
         text="Daryl and Ben had an equal amount of money at first.\nEach day, Daryl spent $5.50 and Ben spent $3.20.\nAfter some days, Daryl had $95.20 left and Ben had $132 left.\nHow much money did each of them have at first?",
         type="short", answer="$183.20"),
    # ── Rosyth WA2 2025 — Booklet A (MCQ) ─────────────────────────────────────
    dict(id=27, topic="Volume", difficulty="Easy", school="Rosyth", marks=1,
         text="A solid cuboid of height 12 cm has a square base of side 4 cm. What is its volume?",
         image="img_p5_rosyth_q1_cuboid.png",
         type="mcq",
         opts=["(1)  16 cm³", "(2)  48 cm³", "(3)  96 cm³", "(4)  192 cm³"],
         answer="(4)  192 cm³"),
    dict(id=28, topic="Triangles & Area", difficulty="Easy", school="Rosyth", marks=1,
         text="Given that the base of triangle ABC is BC, what is the corresponding height?",
         image="img_p5_rosyth_q2_triangle.png",
         type="mcq",
         opts=["(1)  AD", "(2)  AC", "(3)  BC", "(4)  CE"],
         answer="(1)  AD"),
    dict(id=29, topic="Fractions", difficulty="Easy", school="Rosyth", marks=1,
         text="Find the value of 5/8 × 7/10 in its simplest form.",
         type="mcq",
         opts=["(1)  2/3", "(2)  7/16", "(3)  25/28", "(4)  1 13/40"],
         answer="(2)  7/16"),
    dict(id=30, topic="Ratio", difficulty="Easy", school="Rosyth", marks=1,
         text="Charles has 30 marbles and David has 25 marbles.\nFind the ratio of David's marbles to the total number of marbles that Charles and David have.",
         type="mcq",
         opts=["(1)  5 : 6", "(2)  6 : 5", "(3)  5 : 11", "(4)  11 : 5"],
         answer="(3)  5 : 11"),
    dict(id=31, topic="Decimals & Measurement", difficulty="Easy", school="Rosyth", marks=1,
         text="In the number line below, what is the value represented by A?",
         image="img_p5_rosyth_q5_numberline.png",
         type="mcq",
         opts=["(1)  8 7/10", "(2)  8 7/12", "(3)  9 1/5", "(4)  9 1/6"],
         answer="(1)  8 7/10"),
    # ── Rosyth WA2 2025 — Booklet B (Short Answer) ─────────────────────────────
    dict(id=32, topic="Whole Numbers", difficulty="Easy", school="Rosyth", marks=1,
         text="Find the value of 20 − 3 × 4 + 6 ÷ 2.",
         type="short", answer="11"),
    dict(id=33, topic="Ratio", difficulty="Easy", school="Rosyth", marks=1,
         text="The ratio of Clara's money to Devi's money is 3 : 8.\nClara has $21. How much money does Devi have?",
         type="short", answer="$56"),
    dict(id=34, topic="Triangles & Area", difficulty="Easy", school="Rosyth", marks=1,
         text="Find the area of the triangle shown below.",
         image="img_p5_rosyth_q8_triangle.png",
         type="short", answer="30 cm²"),
    dict(id=35, topic="Fractions", difficulty="Easy", school="Rosyth", marks=2,
         text="Express 15/4 as a decimal.",
         type="short", answer="3.75"),
    dict(id=36, topic="Ratio", difficulty="Medium", school="Rosyth", marks=2,
         text="The ratio of the number of stickers Edward has to the number Ahmad has is 1 : 4.\nAhmad has 160 stickers.\nHow many stickers must Ahmad give to Edward so that both will have the same number in the end?",
         type="short", answer="60"),
    dict(id=37, topic="Fractions", difficulty="Medium", school="Rosyth", marks=2,
         text="Mandy had 8 kg of sugar.\nShe used 3/4 of it to bake cookies and gave 5/6 kg of sugar to her mother.\nHow much sugar did she have left? Leave your answer in kilograms.",
         type="short", answer="1 1/6 kg"),
    dict(id=38, topic="Word Problems", difficulty="Hard", school="Rosyth", marks=2,
         text="The cost of a present was to be shared equally among 8 friends.\nHowever, 3 of the friends decided not to pay for the present.\nAs a result, the remaining friends each had to pay $126 more.\nHow much did each of the 8 friends have to pay at first?",
         type="short", answer="$210"),
    dict(id=39, topic="Triangles & Area", difficulty="Hard", school="Rosyth", marks=2,
         text="Raju drew three triangles to form a figure as shown below.\nThe areas of the triangles were in the ratio 1 : 4 : 15.\nHe then shaded some parts of the figure.\nThe unshaded area of the figure is 33 cm².\nFind the total shaded area of the figure.",
         image="img_p5_rosyth_q14_shaded.png",
         type="short", answer="132 cm²"),
    # ── Rosyth WA2 2025 — Paper 2 (Long Answer) ────────────────────────────────
    dict(id=40, topic="Word Problems", difficulty="Medium", school="Rosyth", marks=2,
         text="Sandra was given some money to buy some books.\nIf she bought 13 books, she would need $9 more.\nIf she bought 9 books, she would be left with $15.\nHow much did each book cost?",
         type="short", answer="$6"),
    dict(id=41, topic="Volume", difficulty="Hard", school="Rosyth", marks=3,
         text="Tank X, measuring 80 cm by 45 cm by 70 cm, is half-filled with water.\nTank Y, measuring 40 cm by 40 cm by 100 cm, is filled with 12 l of water.\nMr Leo pours all the water from Tank X into Tank Y without spilling.\nHow much more water is needed to fill Tank Y to its brim?",
         image="img_p5_rosyth_q16_tanks.png",
         type="short", answer="22 000 cm³"),
    dict(id=42, topic="Word Problems", difficulty="Hard", school="Rosyth", marks=3,
         text="Randy spent $189 on a table and 4/9 of his remaining money on a chair.\nHe had 1/6 of his original sum of money left.\nHow much money did he have at first?",
         type="short", answer="$270"),
    dict(id=43, topic="Fractions", difficulty="Hard", school="Rosyth", marks=4,
         text="Mrs Ho baked some cookies.\nShe sold 1/5 of her cookies and an additional 8 cookies on Monday.\nShe sold 2/3 of the remaining cookies and an additional 5 cookies on Tuesday.\nShe gave the rest of her 31 cookies to Mrs Lim.\nHow many cookies did Mrs Ho bake at first?",
         type="short", answer="145"),
    dict(id=44, topic="Word Problems", difficulty="Hard", school="Rosyth", marks=4,
         text="Betty sold brownies at $3 each.\nFor every 5 brownies purchased, she gave 2 free brownies to her customers.\nOn Friday, she sold and gave away a total of 240 brownies.\n(a) What was the largest possible number of brownies given free on Friday?\n(b) What was the least possible amount of money she collected from the 240 brownies sold and given away on Friday?",
         type="short", answer="(a) 68  (b) $516"),
]

# ── P6 Questions (Ai Tong 2025 Prelim) ───────────────────────────────────────
P6_QUESTIONS = [
    # ── Paper 1 Booklet A — MCQ (1 mark each) ─────────────────────────────────
    dict(id=1,  topic="Whole Numbers",  difficulty="Easy",   school="Ai Tong", marks=1,
         text="Which of the following is forty-five thousand and thirty in numerals?",
         type="mcq",
         opts=["(1)  4530", "(2)  45 030", "(3)  45 300", "(4)  450 030"],
         answer="(2)  45 030"),
    dict(id=2,  topic="Whole Numbers",  difficulty="Easy",   school="Ai Tong", marks=1,
         text="Round 7549 to the nearest hundred.",
         type="mcq",
         opts=["(1)  7000", "(2)  7500", "(3)  7600", "(4)  8000"],
         answer="(2)  7500"),
    dict(id=3,  topic="Percentage",     difficulty="Easy",   school="Ai Tong", marks=1,
         text="Express 2.4 as a percentage.",
         type="mcq",
         opts=["(1)  0.024%", "(2)  0.24%", "(3)  24%", "(4)  240%"],
         answer="(4)  240%"),
    dict(id=4,  topic="Decimals",       difficulty="Easy",   school="Ai Tong", marks=1,
         text="What is the missing number in the box?\n7.216 = 7 + 0.2 + ___",
         type="mcq",
         opts=["(1)  0.016", "(2)  0.16", "(3)  1.6", "(4)  16"],
         answer="(1)  0.016"),
    dict(id=5,  topic="Fractions",      difficulty="Easy",   school="Ai Tong", marks=1,
         text="Which fraction is smaller than 1/2?",
         type="mcq",
         opts=["(1)  5/7", "(2)  4/9", "(3)  3/6", "(4)  2/3"],
         answer="(2)  4/9"),
    dict(id=6,  topic="Measurement",    difficulty="Easy",   school="Ai Tong", marks=1,
         text="Which of the following could be the mass of a mobile phone?",
         type="mcq",
         opts=["(1)  0.05 kg", "(2)  1.5 kg", "(3)  15 g", "(4)  150 g"],
         answer="(4)  150 g"),
    dict(id=7,  topic="Fractions",      difficulty="Easy",   school="Ai Tong", marks=1,
         text="Arrange the following fractions from the smallest to the greatest:\n6/11,  7/10,  3/5",
         type="mcq",
         opts=["(1)  6/11, 3/5, 7/10", "(2)  6/11, 7/10, 3/5",
               "(3)  3/5, 6/11, 7/10", "(4)  3/5, 7/10, 6/11"],
         answer="(1)  6/11, 3/5, 7/10"),
    dict(id=8,  topic="Geometry",       difficulty="Medium", school="Ai Tong", marks=2,
         text="The figure shows a cube.\nWhich one of the following is a net of a cube?",
         image="p6_q8_cube_nets.jpg",
         type="mcq",
         opts=["(1)", "(2)", "(3)", "(4)"],
         answer="(4)"),
    dict(id=9,  topic="Data Analysis",  difficulty="Medium", school="Ai Tong", marks=2,
         text="The table below shows the number of students in four groups A, B, C and D.\nGroup A: 15, Group B: 30, Group C: 25, Group D: 30.\nWhich of the following pie charts best represents the information?",
         image="p6_q9_pie_charts.jpg",
         type="mcq",
         opts=["(1)", "(2)", "(3)", "(4)"],
         answer="(3)"),
    dict(id=10, topic="Algebra",        difficulty="Easy",   school="Ai Tong", marks=1,
         text="Find the value of 4y/2 + 10 − 4 when y = 4.",
         type="mcq",
         opts=["(1)  11", "(2)  14", "(3)  22", "(4)  28"],
         answer="(2)  14"),
    # ── Paper 1 Booklet A — MCQ (2 marks each) ────────────────────────────────
    dict(id=11, topic="Geometry",       difficulty="Medium", school="Ai Tong", marks=2,
         text="Amelia used identical unit cubes to build a solid. She drew the top and side views of the solid as shown. Which of the following could be the solid built by Amelia?",
         image="p6_q11_3d_solids.jpg", img_height=14.0,
         type="mcq",
         opts=["(1)", "(2)", "(3)", "(4)"],
         answer="(3)"),
    dict(id=12, topic="Percentage",     difficulty="Medium", school="Ai Tong", marks=2,
         text="Hassan spent 35% of his monthly allowance on food and 2/5 of the remaining allowance on transport.\nWhat percentage of his allowance was left?",
         type="mcq",
         opts=["(1)  65%", "(2)  61%", "(3)  39%", "(4)  25%"],
         answer="(3)  39%"),
    dict(id=13, topic="Perimeter & Area", difficulty="Medium", school="Ai Tong", marks=2,
         text="The figure is made up of two identical semicircles with radius of 21 m.\nFind the perimeter of the figure in terms of π.",
         image="p6_q13_semicircles.jpg",
         type="mcq",
         opts=["(1)  21π m", "(2)  (21π + 21) m", "(3)  42π m", "(4)  (42π + 42) m"],
         answer="(4)  (42π + 42) m"),
    dict(id=14, topic="Ratio",          difficulty="Hard",   school="Ai Tong", marks=2,
         text="Jack drew three triangles to form a figure. The areas of the triangles were in the ratio of 1 : 8 : 12. He then shaded some parts of the figure as shown.\nWhat is the ratio of the total area of the shaded parts to the area of the figure?",
         image="p6_q14_triangles.jpg",
         type="mcq",
         opts=["(1)  5 : 12", "(2)  5 : 21", "(3)  7 : 12", "(4)  2 : 3"],
         answer="(1)  5 : 12"),
    dict(id=15, topic="Ratio",          difficulty="Hard",   school="Ai Tong", marks=2,
         text="4 years ago, the ratio of Calvin's age to Lina's age is 2 : 7.\nIn 8 years' time, Calvin's age will be 2/5 of Lina's age.\nHow old is Calvin now?",
         type="mcq",
         opts=["(1)  10 years old", "(2)  18 years old",
               "(3)  22 years old",  "(4)  30 years old"],
         answer="(3)  22 years old"),
    # ── Paper 1 Booklet B — Short Answer (1 mark each) ────────────────────────
    dict(id=16, topic="Order of Operations", difficulty="Easy", school="Ai Tong", marks=1,
         text="What is the value of 30 − (8 + 16) ÷ 3 × 2?",
         type="short", answer="14"),
    dict(id=17, topic="Geometry",       difficulty="Medium", school="Ai Tong", marks=1,
         text="In the figure, EOH, FOJ and GOK are straight lines.\n∠EOF = 31° and ∠KOH = 96°. Find ∠GOF.",
         image="p6_q17_angles.jpg", img_height=8.0,
         type="short", answer="65°"),
    dict(id=18, topic="Average",        difficulty="Easy",   school="Ai Tong", marks=1,
         text="Find the average of 15, 17, 0 and 4.",
         type="short", answer="9"),
    dict(id=19, topic="Ratio",          difficulty="Easy",   school="Ai Tong", marks=1,
         text="A ribbon was cut into two pieces in the ratio 3 : 5.\nThe length of the longer piece was 35 cm.\nWhat was the length of the ribbon at first?",
         type="short", answer="56 cm"),
    # ── Paper 1 Booklet B — Short Answer (2 marks each) ───────────────────────
    dict(id=20, topic="Volume",         difficulty="Easy",   school="Ai Tong", marks=2,
         text="A solid cuboid of height 21 cm has a square base of side 9 cm.\nWhat is its volume?",
         image="p6_q22_cuboid.jpg",
         type="short", answer="1701 cm³"),
    dict(id=21, topic="Data Analysis",  difficulty="Easy",   school="Ai Tong", marks=2,
         text="The bar graph shows the time taken by 5 children to complete a race.\n(a) Who was the fastest runner?\n(b) How much longer did Dan take than Elvin to complete the race?",
         image="p6_q21_bargraph.jpg",
         type="short", answer="(a) Arif  (b) 16 s"),
    dict(id=22, topic="Fractions",      difficulty="Medium", school="Ai Tong", marks=2,
         text="In the figure, rectangle WXYZ is made up of 8 identical smaller rectangles.\nWhat fraction of rectangle WXYZ is shaded? Express your answer in the simplest form.",
         image="p6_q23_shaded_rect.jpg",
         type="short", answer="5/8"),
    dict(id=23, topic="Geometry",       difficulty="Hard",   school="Ai Tong", marks=2,
         text="A triangular piece of paper ABC is folded along the dotted line as shown. AB = AC. Find ∠p.",
         image="p6_q24_paper_fold.jpg",
         type="short", answer="46°"),
    dict(id=24, topic="Algebra",        difficulty="Medium", school="Ai Tong", marks=2,
         text="Jen wants to spend the least amount of money to buy 25 muffins.\nEach muffin is sold at $n.\nHow much will she pay for the muffins? Express your answer in terms of n.",
         image="p6_q25_muffins.jpg", img_height=3.0,
         type="short", answer="$17n"),
    dict(id=25, topic="Geometry",       difficulty="Medium", school="Ai Tong", marks=2,
         text="In the square grid, AB and BC are straight lines.\n(a) Measure and write down the size of ∠ABC.\n(b) AB and BC form two sides of a parallelogram ABCD. Complete the drawing of the parallelogram ABCD. Label Point D.",
         image="p6_q26_parallelogram.jpg",
         type="short", answer="(a) 141°"),
    dict(id=26, topic="Measurement",    difficulty="Easy",   school="Ai Tong", marks=2,
         text="Three beakers are filled with some water. What is the total volume of water in the three beakers?",
         image="p6_q27_beakers.jpg", img_height=3.5,
         type="short", answer="1.95 l"),
    dict(id=27, topic="Geometry",       difficulty="Hard",   school="Ai Tong", marks=2,
         text="In the figure, ABCD is a trapezium with AD // BC.\nBCF is an isosceles triangle. EFC is a straight line. Find ∠ABF.",
         image="p6_q28_trapezium.jpg",
         type="short", answer="26°"),
    dict(id=28, topic="Perimeter & Area", difficulty="Hard", school="Ai Tong", marks=2,
         text="The figure is made up of two identical right-angled triangles overlapping each other. XY = 3 cm and PQ is a straight line.\nFind the area of the shaded part.",
         image="p6_q29_triangles.jpg",
         type="short", answer="32.5 cm²"),
    dict(id=29, topic="Fractions",      difficulty="Hard",   school="Ai Tong", marks=2,
         text="A shop had some bags for sale.\nAfter selling 28 bags in the morning and 5/8 of the remaining bags in the afternoon, 1/4 of the bags were left unsold.\nHow many bags were sold altogether?",
         type="short", answer="63"),
    # ── Paper 2 — Short Answer ────────────────────────────────────────────────
    dict(id=30, topic="Money",          difficulty="Medium", school="Ai Tong", marks=2,
         text="The table shows water charges:\n\nMr Chan paid $89 for using 60 m³ of water.\nHow much did he pay per cubic metre for water consumption more than 40 m³?",
         image="p6_p2q1_water_table.jpg", img_height=3.0,
         type="short", answer="$1.65"),
    dict(id=31, topic="Measurement",    difficulty="Easy",   school="Ai Tong", marks=2,
         text="Deena had 2.07 kg of flour at first. She used 459 g of it.\nHow many kilograms of flour was left?",
         type="short", answer="1.611 kg"),
    dict(id=32, topic="Percentage",     difficulty="Medium", school="Ai Tong", marks=2,
         text="The line graph shows the growth of a plant over 4 weeks.\nWhat was the percentage increase in the height of the plant from Week 1 to Week 3?",
         image="p6_p2q3_linegraph.jpg", img_height=8.0,
         type="short", answer="300%"),
    dict(id=33, topic="Perimeter & Area", difficulty="Hard", school="Ai Tong", marks=2,
         text="Triangle ABC is an isosceles triangle that lies within a figure made up of a semicircle and a rectangle. AB = AC. Find the area of Triangle ABC.",
         image="p6_p2q4_triangle.jpg",
         type="short", answer="123.75 m²"),
    dict(id=34, topic="Perimeter & Area", difficulty="Hard", school="Ai Tong", marks=2,
         text="The figure is formed using 2 squares and 2 equilateral triangles. The perimeter of the figure is 120 cm. PQ is a straight line. What is the length of PQ?",
         image="p6_p2q5_figure.jpg",
         type="short", answer="24 cm"),
    # ── Paper 2 — Long Answer ─────────────────────────────────────────────────
    dict(id=35, topic="Data Analysis",  difficulty="Medium", school="Ai Tong", marks=3,
         text="A group of students were asked to choose their favourite fruit. The result was represented in the pie chart. Half of the number of students chose mango or orange as their favourite fruit.\n(a) What fraction of the students chose apple as their favourite fruit? Express your answer in its simplest form.\n(b) Each of the statements below is either true, false or not possible to tell. Put a tick to indicate your answer.",
         image="p6_p2q6_piechart.jpg", img_height=13.0, img_align="centre",
         type="short", answer="(a) 3/20"),
    dict(id=36, topic="Volume",         difficulty="Hard",   school="Ai Tong", marks=3,
         text="Figure 1 shows an empty container with a rectangular base area of 30 cm².\nThe container was filled with some water. Figure 2 shows the front view with water level at 4.6 cm. Figure 3 shows the container turned upside down with water level at 5.5 cm.\nWhat is the capacity of the container?",
         image="p6_p2q7_container.jpg",
         type="short", answer="234 cm³"),
    dict(id=37, topic="Geometry",       difficulty="Hard",   school="Ai Tong", marks=3,
         text="JKLM is a rhombus. KLN and KLO are triangles. LM = MN.\n(a) Find ∠LOK.\n(b) Find ∠LNM.",
         image="p6_p2q8_rhombus.jpg", img_height=9.0,
         type="short", answer="(a) 21°  (b) 27°"),
    dict(id=38, topic="Ratio",          difficulty="Hard",   school="Ai Tong", marks=3,
         text="Kai read part of a book in the morning.\nThe ratio of the number of pages he read to the number of pages that were unread was 6 : 5.\nAfter reading another 195 pages in the afternoon, Kai still had 10% of the book unread.\nHow many pages were there in the book?",
         type="short", answer="550"),
    dict(id=39, topic="Speed",          difficulty="Hard",   school="Ai Tong", marks=3,
         text="Town X and Town Y were 455 km apart.\nSam left Town X for Town Y, travelling at a constant speed of 85 km/h.\nAt the same time, Dan left Town Y for Town X, travelling along the same route at a constant speed of 90 km/h. How long had they travelled when they met each other?\nExpress your answer in h and min.",
         type="short", answer="2 h 36 min"),
    dict(id=40, topic="Fractions",      difficulty="Hard",   school="Ai Tong", marks=4,
         text="A fruit seller had some mangoes.\nHe sold 2/5 of them and donated 104 of them.\nHe was left with 1/3 of the mangoes and packed them into 24 bags.\nSome bags contained 4 mangoes each while the rest contained 6 mangoes each.\n(a) How many mangoes were packed?\n(b) How many bags contained 6 mangoes each?",
         type="short", answer="(a) 130  (b) 17"),
    dict(id=42, topic="Perimeter & Area", difficulty="Hard", school="Ai Tong", marks=5,
         text="The figure is made up of four identical quarter circles, two identical squares of sides 14 cm and a rectangle of breadth 19 cm. Four identical semicircles lie within the figure. (Take π = 3.14)\n(a) Find the perimeter of the unshaded part.\n(b) Find the area of the shaded parts.",
         image="p6_p2q12_circles.jpg",
         type="short", answer="(a) 169.88 cm  (b) 315.07 cm²"),
    dict(id=43, topic="Volume",         difficulty="Hard",   school="Ai Tong", marks=5,
         text="Two rectangular tanks, Tank A and Tank B, are shown. Tank A: 48 cm × 20 cm × 36 cm. Tank B: 60 cm × 10 cm × 45 cm. At first, Tank A was 1/3-filled with water and Tank B was empty.\n(a) What was the volume of water in Tank A at first?\n(b) Both taps were turned on at the same time at 2.4 litres per minute. How long did it take for the height of water in both tanks to be the same?",
         image="1776767678258_image.png",
         type="short", answer="(a) 11 520 cm³  (b) 8 min"),
    dict(id=44, topic="Number Patterns", difficulty="Medium", school="Ai Tong", marks=3,
         text="Selvi used rods to form figures following a pattern.\nFigure 1: 7 rods, Figure 2: 10 rods, Figure 3: 12 rods, Figure 4: 15 rods.\n(a) What is the difference between the number of rods used for Figure 7 and Figure 9?\n(b) How many rods would she use for Figure 99?",
         type="short", answer="(a) 5  (b) 252"),
    dict(id=46, topic="Word Problems",  difficulty="Hard",   school="Ai Tong", marks=4,
         text="There were 16 more students in Team A than in Team B in a competition.\n1/4 of the students in Team A and 3/7 of the students in Team B were girls.\nThe number of boys was twice the number of girls in the competition.\nHow many boys were there altogether?",
         type="short", answer="160"),
]

QUESTIONS = {
    "P1": P1_QUESTIONS,
    "P2": P2_QUESTIONS,
    "P3": P3_QUESTIONS,
    "P4": P4_QUESTIONS,
    "P5": P5_QUESTIONS,
    "P6": P6_QUESTIONS,   # ← NEW
}

LEVEL_LABELS = {
    "P1": "Primary 1",
    "P2": "Primary 2",
    "P3": "Primary 3",
    "P4": "Primary 4",
    "P5": "Primary 5",
    "P6": "Primary 6",    # ← NEW
}
DIFF_COLORS  = {"Easy": (GBG, GREEN), "Medium": (ABG, AMBER), "Hard": (RBG, RED)}

def make_styles(fsize=10):
    lh = round(fsize * 1.5)        # leading scales with font
    return {
        "section":   ParagraphStyle("section",   fontName=BOLD_FONT, fontSize=fsize+2,
                                    textColor=NAVY, spaceBefore=14, spaceAfter=6),
        "qtext":     ParagraphStyle("qtext",     fontName=BODY_FONT, fontSize=fsize,
                                    textColor=colors.black, leading=lh, spaceAfter=4),
        "qbold":     ParagraphStyle("qbold",     fontName=BOLD_FONT, fontSize=fsize,
                                    textColor=colors.black, leading=lh, spaceAfter=4),
        "opt":       ParagraphStyle("opt",       fontName=BODY_FONT, fontSize=fsize,
                                    textColor=colors.black, leading=lh-1, leftIndent=12),
        "ans_label": ParagraphStyle("ans_label", fontName=BODY_FONT, fontSize=max(8, fsize-1),
                                    textColor=MGRAY),
        "ans":       ParagraphStyle("ans",       fontName=BOLD_FONT, fontSize=fsize,
                                    textColor=RED),
        "footer":    ParagraphStyle("footer",    fontName=BODY_FONT, fontSize=8,
                                    textColor=MGRAY, alignment=TA_CENTER),
        "fl":        ParagraphStyle("fl",        fontName=BODY_FONT, fontSize=fsize,
                                    textColor=colors.black),
    }

def build_pdf(output_path, level="P4", selected_topics=None, include_answers=False, fsize=None):
    import re as _re
    # Default font size by level if not explicitly set
    if fsize is None:
        fsize = 13 if level == "P1" else 10
    S = make_styles(fsize=fsize)

    LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sgmaths_logo.png")
    PAGE_W_PT, PAGE_H_PT = A4

    footer_text = f"sgmaths.sg  |  {LEVEL_LABELS.get(level, level)} Mathematics  |  End of Paper"

    def draw_page(canvas, doc):
        import math
        canvas.saveState()
        # Watermark
        img = ImageReader(LOGO_PATH)
        iw, ih = img.getSize()
        wm_w = 16 * cm
        wm_h = wm_w * ih / iw
        angle = math.degrees(math.atan2(PAGE_H_PT, PAGE_W_PT))
        canvas.translate(PAGE_W_PT / 2, PAGE_H_PT / 2)
        canvas.rotate(angle)
        canvas.setFillAlpha(0.07)
        canvas.drawImage(img, -wm_w / 2, -wm_h / 2,
                         width=wm_w, height=wm_h, mask="auto")
        canvas.restoreState()
        # Footer on last page only
        if canvas.getPageNumber() == doc._pageCount:
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(HexColor("#6b7280"))
            canvas.drawCentredString(PAGE_W_PT / 2, 1.2*cm, footer_text)
            canvas.restoreState()

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    qs = QUESTIONS.get(level, P4_QUESTIONS)
    if selected_topics:
        qs = [q for q in qs if q["topic"] in selected_topics]
    story = []

    # ── Page header ────────────────────────────────────────────────────────────
    PAGE_W  = 17.0*cm
    BADGE_W = 3.0*cm
    LINE_H  = round(fsize * 2.2)  # scales with font size

    # Name / Class / Date — single row with inline underscores, matching P2-P5 style
    UNDERLINE_NAME  = "_" * 32
    UNDERLINE_CLASS = "_" * 10
    UNDERLINE_DATE  = "_" * 14
    header_style = ParagraphStyle("hdr", fontName=BODY_FONT, fontSize=fsize,
                                  textColor=colors.black, leading=fsize * 1.5)
    name_data = [[
        Paragraph(f"Name: {UNDERLINE_NAME}", header_style),
        Paragraph(f"Class: {UNDERLINE_CLASS}", header_style),
        Paragraph(f"Date: {UNDERLINE_DATE}", header_style),
    ]]
    name_tbl = Table(name_data, colWidths=[8.5*cm, 4.0*cm, 4.5*cm])
    name_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(name_tbl)
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY))
    story.append(Spacer(1, 0.3*cm))

    # ── Helpers ────────────────────────────────────────────────────────────────
    PART_RE = _re.compile(r'^\(([a-z])\)\s*')

    def smart_line(text, bold_prefix=None, fsize=fsize):
        segs = _parse_segs(text)
        has_frac = any(s[0] == "frac" for s in segs)
        if has_frac:
            return MixedLine(segs, fsize=fsize, bold_prefix=bold_prefix, leading=LINE_H)
        prefix_html = f"<b>{bold_prefix}</b> " if bold_prefix else ""
        style = ParagraphStyle("ql", fontName=BODY_FONT, fontSize=fsize,
                               leading=LINE_H, textColor=colors.black)
        return Paragraph(prefix_html + text, style)

    def make_work_box(marks, is_word_problem=False):
        """Working space box — larger for word problems."""
        if is_word_problem:
            if marks <= 3:
                h = 7.0*cm
            else:
                h = 10.0*cm
        else:
            if marks <= 2:
                h = 2.5*cm
            elif marks <= 4:
                h = 4.5*cm
            else:
                h = 6.5*cm
        tbl = Table([[Paragraph("Working:", S["ans_label"])]], colWidths=[PAGE_W],
                    rowHeights=[h])
        tbl.setStyle(TableStyle([
            ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
            ("BACKGROUND",    (0,0), (-1,-1), LGRAY),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        return tbl

    def make_ans_boxes(parts):
        """
        parts: list of part labels e.g. ['a','b'] or [] for single answer.
        Each part gets its own row: label right-aligned next to a box.
        Single answer → one row with "Ans:" label.
        """
        BOX_W   = 5.0*cm
        LABEL_W = 1.8*cm
        SPACE_W = PAGE_W - LABEL_W - BOX_W   # left spacer

        if not parts:
            parts = [""]

        rows   = []
        styles = [
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",   (0,0), (-1,-1), 0),
            ("RIGHTPADDING",  (0,0), (-1,-1), 0),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ]
        for i, p in enumerate(parts):
            label_txt = f"({p})" if p else "Ans:"
            rows.append([
                Paragraph("", S["ans_label"]),
                Paragraph(label_txt, S["ans_label"]),
                Paragraph("", S["ans_label"]),
            ])
            # box is column 2
            styles.append(("BOX", (2, i), (2, i), 1, NAVY))

        tbl = Table(rows, colWidths=[SPACE_W, LABEL_W, BOX_W])
        tbl.setStyle(TableStyle(styles))
        return tbl

    # ── Questions ──────────────────────────────────────────────────────────────
    q_counter = 0
    for q in qs:
        q_counter += 1
        diff_bg, diff_fg = DIFF_COLORS[q["difficulty"]]
        is_word = (q["topic"] == "Word Problems")

        # Detect parts (a), (b), (c) in question text
        parts = _re.findall(r'\(([a-z])\)', q["text"])
        parts = list(dict.fromkeys(parts))   # deduplicate, preserve order

        # Badge
        badge = Paragraph(
            f"{q['difficulty']}  |  {q['marks']} mark{'s' if q['marks']>1 else ''}",
            ParagraphStyle("b", fontName=BODY_FONT, fontSize=max(8, fsize-2),
                           textColor=diff_fg, alignment=TA_CENTER))
        badge_tbl = Table([[badge]], colWidths=[BADGE_W])
        badge_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), diff_bg),
            ("ROUNDEDCORNERS",[4]),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        badge_row = Table([[Paragraph("", S["ans_label"]), badge_tbl]],
                          colWidths=[PAGE_W - BADGE_W, BADGE_W])
        badge_row.setStyle(TableStyle([
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 2),
        ]))

        # Question text lines
        all_lines = q["text"].split("\n")
        first_cell = smart_line(all_lines[0], bold_prefix=f"Q{q_counter}.", fsize=fsize)
        q_block = [first_cell]
        for extra in all_lines[1:]:
            if extra.strip():
                q_block.append(smart_line(extra, fsize=fsize))
            else:
                q_block.append(Spacer(1, 0.15*cm))

        # Embed image or vector diagram if question has one
        if q.get("image"):
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), q["image"])
            if os.path.exists(img_path):
                img_h = q.get("img_height", 5.5) * cm
                img_align = q.get("img_align", "left")
                q_block.append(Spacer(1, 0.2*cm))
                _img = Image(img_path, width=PAGE_W, height=img_h, kind="proportional")
                if img_align == "centre":
                    _img.hAlign = "CENTER"
                q_block.append(_img)
                q_block.append(Spacer(1, 0.2*cm))
            else:
                placeholder = Table(
                    [[Paragraph("[Diagram: see original paper]", S["ans_label"])]],
                    colWidths=[PAGE_W], rowHeights=[2.5*cm]
                )
                placeholder.setStyle(TableStyle([
                    ("BOX",         (0,0), (-1,-1), 0.5, BORDER),
                    ("BACKGROUND",  (0,0), (-1,-1), LGRAY),
                    ("TOPPADDING",  (0,0), (-1,-1), 8),
                    ("LEFTPADDING", (0,0), (-1,-1), 8),
                ]))
                q_block.append(Spacer(1, 0.2*cm))
                q_block.append(placeholder)
                q_block.append(Spacer(1, 0.2*cm))
        elif q.get("diagram"):
            from diagrams import get_diagram
            diag = get_diagram(*q["diagram"])
            if diag is not None:
                q_block.append(Spacer(1, 0.2*cm))
                q_block.append(diag)
                q_block.append(Spacer(1, 0.2*cm))

        
        # Answer / working area
        if q["type"] == "mcq":
            q_block.append(Spacer(1, 0.1*cm))
            for opt in q["opts"]:
                q_block.append(smart_line(opt, fsize=fsize))
            q_block.append(Spacer(1, 0.1*cm))
            q_block.append(badge_row)
            q_block.append(make_ans_boxes([]))
        elif q["type"] == "draw":
            q_block.append(Spacer(1, 0.1*cm))
            q_block.append(badge_row)
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
            q_block.append(Spacer(1, 0.1*cm))
            q_block.append(badge_row)
            q_block.append(make_work_box(q["marks"], is_word_problem=is_word))
            q_block.append(Spacer(1, 0.1*cm))
            q_block.append(make_ans_boxes(parts))

        if include_answers:
            ak_line  = MixedLine(_parse_segs(str(q["answer"])), fsize=fsize,
                                 bold_prefix="Answer:", leading=LINE_H, color=HexColor("#991b1b"))
            ak_outer = Table([[ak_line]], colWidths=[PAGE_W])
            ak_outer.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), HexColor("#fee2e2")),
                ("BOX",           (0,0), (-1,-1), 0.5, HexColor("#fca5a5")),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ]))
            q_block.append(ak_outer)

        story.append(KeepTogether(q_block))

        # Word problems: 2 per page → hard page break after every 2nd one
        if is_word:
            if q_counter % 2 == 0:
                from reportlab.platypus import PageBreak
                story.append(PageBreak())
            else:
                story.append(Spacer(1, 0.5*cm))
        else:
            story.append(Spacer(1, 0.5*cm))

    # Two-pass: dry-run on a copy to get total page count, then real build
    import io, copy
    _buf = io.BytesIO()
    _doc2 = SimpleDocTemplate(_buf, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    _page_count = [0]
    def _count_page(canvas, doc): _page_count[0] = canvas.getPageNumber()
    _doc2.build(copy.deepcopy(story), onFirstPage=_count_page, onLaterPages=_count_page)
    doc._pageCount = _page_count[0]

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"PDF saved: {output_path}")

if __name__ == "__main__":
    build_pdf("sgmaths_p2_worksheet.pdf",         level="P2", include_answers=False)
    build_pdf("sgmaths_p2_worksheet_answers.pdf", level="P2", include_answers=True)
    build_pdf("sgmaths_p3_worksheet.pdf",         level="P3", include_answers=False)
    build_pdf("sgmaths_p3_worksheet_answers.pdf", level="P3", include_answers=True)
    build_pdf("sgmaths_p4_worksheet.pdf",         level="P4", include_answers=False)
    build_pdf("sgmaths_p4_worksheet_answers.pdf", level="P4", include_answers=True)
    build_pdf("sgmaths_p5_worksheet.pdf",         level="P5", include_answers=False)
    build_pdf("sgmaths_p5_worksheet_answers.pdf", level="P5", include_answers=True)
    build_pdf("sgmaths_p6_worksheet.pdf",         level="P6", include_answers=False)
    build_pdf("sgmaths_p6_worksheet_answers.pdf", level="P6", include_answers=True)
