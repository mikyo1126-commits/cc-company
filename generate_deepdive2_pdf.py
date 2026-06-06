#!/usr/bin/env python3
"""
DEEP DIVE Vol.2 PDF generator — 朝夜投稿セット（DD-11〜DD-24）
Output: marketing/content-plan/hajime-x-deepdive2-posts.pdf
"""
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_PATH = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
pdfmetrics.registerFont(TTFont("JA", FONT_PATH))

W, H = A4
ML, MR, MT, MB = 18*mm, 18*mm, 22*mm, 18*mm
TW = W - ML - MR

# Base palette
COL_BG      = HexColor("#F4F6F9")
COL_CARD    = HexColor("#FFFFFF")
COL_SHADOW  = HexColor("#D0D7E3")
COL_HDR     = HexColor("#0D1B2A")
COL_BODY    = HexColor("#2C3E50")
COL_SOURCE  = HexColor("#7F8C8D")
COL_DIVIDER = HexColor("#BDC3C7")
COL_HASH_BG = HexColor("#EAF2FF")
COL_HASH    = HexColor("#1A5276")

# Morning (🌅) — orange/warm
MORNING_ACCENT = HexColor("#E67E22")
MORNING_BADGE  = HexColor("#D35400")
MORNING_HDR    = HexColor("#1A1A2E")

# Evening (🌙) — purple/cool
EVENING_ACCENT = HexColor("#6C3483")
EVENING_BADGE  = HexColor("#512E5F")
EVENING_HDR    = HexColor("#0D1B2A")

CATEGORY_COLORS = {
    "オーダーブロック": HexColor("#E67E22"),
    "資金設計":         HexColor("#C0392B"),
    "移動平均線":       HexColor("#1A5276"),
    "手法探し":         HexColor("#884EA0"),
    "時間軸":           HexColor("#1E8449"),
    "含み損":           HexColor("#922B21"),
    "ポジション管理":   HexColor("#B7950B"),
    "プロの習慣":       HexColor("#2C3E50"),
    "相関通貨":         HexColor("#117A65"),
    "記録":             HexColor("#784212"),
    "水平線":           HexColor("#0E6251"),
    "成長":             HexColor("#6C3483"),
    "ボラティリティ":   HexColor("#17202A"),
    "継続":             HexColor("#1B4F72"),
}

SCHEDULE = [
    ("1日目", "DD-11 🌅 オーダーブロック",        "DD-12 🌙 資金設計"),
    ("2日目", "DD-13 🌅 移動平均線",              "DD-14 🌙 手法探し"),
    ("3日目", "DD-15 🌅 時間軸",                  "DD-16 🌙 含み損"),
    ("4日目", "DD-17 🌅 ポジション管理",          "DD-18 🌙 プロの習慣"),
    ("5日目", "DD-19 🌅 相関通貨",                "DD-20 🌙 記録"),
    ("6日目", "DD-21 🌅 水平線",                  "DD-22 🌙 成長"),
    ("7日目", "DD-23 🌅 ボラティリティ",          "DD-24 🌙 継続"),
]


def _wrap(c, text, fs, max_w):
    c.setFont("JA", fs)
    lines = []
    for para in text.split("\n"):
        if para == "":
            lines.append("")
            continue
        cur = ""
        for ch in para:
            test = cur + ch
            if pdfmetrics.stringWidth(test, "JA", fs) > max_w:
                lines.append(cur)
                cur = ch
            else:
                cur = test
        lines.append(cur)
    return lines


