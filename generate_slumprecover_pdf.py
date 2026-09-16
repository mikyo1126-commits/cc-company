#!/usr/bin/env python3
"""
暴落→反発サイクル 実践投稿集 PDF generator (SR-01〜SR-05)
Output: marketing/content-plan/hajime-x-slump-recovery-posts.pdf
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

# Color palette: deep navy × action tones
COL_BG      = HexColor("#F5F6FA")
COL_CARD    = HexColor("#FFFFFF")
COL_HDR     = HexColor("#0D1B2A")
COL_BODY    = HexColor("#1C2833")
COL_SOURCE  = HexColor("#717D7E")
COL_DIVIDER = HexColor("#BFC9CA")
COL_HASH_BG = HexColor("#EAF2FF")
COL_HASH    = HexColor("#1A5276")

ACCENT      = HexColor("#1A237E")   # deep indigo — neutral authority
ACCENT_DARK = HexColor("#0D1460")

CATEGORY_COLORS = {
    "暴落中の禁止行動": HexColor("#C0392B"),   # red — danger
    "反発中の禁止行動": HexColor("#D35400"),   # orange — caution
    "推奨行動":         HexColor("#1E8449"),   # green — go
    "分岐点分析":       HexColor("#2471A3"),   # blue — analytical
    "振り返り":         HexColor("#6C3483"),   # purple — reflective
}

INDEX = [
    ("SR-01", "暴落中の禁止行動", "先週の暴落でやってはいけなかった3つのこと"),
    ("SR-02", "反発中の禁止行動", "今週の反発局面でやってはいけないこと"),
    ("SR-03", "推奨行動",         "暴落→反発サイクルで「絶対やった方がいいこと」"),
    ("SR-04", "分岐点分析",       "勝ち続けるトレーダーと脱落するトレーダーの違い"),
    ("SR-05", "振り返り",         "相場が戻った今こそ自分に問いかけるべき3つのこと"),
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


class SlumpRecoverPDF:
    def __init__(self, filename):
        self.c    = canvas.Canvas(filename, pagesize=A4)
        self.c.setTitle("はじめさん 暴落→反発サイクル 実践投稿集（SR-01〜SR-05）")
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

    def draw_cover(self):
        c = self.c

        # Header band
        c.setFillColor(COL_HDR)
        c.rect(0, H - 78*mm, W, 78*mm, fill=1, stroke=0)

        # Tri-color stripe: red → orange → green (crash → caution → recovery)
        colors = [HexColor("#C0392B"), HexColor("#E67E22"), HexColor("#1E8449")]
        stripe_w = W / 3
        for i, col in enumerate(colors):
            c.setFillColor(col)
            c.rect(i * stripe_w, H - 78*mm, stripe_w, 3*mm, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("JA", 9)
        c.drawCentredString(W/2, H - 18*mm, "はじめさん X投稿  実践版")
        c.setFont("JA", 16)
        c.drawCentredString(W/2, H - 31*mm, "暴落→反発 サイクル 実践投稿集")
        c.setFillColor(HexColor("#AED6F1"))
        c.setFont("JA", 8.5)
        c.drawCentredString(W/2, H - 43*mm,
            "心理・行動・やってはいけないこと・やるべきこと — 完全セット")
        c.setFillColor(HexColor("#A9DFBF"))
        c.setFont("JA", 7.5)
        c.drawCentredString(W/2, H - 54*mm,
            "SR-01〜SR-05（5本）  BTC $62k→$63.7k / S&P500 7,383→7,609 反発局面")

        # Stats bar
        c.setFillColor(white)
        bx, by, bw, bh = ML, H - 105*mm, TW, 19*mm
        c.roundRect(bx, by, bw, bh, 3*mm, fill=1, stroke=0)
        stats = [
            ("5本",     "実践投稿"),
            ("禁止行動", "2パターン"),
            ("推奨行動", "1パターン"),
            ("勝ち負け", "分岐点解説"),
        ]
        cw = TW / 4
        for i, (num, lbl) in enumerate(stats):
            cx = bx + cw * i + cw / 2
            c.setFont("JA", 10); c.setFillColor(COL_HDR)
            c.drawCentredString(cx, by + 11*mm, num)
            c.setFont("JA", 6); c.setFillColor(COL_SOURCE)
            c.drawCentredString(cx, by + 4*mm, lbl)

        # Index table
        y = H - 117*mm
        c.setFillColor(ACCENT_DARK)
        c.rect(ML, y - 7*mm, TW, 7*mm, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("JA", 8)
        c.drawString(ML + 4*mm, y - 4.5*mm, "投稿インデックス（SR-01〜SR-05）")
        y -= 8*mm

        col_code  = 16*mm
        col_cat   = 38*mm
        col_title_w = TW - col_code - col_cat - 6*mm

        for idx, (code, cat, title) in enumerate(INDEX):
            row_h = 10*mm
            bg = white if idx % 2 == 0 else HexColor("#EEF1F5")
            c.setFillColor(bg)
            c.rect(ML, y - row_h, TW, row_h, fill=1, stroke=0)

            acc = CATEGORY_COLORS.get(cat, ACCENT)
            c.setFillColor(acc)
            c.roundRect(ML + 2*mm, y - row_h + 2.5*mm, col_code - 2*mm, 5*mm, 1*mm, fill=1, stroke=0)
            c.setFillColor(white); c.setFont("JA", 6.5)
            c.drawCentredString(ML + 2*mm + (col_code - 2*mm)/2, y - row_h + 4*mm, code)

            c.setFillColor(acc); c.setFont("JA", 6.5)
            c.drawString(ML + col_code + 2*mm, y - row_h + 4*mm, cat)

            c.setFillColor(COL_BODY); c.setFont("JA", 7)
            title_str = title if pdfmetrics.stringWidth(title, "JA", 7) <= col_title_w else title[:22] + "…"
            c.drawString(ML + col_code + col_cat, y - row_h + 4*mm, title_str)

            y -= row_h

        # Legend strip: color guide
        y -= 5*mm
        c.setFillColor(white)
        c.roundRect(ML, y - 14*mm, TW, 14*mm, 2*mm, fill=1, stroke=0)
        c.setFillColor(COL_BODY); c.setFont("JA", 7.5)
        c.drawString(ML + 5*mm, y - 4.5*mm, "カード色凡例：")
        legend = [
            (HexColor("#C0392B"), "禁止行動（暴落中）"),
            (HexColor("#D35400"), "禁止行動（反発中）"),
            (HexColor("#1E8449"), "推奨行動"),
            (HexColor("#2471A3"), "分析"),
            (HexColor("#6C3483"), "振り返り"),
        ]
        lx = ML + 30*mm
        for col, label in legend:
            c.setFillColor(col)
            c.roundRect(lx, y - 9*mm, 4*mm, 4*mm, 1*mm, fill=1, stroke=0)
            c.setFillColor(COL_BODY); c.setFont("JA", 6)
            c.drawString(lx + 5*mm, y - 7*mm, label)
            lx += 30*mm

        self._pnum()
        c.showPage()
        self.page += 1
        self._bg()
        self.y = H - MT

    def draw_post(self, code, category, subtitle, source, body, hashtag):
        c = self.c
        acc = CATEGORY_COLORS.get(category, ACCENT)

        body_lines = body.strip().split("\n")
        hash_lines = [l for l in body_lines if l.startswith("#")]
        body_only  = [l for l in body_lines if not l.startswith("#")]
        hash_text  = " ".join(hash_lines)

        BODY_FS = 8.5
        SUB_FS  = 8.0
        PAD     = 4*mm
        INNER_W = TW - 2*PAD

        sub_lines_pre = _wrap(c, subtitle, SUB_FS, INNER_W - 4*mm)
        sub_h = len(sub_lines_pre) * SUB_FS * 1.4 + 1*mm

        def _line_h(ln):
            if ln == "":
                return BODY_FS * 0.7
            is_bullet  = ln.startswith("■")
            is_heading = ln.startswith("【") and ln.endswith("】")
            x_off = 8*mm if is_bullet else 5*mm
            gap   = BODY_FS * 1.4 if is_heading else BODY_FS * 1.25
            max_w = INNER_W - (x_off - 5*mm + 2*mm)
            wrapped = _wrap(c, ln, BODY_FS, max_w)
            return len(wrapped) * gap

        body_h = sum(_line_h(ln) for ln in body_only)
        hash_section = (2*mm + 2*mm + 6*mm) if hash_text else 2*mm
        header_h = PAD + 6.5*mm + 5.5*mm + sub_h + 3*mm
        total = header_h + body_h + hash_section + 6*mm

        self._check(total + 6*mm)
        box_y = self.y - total

        # Card shadow
        c.setFillColor(HexColor("#C8CBD0"))
        c.roundRect(ML + 1*mm, box_y - 1*mm, TW, total, 3*mm, fill=1, stroke=0)

        # Card body
        c.setFillColor(COL_CARD)
        c.roundRect(ML, box_y, TW, total, 3*mm, fill=1, stroke=0)

        # Left accent bar
        c.setFillColor(acc)
        c.rect(ML, box_y, 3*mm, total, fill=1, stroke=0)
        c.roundRect(ML, box_y, 3*mm, total, 1.5*mm, fill=1, stroke=0)

        ty = box_y + total - PAD

        # Code badge
        badge_w = 22*mm
        c.setFillColor(acc)
        c.roundRect(ML + 5*mm, ty - 5.5*mm, badge_w, 5.5*mm, 1.5*mm, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("JA", 7)
        c.drawCentredString(ML + 5*mm + badge_w/2, ty - 3.5*mm, code)
        ty -= 6.5*mm

        # Category tag
        tag_w = pdfmetrics.stringWidth(category, "JA", 7) + 4*mm
        c.setFillColor(HexColor("#EEF1F5"))
        c.roundRect(ML + 5*mm, ty - 4.5*mm, tag_w, 4.5*mm, 1.5*mm, fill=1, stroke=0)
        c.setFillColor(acc); c.setFont("JA", 7)
        c.drawString(ML + 7*mm, ty - 3*mm, category)
        ty -= 5.5*mm

        # Subtitle
        sub_lines = _wrap(c, subtitle, SUB_FS, INNER_W - 4*mm)
        c.setFillColor(COL_HDR)
        for ln in sub_lines:
            c.setFont("JA", SUB_FS)
            c.drawString(ML + 5*mm, ty - SUB_FS, ln)
            ty -= SUB_FS * 1.4
        ty -= 1*mm

        # Divider
        c.setStrokeColor(COL_DIVIDER); c.setLineWidth(0.3)
        c.line(ML + 5*mm, ty, ML + TW - 5*mm, ty)
        ty -= 3*mm

        # Body text
        for ln in body_only:
            if ln == "":
                ty -= BODY_FS * 0.7
                continue
            is_bullet  = ln.startswith("■")
            is_heading = ln.startswith("【") and ln.endswith("】")

            if is_heading:
                c.setFillColor(acc)
                c.setFont("JA", BODY_FS + 0.5)
                c.drawString(ML + 5*mm, ty - BODY_FS, ln)
                ty -= BODY_FS * 1.4
            else:
                x_off = 8*mm if is_bullet else 5*mm
                c.setFillColor(acc if is_bullet else COL_BODY)
                wrapped = _wrap(c, ln, BODY_FS, INNER_W - (x_off - 5*mm + 2*mm))
                for wl in wrapped:
                    c.setFont("JA", BODY_FS)
                    c.drawString(ML + x_off, ty - BODY_FS, wl)
                    ty -= BODY_FS * 1.25

        ty -= 2*mm

        # Hashtag box
        if hash_text:
            c.setStrokeColor(HexColor("#AED6F1")); c.setLineWidth(0.3)
            c.line(ML + 5*mm, ty, ML + TW - 5*mm, ty)
            ty -= 2*mm
            box_h = 6*mm
            c.setFillColor(COL_HASH_BG)
            c.roundRect(ML + 4*mm, ty - box_h, TW - 8*mm, box_h, 1.5*mm, fill=1, stroke=0)
            c.setFillColor(COL_HASH); c.setFont("JA", 7.5)
            c.drawString(ML + 7*mm, ty - box_h + 2*mm, hash_text)

        self.y = box_y - 6*mm

    def save(self):
        self._pnum()
        self.c.save()


def parse_posts(md_path):
    text = Path(md_path).read_text(encoding="utf-8")
    pattern = re.compile(
        r"### (SR-\d+)\s+【([^】]+)】([^\n]+)\n+参考:\s*([^\n]+)\n+---\n+(.*?)\n+(#[^\n]+)\n+---",
        re.DOTALL
    )
    posts = []
    for m in pattern.finditer(text):
        code, cat, subtitle, source, body, hashtag = m.groups()
        posts.append({
            "code":     code.strip(),
            "category": cat.strip(),
            "subtitle": subtitle.strip(),
            "source":   source.strip(),
            "body":     body.strip(),
            "hashtag":  hashtag.strip(),
        })
    return posts


def main():
    md_path  = "marketing/content-plan/hajime-x-slump-recovery-posts.md"
    pdf_path = "marketing/content-plan/hajime-x-slump-recovery-posts.pdf"

    posts = parse_posts(md_path)
    print(f"Parsed {len(posts)} posts")

    pdf = SlumpRecoverPDF(pdf_path)
    pdf.draw_cover()

    for p in posts:
        pdf.draw_post(
            p["code"], p["category"], p["subtitle"],
            p["source"], p["body"], p["hashtag"]
        )

    pdf.save()
    size_kb = Path(pdf_path).stat().st_size // 1024
    print(f"Saved: {pdf_path}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
