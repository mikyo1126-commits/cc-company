#!/usr/bin/env python3
"""
反発相場×メンタル 緊急投稿集 PDF generator (RB-01〜RB-05)
Output: marketing/content-plan/hajime-x-rebound-posts.pdf
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

# Rebound / recovery color palette
COL_BG      = HexColor("#F0FDF4")
COL_CARD    = HexColor("#FFFFFF")
COL_HDR     = HexColor("#0A1F14")
COL_BODY    = HexColor("#1C2E22")
COL_SOURCE  = HexColor("#6B8C74")
COL_DIVIDER = HexColor("#A8D5B5")
COL_HASH_BG = HexColor("#E8F4FD")
COL_HASH    = HexColor("#1A5276")

ACCENT      = HexColor("#1E8449")
ACCENT_DARK = HexColor("#145A32")
ACCENT2     = HexColor("#2E86C1")

CATEGORY_COLORS = {
    "FOMO":             HexColor("#1F618D"),
    "平均回帰バイアス": HexColor("#1E8449"),
    "ディスポジション効果": HexColor("#6C3483"),
    "確証バイアス":     HexColor("#B7950B"),
    "恐怖の記憶":       HexColor("#17A589"),
}

INDEX = [
    ("RB-01", "FOMO",             "反発を「見逃した」という感覚が次のトレードを壊す"),
    ("RB-02", "平均回帰バイアス", "「暴落後は必ず戻る」という確信が判断を狂わせる理由"),
    ("RB-03", "ディスポジション効果", "反発局面で「利確が早すぎる」トレーダーに共通すること"),
    ("RB-04", "確証バイアス",     "「底打ちサイン」を見つけたがる脳が相場判断を歪める"),
    ("RB-05", "恐怖の記憶",       "暴落後のトレーダーが陥る「過剰な慎重さ」の正体"),
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


class ReboundPostPDF:
    def __init__(self, filename):
        self.c    = canvas.Canvas(filename, pagesize=A4)
        self.c.setTitle("はじめさん 反発相場×メンタル 緊急投稿集（RB-01〜RB-05）")
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
        c.rect(0, H - 75*mm, W, 75*mm, fill=1, stroke=0)
        # Accent stripes
        c.setFillColor(ACCENT)
        c.rect(0, H - 75*mm, W, 3*mm, fill=1, stroke=0)
        c.setFillColor(ACCENT2)
        c.rect(0, H - 75*mm + 3*mm, W, 1*mm, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("JA", 9)
        c.drawCentredString(W/2, H - 18*mm, "はじめさん X投稿  緊急版")
        c.setFont("JA", 16)
        c.drawCentredString(W/2, H - 31*mm, "反発相場 × メンタル 緊急投稿集")
        c.setFillColor(HexColor("#A9DFBF"))
        c.setFont("JA", 8.5)
        c.drawCentredString(W/2, H - 42*mm,
            "BTC $63,700（+2.8%反発） / S&P500 7,609（+3%回復） / TSMC +30%上方修正")
        c.setFillColor(HexColor("#AED6F1"))
        c.setFont("JA", 7.5)
        c.drawCentredString(W/2, H - 53*mm,
            "RB-01〜RB-05（5本）  2026年6月8日 作成")

        # Stats bar
        c.setFillColor(white)
        bx, by, bw, bh = ML, H - 103*mm, TW, 19*mm
        c.roundRect(bx, by, bw, bh, 3*mm, fill=1, stroke=0)
        stats = [("5本", "緊急投稿"), ("反発心理", "テーマ"), ("脳科学", "科学的根拠"), ("リアルタイム", "データ活用")]
        cw = TW / 4
        for i, (num, lbl) in enumerate(stats):
            cx = bx + cw * i + cw / 2
            c.setFont("JA", 10); c.setFillColor(COL_HDR)
            c.drawCentredString(cx, by + 11*mm, num)
            c.setFont("JA", 6); c.setFillColor(COL_SOURCE)
            c.drawCentredString(cx, by + 4*mm, lbl)

        # Index table
        y = H - 115*mm
        c.setFillColor(ACCENT_DARK)
        c.rect(ML, y - 7*mm, TW, 7*mm, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("JA", 8)
        c.drawString(ML + 4*mm, y - 4.5*mm, "投稿インデックス（RB-01〜RB-05）")
        y -= 8*mm

        col_code  = 16*mm
        col_cat   = 38*mm
        col_title_w = TW - col_code - col_cat - 6*mm

        for idx, (code, cat, title) in enumerate(INDEX):
            row_h = 10*mm
            bg = white if idx % 2 == 0 else HexColor("#E9F7EF")
            c.setFillColor(bg)
            c.rect(ML, y - row_h, TW, row_h, fill=1, stroke=0)

            acc = CATEGORY_COLORS.get(cat, ACCENT)
            c.setFillColor(acc)
            c.roundRect(ML + 2*mm, y - row_h + 2.5*mm, col_code - 2*mm, 5*mm, 1*mm, fill=1, stroke=0)
            c.setFillColor(white); c.setFont("JA", 6.5)
            c.drawCentredString(ML + 2*mm + (col_code - 2*mm)/2, y - row_h + 4*mm, code)

            c.setFillColor(COL_SOURCE); c.setFont("JA", 6.5)
            c.drawString(ML + col_code + 2*mm, y - row_h + 4*mm, cat)

            c.setFillColor(COL_BODY); c.setFont("JA", 7)
            title_str = title if pdfmetrics.stringWidth(title, "JA", 7) <= col_title_w else title[:22] + "…"
            c.drawString(ML + col_code + col_cat, y - row_h + 4*mm, title_str)

            y -= row_h

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
        c.setFillColor(HexColor("#C3D9C3"))
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
        c.setFillColor(HexColor("#E9F7EF"))
        c.roundRect(ML + 5*mm, ty - 4.5*mm, tag_w, 4.5*mm, 1.5*mm, fill=1, stroke=0)
        c.setFillColor(ACCENT_DARK); c.setFont("JA", 7)
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
        r"### (RB-\d+)\s+【([^】]+)】([^\n]+)\n+参考:\s*([^\n]+)\n+---\n+(.*?)\n+(#[^\n]+)\n+---",
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
    md_path  = "marketing/content-plan/hajime-x-rebound-posts.md"
    pdf_path = "marketing/content-plan/hajime-x-rebound-posts.pdf"

    posts = parse_posts(md_path)
    print(f"Parsed {len(posts)} posts")

    pdf = ReboundPostPDF(pdf_path)
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