class DeepDive2PDF:
    def __init__(self, filename):
        self.c    = canvas.Canvas(filename, pagesize=A4)
        self.c.setTitle("はじめさん DEEP DIVE Vol.2 徹底解説投稿集（朝夜セット）")
        self.y    = H - MT
        self.page = 1
        self._bg()

    def _bg(self):
        self.c.setFillColor(COL_BG)
        self.c.rect(0, 0, W, H, fill=1, stroke=0)

    def _check(self, needed):
        if self.y - needed < MB:
            self._pnum()
            self.c.showPage()
            self.page += 1
            self._bg()
            self.y = H - MT

    def _pnum(self):
        self.c.setFont("JA", 7)
        self.c.setFillColor(COL_SOURCE)
        self.c.drawCentredString(W/2, 10*mm, f"- {self.page} -")

    def draw_cover(self, posts):
        c = self.c

        # Header band
        c.setFillColor(COL_HDR)
        c.rect(0, H - 80*mm, W, 80*mm, fill=1, stroke=0)
        c.setFillColor(MORNING_ACCENT)
        c.rect(0, H - 80*mm, W/2, 3*mm, fill=1, stroke=0)
        c.setFillColor(EVENING_ACCENT)
        c.rect(W/2, H - 80*mm, W/2, 3*mm, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("JA", 10)
        c.drawCentredString(W/2, H - 19*mm, "はじめさん X投稿")
        c.setFont("JA", 19)
        c.drawCentredString(W/2, H - 32*mm, "DEEP DIVE 徹底解説投稿集 Vol.2")
        c.setFillColor(HexColor("#AEB6BF"))
        c.setFont("JA", 8.5)
        c.drawCentredString(W/2, H - 44*mm, "朝夜2投稿対応 ／ DD-11〜DD-24（14本）")
        c.setFont("JA", 7.5)
        c.drawCentredString(W/2, H - 55*mm,
            "🌅 朝：テクニカル・知識系（7本）  ／  🌙 夜：マインド・哲学系（7本）")

        # Stats
        c.setFillColor(white)
        bx, by, bw, bh = ML, H - 108*mm, TW, 20*mm
        c.roundRect(bx, by, bw, bh, 3*mm, fill=1, stroke=0)
        stats = [("14本", "投稿総数"), ("7日分", "スケジュール"), ("🌅 7本", "朝投稿"), ("🌙 7本", "夜投稿")]
        cw = TW / 4
        for i, (num, lbl) in enumerate(stats):
            cx = bx + cw * i + cw / 2
            c.setFont("JA", 12); c.setFillColor(COL_HDR)
            c.drawCentredString(cx, by + 12*mm, num)
            c.setFont("JA", 6.5); c.setFillColor(COL_SOURCE)
            c.drawCentredString(cx, by + 5*mm, lbl)

        # 7-day schedule table
        y = H - 120*mm
        c.setFillColor(HexColor("#E8EAF6"))
        c.rect(ML, y - 7*mm, TW, 7*mm, fill=1, stroke=0)
        c.setFillColor(COL_HDR); c.setFont("JA", 8.5)
        c.drawString(ML + 4*mm, y - 4.5*mm, "7日間投稿スケジュール")
        y -= 8*mm

        col_day = 16*mm
        col_am  = (TW - col_day) / 2
        col_pm  = (TW - col_day) / 2

        # Table header
        c.setFillColor(COL_HDR)
        c.rect(ML, y - 8*mm, TW, 8*mm, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("JA", 7.5)
        c.drawString(ML + 3*mm, y - 5.5*mm, "日")
        c.setFillColor(MORNING_ACCENT); c.setFont("JA", 7.5)
        c.drawString(ML + col_day + 3*mm, y - 5.5*mm, "🌅 朝投稿")
        c.setFillColor(EVENING_ACCENT)
        c.drawString(ML + col_day + col_am + 3*mm, y - 5.5*mm, "🌙 夜投稿")
        y -= 9*mm

        for ri, (day, am, pm) in enumerate(SCHEDULE):
            bg = HexColor("#FFFFFF") if ri % 2 == 0 else HexColor("#F8F9FA")
            c.setFillColor(bg)
            c.rect(ML, y - 8*mm, TW, 8*mm, fill=1, stroke=0)
            c.setFillColor(COL_SOURCE); c.setFont("JA", 7)
            c.drawString(ML + 3*mm, y - 5.5*mm, day)
            c.setFillColor(HexColor("#784000")); c.setFont("JA", 7)
            c.drawString(ML + col_day + 3*mm, y - 5.5*mm, am)
            c.setFillColor(EVENING_ACCENT)
            c.drawString(ML + col_day + col_am + 3*mm, y - 5.5*mm, pm)
            y -= 9*mm

        self.y = y - 4*mm

        # Legend
        self._check(18*mm)
        c.setFillColor(COL_CARD)
        c.roundRect(ML, self.y - 14*mm, TW, 14*mm, 2*mm, fill=1, stroke=0)

        samples = [
            (MORNING_ACCENT, HexColor("#FFF3E0"), "🌅 朝投稿カード（テクニカル・知識系）"),
            (EVENING_ACCENT, HexColor("#F3E5F5"), "🌙 夜投稿カード（マインド・哲学・共感系）"),
        ]
        for i, (acc, bg, lbl) in enumerate(samples):
            sx = ML + 5*mm + i * (TW/2)
            c.setFillColor(bg)
            c.roundRect(sx, self.y - 12*mm, TW/2 - 8*mm, 10*mm, 2*mm, fill=1, stroke=0)
            c.setFillColor(acc)
            c.rect(sx, self.y - 12*mm, 3*mm, 10*mm, fill=1, stroke=0)
            c.roundRect(sx, self.y - 12*mm, 3*mm, 10*mm, 2*mm, fill=1, stroke=0)
            c.setFillColor(COL_HDR); c.setFont("JA", 7.5)
            c.drawString(sx + 6*mm, self.y - 7.5*mm, lbl)
        self.y -= 14*mm

        self._pnum()
        self.c.showPage()
        self.page += 1
        self._bg()
        self.y = H - MT

    def draw_post(self, code, time_of_day, category, ref, title, body, hashtag):
        is_morning = (time_of_day == "🌅")
        accent = MORNING_ACCENT if is_morning else EVENING_ACCENT
        badge_col = MORNING_BADGE if is_morning else EVENING_BADGE
        card_bg = HexColor("#FFFBF5") if is_morning else HexColor("#F9F5FF")
        cat_col = CATEGORY_COLORS.get(category, accent)
        time_label = "🌅 朝投稿" if is_morning else "🌙 夜投稿"

        hash_lines  = _wrap(self.c, hashtag, 7.5, TW - 14*mm) if hashtag else []
        body_lines  = _wrap(self.c, body, 8.5, TW - 8*mm)
        title_lines = _wrap(self.c, title, 10, TW - 12*mm)

        header_h = 13*mm
        title_h  = len(title_lines) * 5.5*mm + 4*mm
        body_h   = len(body_lines) * 5.2*mm + 4*mm
        ref_h    = 6*mm
        hash_h   = (len(hash_lines) * 4.8*mm + 4*mm + 3*mm) if hash_lines else 0
        total    = header_h + title_h + body_h + ref_h + hash_h + 10*mm

        self._check(total)
        box_y = self.y - total

        # Shadow
        self.c.setFillColor(COL_SHADOW)
        self.c.roundRect(ML + 1.5*mm, box_y - 1.5*mm, TW, total, 4*mm, fill=1, stroke=0)

        # Card bg
        self.c.setFillColor(card_bg)
        self.c.roundRect(ML, box_y, TW, total, 4*mm, fill=1, stroke=0)

        # Left bar
        self.c.setFillColor(cat_col)
        self.c.rect(ML, box_y, 3*mm, total, fill=1, stroke=0)
        self.c.roundRect(ML, box_y, 3*mm, total, 2*mm, fill=1, stroke=0)

        # Header
        self.c.setFillColor(COL_HDR)
        self.c.roundRect(ML, box_y + total - header_h, TW, header_h, 4*mm, fill=1, stroke=0)
        self.c.rect(ML, box_y + total - header_h, TW, header_h / 2, fill=1, stroke=0)

        # DEEP DIVE badge
        bx = ML + 5*mm
        by2 = box_y + total - header_h + 3*mm
        self.c.setFillColor(badge_col)
        self.c.roundRect(bx, by2, 22*mm, 5.5*mm, 1*mm, fill=1, stroke=0)
        self.c.setFillColor(white); self.c.setFont("JA", 6.5)
        self.c.drawCentredString(bx + 11*mm, by2 + 1.5*mm, "DEEP DIVE")

        # Time badge
        self.c.setFillColor(accent)
        self.c.roundRect(bx + 24*mm, by2, 18*mm, 5.5*mm, 1*mm, fill=1, stroke=0)
        self.c.setFillColor(white); self.c.setFont("JA", 6.5)
        self.c.drawCentredString(bx + 33*mm, by2 + 1.5*mm, time_label)

        # Category badge
        cat_label = f"【{category}】"
        cat_w = pdfmetrics.stringWidth(cat_label, "JA", 7) + 4*mm
        self.c.setFillColor(cat_col)
        self.c.roundRect(bx + 44*mm, by2, cat_w, 5.5*mm, 1*mm, fill=1, stroke=0)
        self.c.setFillColor(white); self.c.setFont("JA", 7)
        self.c.drawString(bx + 46*mm, by2 + 1.5*mm, cat_label)

        # Code label right
        self.c.setFillColor(HexColor("#AEB6BF"))
        self.c.setFont("JA", 8)
        self.c.drawRightString(ML + TW - 4*mm, by2 + 1.5*mm, code)

        # Title
        ty = box_y + total - header_h - 5.5*mm
        self.c.setFillColor(COL_HDR); self.c.setFont("JA", 10)
        for tl in title_lines:
            self.c.drawString(ML + 6*mm, ty, tl)
            ty -= 5.5*mm

        # Accent divider
        self.c.setStrokeColor(accent)
        self.c.setLineWidth(1.0)
        self.c.line(ML + 6*mm, ty + 2*mm, ML + 6*mm + 30*mm, ty + 2*mm)
        self.c.setStrokeColor(COL_DIVIDER)
        self.c.setLineWidth(0.4)
        self.c.line(ML + 36*mm + 6*mm, ty + 2*mm, ML + TW - 6*mm, ty + 2*mm)
        ty -= 4*mm

        # Body
        self.c.setFont("JA", 8.5)
        stop_y = box_y + hash_h + ref_h + 3*mm
        for line in body_lines:
            if ty < stop_y:
                break
            if line.startswith("■") or line.startswith("【"):
                self.c.setFillColor(cat_col)
            elif line.startswith("①") or line.startswith("②") or line.startswith("③"):
                self.c.setFillColor(accent)
            else:
                self.c.setFillColor(COL_BODY)
            self.c.drawString(ML + 6*mm, ty, line)
            ty -= 5.2*mm

        # Reference
        ref_y = box_y + hash_h + 3*mm
        self.c.setStrokeColor(COL_DIVIDER)
        self.c.setLineWidth(0.3)
        self.c.line(ML + 6*mm, ref_y + 5*mm, ML + TW - 6*mm, ref_y + 5*mm)
        self.c.setFillColor(COL_SOURCE); self.c.setFont("JA", 6.5)
        self.c.drawString(ML + 6*mm, ref_y + 1.5*mm, f"参考: {ref}")

        # Hashtag box
        if hash_lines:
            inner_h = len(hash_lines) * 4.8*mm + 4*mm
            tag_y = box_y + 3*mm
            self.c.setFillColor(COL_HASH_BG)
            self.c.roundRect(ML + 6*mm, tag_y, TW - 12*mm, inner_h, 2*mm, fill=1, stroke=0)
            self.c.setFillColor(COL_HASH); self.c.setFont("JA", 7.5)
            text_y = tag_y + inner_h - 4*mm
            for tl in hash_lines:
                self.c.drawString(ML + 9*mm, text_y, tl)
                text_y -= 4.8*mm

        self.y = box_y - 6*mm

    def save(self):
        self._pnum()
        self.c.save()


def parse_posts(filepath):
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    posts = []
    pattern = re.compile(
        r"### (DD-\d+)\s+([🌅🌙])\s+【([^】]+)】([^\n]+)\n+"
        r"参考:\s*([^\n]+)\n+"
        r"---\n+"
        r"(.*?)\n+"
        r"(#[^\n]+)\n+"
        r"---",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        code        = m.group(1).strip()
        time_of_day = m.group(2).strip()
        category    = m.group(3).strip()
        title       = m.group(4).strip()
        ref         = m.group(5).strip()
        body        = m.group(6).strip()
        hashtag     = m.group(7).strip()
        posts.append((code, time_of_day, category, ref, title, body, hashtag))
    return posts


if __name__ == "__main__":
    INPUT  = "marketing/content-plan/hajime-x-deepdive2-posts.md"
    OUTPUT = "marketing/content-plan/hajime-x-deepdive2-posts.pdf"

    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    posts = parse_posts(INPUT)
    print(f"Parsed {len(posts)} posts")

    maker = DeepDive2PDF(OUTPUT)
    maker.draw_cover(posts)

    for post in posts:
        maker.draw_post(*post)

    maker.save()
    size_kb = Path(OUTPUT).stat().st_size // 1024
    print(f"PDF saved: {OUTPUT}  ({size_kb} KB)")
