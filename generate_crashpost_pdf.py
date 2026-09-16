#!/usr/bin/env python3
"""
暴落相場×メンタル 緊急投稿集 PDF generator (CR-01〜CR-10)
Output: marketing/content-plan/hajime-x-crashpost-posts.pdf
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

# Crisis color palette
COL_BG      = HexColor("#FDF2F2")
COL_CARD    = HexColor("#FFFFFF")
COL_HDR     = HexColor("#1A0A0A")
COL_BODY    = HexColor("#2C2323")
COL_SOURCE  = HexColor("#7F6B6B")
COL_DIVIDER = HexColor("#D5BFBF")
COL_HASH_BG = HexColor("#FEF0E7")
COL_HASH    = HexColor("#7B241C")

ACCENT      = HexColor("#C0392B")
ACCENT_DARK = HexColor("#7B241C")
ACCENT_GOLD = HexColor("#E67E22")

CATEGORY_COLORS = {
    "パニック心理":       HexColor("#C0392B"),
    "後知恵バイアス":     HexColor("#A93226"),
    "アンカリング":       HexColor("#1F618D"),
    "情報バイアス":       HexColor("#515A5A"),
    "群集心理":           HexColor("#7D6608"),
    "ギャンブラーの誤謬": HexColor("#884EA0"),
    "特殊性バイアス":     HexColor("#2E4053"),
    "行動バイアス":       HexColor("#0B5345"),
    "メタ認知":           HexColor("#4A235A"),
    "扁桃体反応":         HexColor("#922B21"),
}

INDEX = [
    ("CR-01", "パニック心理",       "暴落中に「今が底だ」と感じてしまう脳の仕組み"),
    ("CR-02", "後知恵バイアス",     "暴落後に「わかっていた」と言う人が必ず現れる理由"),
    ("CR-03", "アンカリング",       "ビットコインが$69,000から落ちても損切りできない心理"),
    ("CR-04", "情報バイアス",       "暴落ニュースを見れば見るほど判断が狂う仕組み"),
    ("CR-05", "群集心理",           "ゴールドが最高値のときに「買いたい」と思う心理の正体"),
    ("CR-06", "ギャンブラーの誤謬", "暴落後こそポジションを大きくしたくなる危険な錯覚"),
    ("CR-07", "特殊性バイアス",     "「今回の暴落は違う」と毎回言いたくなる心理の正体"),
    ("CR-08", "行動バイアス",       "暴落相場で「何もしない」が最強の選択肢になる理由"),
    ("CR-09", "メタ認知",           "相場が怖いとき「感情の記録」が機能する脳科学的理由"),
    ("CR-10", "扁桃体反応",         "暴落中に「全部売りたい」衝動が起きる脳の仕組み"),
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


class CrashPostPDF:
    def __init__(self, filename):
        self.c    = canvas.Canvas(filename, pagesize=A4)
        self.c.setTitle("はじめさん 暴落相場×メンタル 緊急投稿集（CR-01〜CR-10）")
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
        # Accent stripe
        c.setFillColor(ACCENT)
        c.rect(0, H - 75*mm, W, 3*mm, fill=1, stroke=0)
        c.setFillColor(ACCENT_GOLD)
        c.rect(0, H - 75*mm + 3*mm, W, 1*mm, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("JA", 9)
        c.drawCentredString(W/2, H - 18*mm, "はじめさん X投稿  緊急版")
        c.setFont("JA", 16)
        c.drawCentredString(W/2, H - 31*mm, "暴落相場 × メンタル 緊急投稿集")
        c.setFillColor(ACCENT_GOLD)
        c.setFont("JA", 8.5)
        c.drawCentredString(W/2, H - 42*mm, "BTC -10% / S&P500 -2.6% / 金最高値  ／  脳科学・認知バイアス×暴落心理")
        c.setFillColor(HexColor("#F1948A"))
        c.setFont("JA", 7.5)
        c.drawCentredString(W/2, H - 53*mm, "CR-01〜CR-10（10本）  2026年6月 緊急作成")

        # Stats bar
        c.setFillColor(white)
        bx, by, bw, bh = ML, H - 103*mm, TW, 19*mm
        c.roundRect(bx, by, bw, bh, 3*mm, fill=1, stroke=0)
        stats = [("10本", "緊急投稿"), ("暴落心理", "テーマ"), ("脳科学", "科学的根拠"), ("トレンド乗り", "タイムリー")]
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
        c.drawString(ML + 4*mm, y - 4.5*mm, "投稿インデックス（CR-01〜CR-10）")
        y -= 8*mm

        col_code = 16*mm
        col_cat  = 33*mm
        col_title_w = TW - col_code - col_cat - 6*mm

        for idx, (code, cat, title) in enumerate(INDEX):
            row_h = 8*mm
            bg = white if idx % 2 == 0 else HexColor("#FDEDEC")
            c.setFillColor(bg)
            c.rect(ML, y - row_h, TW, row_h, fill=1, stroke=0)

            acc = CATEGORY_COLORS.get(cat, ACCENT)
            c.setFillColor(acc)
            c.roundRect(ML + 2*mm, y - row_h + 1.5*mm, col_code - 2*mm, 5*mm, 1*mm, fill=1, stroke=0)
            c.setFillColor(white); c.setFont("JA", 6.5)
            c.drawCentredString(ML + 2*mm + (col_code - 2*mm)/2, y - row_h + 3*mm, code)

            c.setFillColor(COL_SOURCE); c.setFont("JA", 6.5)
            c.drawString(ML + col_code + 2*mm, y - row_h + 3*mm, cat)

            c.setFillColor(COL_BODY); c.setFont("JA", 6.5)
            title_str = title if pdfmetrics.stringWidth(title, "JA", 6.5) <= col_title_w else title[:24] + "…"
            c.drawString(ML + col_code + col_cat, y - row_h + 3*mm, title_str)

            y -= row_h
            if y < MB + 5*mm:
                break

        self._pnum()
        c.showPage()
        self.page += 1
        self._bg()
        self.y = H - MT

    def draw_post(self, code, category, subtitle, source, body, hashtag):
        c = self.c
        acc = CATEGORY_COLORS.get(category, ACCENT)

        body_lines  = body.strip().split("\n")
        hash_lines  = [l for l in body_lines if l.startswith("#")]
        body_only   = [l for l in body_lines if not l.startswith("#")]
        hash_text   = " ".join(hash_lines)

        BODY_FS   = 8.5
        SUB_FS    = 8.0
        PAD       = 4*mm
        INNER_W   = TW - 2*PAD

        sub_lines_pre = _wrap(c, subtitle, SUB_FS, INNER_W - 4*mm)
        sub_h = len(sub_lines_pre) * SUB_FS * 1.4 + 1*mm

        def _line_h(ln):
            if ln == "":
                return BODY_FS * 0.7
            is_bullet   = ln.startswith("■")
            is_heading  = ln.startswith("【") and ln.endswith("】")
            x_off = 8*mm if is_bullet else 5*mm
            fs    = BODY_FS
            gap   = BODY_FS * 1.4 if is_heading else BODY_FS * 1.25
            max_w = INNER_W - (x_off - 5*mm + 2*mm)
            wrapped = _wrap(c, ln, fs, max_w)
            return len(wrapped) * gap

        body_h = sum(_line_h(ln) for ln in body_only)

        hash_section = (2*mm + 2*mm + 6*mm) if hash_text else 2*mm
        header_h = PAD + 6.5*mm + 5.5*mm + sub_h + 3*mm
        total = header_h + body_h + hash_section + 6*mm

        self._check(total + 6*mm)
        box_y = self.y - total

        # Card shadow
        c.setFillColor(HexColor("#E8C3C3"))
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
        c.setFillColor(HexColor("#FDEDEC"))
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
                fs    = BODY_FS
                c.setFillColor(acc if is_bullet else COL_BODY)
                wrapped = _wrap(c, ln, fs, INNER_W - (x_off - 5*mm + 2*mm))
                for i, wl in enumerate(wrapped):
                    c.setFont("JA", fs)
                    c.drawString(ML + x_off, ty - fs, wl)
                    ty -= fs * 1.25

        ty -= 2*mm

        # Hashtag box
        if hash_text:
            c.setStrokeColor(HexColor("#F5CBA7")); c.setLineWidth(0.3)
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
        r"### (CR-\d+)\s+【([^】]+)】([^\n]+)\n+参考:\s*([^\n]+)\n+---\n+(.*?)\n+(#[^\n]+)\n+---",
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
    md_path  = "marketing/content-plan/hajime-x-crashpost-posts.md"
    pdf_path = "marketing/content-plan/hajime-x-crashpost-posts.pdf"

    posts = parse_posts(md_path)
    print(f"Parsed {len(posts)} posts")

    pdf = CrashPostPDF(pdf_path)
    pdf.draw_cover()

    for p in posts:
        pdf.draw_post(
            p["code"], p["category"], p["subtitle"],
            p["source"], p["body"], p["hashtag"]
        )

    pdf.save()
    print(f"Saved: {pdf_path}")


if __name__ == "__main__":
    main()
