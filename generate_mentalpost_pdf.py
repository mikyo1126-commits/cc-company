#!/usr/bin/env python3
"""
トレード×メンタル 深層解説 投稿集 PDF generator (TM-01〜TM-20)
Output: marketing/content-plan/hajime-x-mentalpost-posts.pdf
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
COL_BG      = HexColor("#F0F4F8")
COL_CARD    = HexColor("#FFFFFF")
COL_HDR     = HexColor("#1A1A2E")
COL_BODY    = HexColor("#2C3E50")
COL_SOURCE  = HexColor("#7F8C8D")
COL_DIVIDER = HexColor("#BDC3C7")
COL_HASH_BG = HexColor("#E8F4F8")
COL_HASH    = HexColor("#1A5276")

# Mental theme accent — psychology blue / teal
ACCENT      = HexColor("#2980B9")
ACCENT_DARK = HexColor("#1A5276")
ACCENT_MINT = HexColor("#1ABC9C")

CATEGORY_COLORS = {
    "リベンジトレード": HexColor("#C0392B"),
    "損失回避":         HexColor("#E67E22"),
    "過信の錯覚":       HexColor("#8E44AD"),
    "サンクコスト":     HexColor("#7D6608"),
    "ディスポジション効果": HexColor("#1E8449"),
    "確証バイアス":     HexColor("#2980B9"),
    "アンカリング":     HexColor("#117A65"),
    "過信バイアス":     HexColor("#884EA0"),
    "意思決定疲労":     HexColor("#2E4053"),
    "どうにでもなれ効果": HexColor("#A93226"),
    "メタ認知":         HexColor("#1A5276"),
    "習慣化":           HexColor("#0E6655"),
    "睡眠":             HexColor("#1B2631"),
    "ネガティビティバイアス": HexColor("#7B241C"),
    "現在バイアス":     HexColor("#1F618D"),
    "脳の構造":         HexColor("#4A235A"),
    "確率の現実":       HexColor("#0B5345"),
    "二重プロセス":     HexColor("#2C3E50"),
    "情報過負荷":       HexColor("#515A5A"),
    "自己効力感":       HexColor("#1A5276"),
}

INDEX = [
    ("TM-01", "リベンジトレード", "リベンジトレードが「悪癖」に変わるまでの脳の仕組み"),
    ("TM-02", "損失回避",         "なぜ人は損失を利益の2倍怖く感じるのか"),
    ("TM-03", "過信の錯覚",       "「自分だけは9割に入らない」という錯覚の正体"),
    ("TM-04", "サンクコスト",     "すでに損した金額が判断を狂わせる理由"),
    ("TM-05", "ディスポジション効果", "利益は早く確定して損失を伸ばしてしまう理由"),
    ("TM-06", "確証バイアス",     "自分に都合いいチャートしか見えない理由"),
    ("TM-07", "アンカリング",     "「あの値段で買ったから」が損切りを遅らせる理由"),
    ("TM-08", "過信バイアス",     "連勝後に大きく負けるトレーダーに共通すること"),
    ("TM-09", "意思決定疲労",     "1日に何度もエントリー判断すると脳は劣化する"),
    ("TM-10", "どうにでもなれ効果", "一度ルールを破ると全部崩れる理由"),
    ("TM-11", "メタ認知",         "トレード後に「感情の記録」をつける人が上達する理由"),
    ("TM-12", "習慣化",           "プロトレーダーが同じルーティンを繰り返す脳科学的理由"),
    ("TM-13", "睡眠",             "睡眠6時間未満で判断力が大幅に落ちるという事実"),
    ("TM-14", "ネガティビティバイアス", "損失ニュースが利益より3倍刺さる理由"),
    ("TM-15", "現在バイアス",     "「今すぐ入りたい」衝動が長期利益を破壊する理由"),
    ("TM-16", "脳の構造",         "相場の「恐怖と欲」は脳のどこから来るのか"),
    ("TM-17", "確率の現実",       "サイコロで売買を決めると長期的に必ず負ける理由"),
    ("TM-18", "二重プロセス",     "「わかっているのにできない」の正体"),
    ("TM-19", "情報過負荷",       "チャートに線を引けば引くほど判断できなくなる理由"),
    ("TM-20", "自己効力感",       "「自分には無理」という信念がトレードを壊す構造"),
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


class MentalPostPDF:
    def __init__(self, filename):
        self.c    = canvas.Canvas(filename, pagesize=A4)
        self.c.setTitle("はじめさん トレード×メンタル 深層解説 投稿集（TM-01〜TM-20）")
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
        c.setFillColor(ACCENT_MINT)
        c.rect(0, H - 75*mm + 3*mm, W, 1*mm, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("JA", 9)
        c.drawCentredString(W/2, H - 18*mm, "はじめさん X投稿")
        c.setFont("JA", 17)
        c.drawCentredString(W/2, H - 31*mm, "トレード×メンタル 深層解説 投稿集")
        c.setFillColor(ACCENT_MINT)
        c.setFont("JA", 8.5)
        c.drawCentredString(W/2, H - 42*mm, "@nihontoshiconsa スタイル参考  ／  脳科学・認知バイアス×FX")
        c.setFillColor(HexColor("#AEB6BF"))
        c.setFont("JA", 7.5)
        c.drawCentredString(W/2, H - 53*mm, "TM-01〜TM-20（20本）")

        # Stats bar
        c.setFillColor(white)
        bx, by, bw, bh = ML, H - 103*mm, TW, 19*mm
        c.roundRect(bx, by, bw, bh, 3*mm, fill=1, stroke=0)
        stats = [("20本", "投稿総数"), ("認知バイアス", "解説テーマ"), ("脳科学", "科学的根拠"), ("バズ設計", "Xアルゴリズム対応")]
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
        c.drawString(ML + 4*mm, y - 4.5*mm, "投稿インデックス（TM-01〜TM-20）")
        y -= 8*mm

        col_code = 16*mm
        col_cat  = 33*mm
        col_title_w = TW - col_code - col_cat - 6*mm

        for idx, (code, cat, title) in enumerate(INDEX):
            row_h = 8*mm
            bg = white if idx % 2 == 0 else HexColor("#EBF5FB")
            c.setFillColor(bg)
            c.rect(ML, y - row_h, TW, row_h, fill=1, stroke=0)

            # code badge
            acc = CATEGORY_COLORS.get(cat, ACCENT)
            c.setFillColor(acc)
            c.roundRect(ML + 2*mm, y - row_h + 1.5*mm, col_code - 2*mm, 5*mm, 1*mm, fill=1, stroke=0)
            c.setFillColor(white); c.setFont("JA", 6.5)
            c.drawCentredString(ML + 2*mm + (col_code - 2*mm)/2, y - row_h + 3*mm, code)

            # category
            c.setFillColor(COL_SOURCE); c.setFont("JA", 6.5)
            c.drawString(ML + col_code + 2*mm, y - row_h + 3*mm, cat)

            # title
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

        # Pre-calculate heights
        BODY_FS   = 8.5
        SUB_FS    = 8.0
        PAD       = 4*mm
        INNER_W   = TW - 2*PAD

        # Subtitle height (exact, matching drawing loop)
        sub_lines_pre = _wrap(c, subtitle, SUB_FS, INNER_W - 4*mm)
        sub_h = len(sub_lines_pre) * SUB_FS * 1.4 + 1*mm

        # Body height (exact same widths and spacing as drawing loop)
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

        # Hash section: divider-gap + line-gap + box
        hash_section = (2*mm + 2*mm + 6*mm) if hash_text else 2*mm

        # Header: pad + badge + tag + subtitle + divider
        header_h = PAD + 6.5*mm + 5.5*mm + sub_h + 3*mm

        total = header_h + body_h + hash_section + 6*mm  # 6mm bottom pad

        self._check(total + 6*mm)
        box_y = self.y - total

        # Card shadow
        c.setFillColor(HexColor("#C8D6E5"))
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
        c.setFillColor(HexColor("#EBF5FB"))
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
            is_header  = ln.startswith("【") and "】" in ln and not ln.endswith("】")

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
            c.setStrokeColor(HexColor("#D6EAF8")); c.setLineWidth(0.3)
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
        r"### (TM-\d+)\s+【([^】]+)】([^\n]+)\n+参考:\s*([^\n]+)\n+---\n+(.*?)\n+(#[^\n]+)\n+---",
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
    md_path  = "marketing/content-plan/hajime-x-mentalpost-posts.md"
    pdf_path = "marketing/content-plan/hajime-x-mentalpost-posts.pdf"

    posts = parse_posts(md_path)
    print(f"Parsed {len(posts)} posts")

    pdf = MentalPostPDF(pdf_path)
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
