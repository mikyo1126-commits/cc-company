#!/usr/bin/env python3
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_PATH = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
pdfmetrics.registerFont(TTFont("JA", FONT_PATH))

W, H = A4
MARGIN_L = 18 * mm
MARGIN_R = 18 * mm
MARGIN_T = 22 * mm
MARGIN_B = 18 * mm
TEXT_W = W - MARGIN_L - MARGIN_R

# Deep Dive color palette
COL_BG       = HexColor("#F4F6F9")   # page bg
COL_CARD     = HexColor("#FFFFFF")   # card bg
COL_SHADOW   = HexColor("#D0D7E3")
COL_HDR      = HexColor("#0D1B2A")   # dark navy header
COL_BADGE    = HexColor("#C0392B")   # deep red badge
COL_BADGE_TX = white
COL_TITLE    = HexColor("#0D1B2A")
COL_BODY     = HexColor("#2C3E50")
COL_SOURCE   = HexColor("#7F8C8D")
COL_HASH_BG  = HexColor("#EAF2FF")
COL_HASH     = HexColor("#1A5276")
COL_DIVIDER  = HexColor("#BDC3C7")
COL_ACCENT   = HexColor("#E67E22")   # orange accent line

CATEGORY_COLORS = {
    "スマートマネー": HexColor("#6C3483"),
    "ローソク足":    HexColor("#1A5276"),
    "環境認識":      HexColor("#1E8449"),
    "資金管理":      HexColor("#B7950B"),
    "数学":          HexColor("#117A65"),
    "時間帯":        HexColor("#784212"),
    "チャートパターン": HexColor("#6E2F1A"),
    "心理学":        HexColor("#922B21"),
    "検証":          HexColor("#2C3E50"),
    "生存戦略":      HexColor("#0E6251"),
}


class DeepDivePDF:
    def __init__(self, filename):
        self.c = canvas.Canvas(filename, pagesize=A4)
        self.c.setTitle("はじめさん DEEP DIVE 徹底解説投稿集（10本）")
        self.y = H - MARGIN_T
        self.page = 1
        self._new_page_bg()

    def _new_page_bg(self):
        self.c.setFillColor(COL_BG)
        self.c.rect(0, 0, W, H, fill=1, stroke=0)
        self.c.setFillColor(black)

    def _check_space(self, needed):
        if self.y - needed < MARGIN_B:
            self.page_number()
            self.c.showPage()
            self.page += 1
            self._new_page_bg()
            self.y = H - MARGIN_T

    def _wrap_text(self, text, font_size, max_w):
        self.c.setFont("JA", font_size)
        lines = []
        for para in text.split("\n"):
            if para == "":
                lines.append("")
                continue
            cur = ""
            for ch in para:
                test = cur + ch
                if pdfmetrics.stringWidth(test, "JA", font_size) > max_w:
                    lines.append(cur)
                    cur = ch
                else:
                    cur = test
            lines.append(cur)
        return lines

    def draw_cover(self, posts):
        # Header
        self.c.setFillColor(COL_HDR)
        self.c.rect(0, H - 85*mm, W, 85*mm, fill=1, stroke=0)

        # Accent stripe
        self.c.setFillColor(COL_ACCENT)
        self.c.rect(0, H - 85*mm, W, 3*mm, fill=1, stroke=0)

        self.c.setFillColor(white)
        self.c.setFont("JA", 11)
        self.c.drawCentredString(W/2, H - 22*mm, "はじめさん X投稿")
        self.c.setFont("JA", 20)
        self.c.drawCentredString(W/2, H - 36*mm, "DEEP DIVE  徹底解説投稿集")
        self.c.setFont("JA", 9)
        self.c.setFillColor(HexColor("#AEB6BF"))
        self.c.drawCentredString(W/2, H - 50*mm, "日本・海外 5000フォロワー以上アカウント分析に基づく「深層教育コンテンツ」10本")
        self.c.setFont("JA", 8)
        self.c.drawCentredString(W/2, H - 62*mm,
            "参考: @FxRumasan / @mochi_fxtrader / @hitsuzikai / @PeterLBrandt / @I_Am_The_ICT")

        # Stats bar
        self.c.setFillColor(white)
        bx, by, bw, bh = MARGIN_L, H - 115*mm, TEXT_W, 22*mm
        self.c.roundRect(bx, by, bw, bh, 3*mm, fill=1, stroke=0)
        cols = [
            ("10本", "DEEP DIVE投稿"),
            ("5アカウント", "参考分析"),
            ("日本+海外", "調査範囲"),
            ("500〜800字", "1投稿あたり文字数"),
        ]
        col_w = TEXT_W / len(cols)
        for i, (num, label) in enumerate(cols):
            cx = bx + col_w * i + col_w / 2
            self.c.setFont("JA", 12)
            self.c.setFillColor(COL_HDR)
            self.c.drawCentredString(cx, by + 13*mm, num)
            self.c.setFont("JA", 6.5)
            self.c.setFillColor(COL_SOURCE)
            self.c.drawCentredString(cx, by + 6*mm, label)

        # Category legend
        y_leg = H - 130*mm
        self.c.setFont("JA", 8.5)
        self.c.setFillColor(COL_HDR)
        self.c.drawString(MARGIN_L, y_leg, "■ 投稿カテゴリ一覧")
        y_leg -= 7*mm

        cat_list = [
            ("DD-01", "スマートマネー", "流動性スイープ・機関の罠の仕組み"),
            ("DD-02", "ローソク足",    "機関投資家の心理をローソク足で読む"),
            ("DD-03", "環境認識",      "プロの4ステップMTF分析完全版"),
            ("DD-04", "資金管理",      "リスクリワード比の数学と心理"),
            ("DD-05", "数学",          "勝率60%でも破産する理由・ケリー基準"),
            ("DD-06", "時間帯",        "キルゾーン理論・プロが動く時間帯"),
            ("DD-07", "チャートパターン", "各パターンの実際の成功率データ"),
            ("DD-08", "心理学",        "損切りできない理由と行動経済学的解決"),
            ("DD-09", "検証",          "バックテストの落とし穴と正しい手順"),
            ("DD-10", "生存戦略",      "ドローダウン管理・10年生き残る法則"),
        ]

        col_cnt = 2
        col_w2 = TEXT_W / col_cnt
        for i, (code, cat, desc) in enumerate(cat_list):
            col = i % col_cnt
            row = i // col_cnt
            cx = MARGIN_L + col * col_w2
            cy = y_leg - row * 9*mm
            cat_col = CATEGORY_COLORS.get(cat, COL_HDR)
            self.c.setFillColor(cat_col)
            self.c.roundRect(cx, cy, 16*mm, 5*mm, 1*mm, fill=1, stroke=0)
            self.c.setFillColor(white)
            self.c.setFont("JA", 6)
            self.c.drawCentredString(cx + 8*mm, cy + 1.5*mm, code)
            self.c.setFillColor(COL_HDR)
            self.c.setFont("JA", 7.5)
            self.c.drawString(cx + 18*mm, cy + 1.5*mm, f"【{cat}】{desc}")

        self.c.showPage()
        self.page += 1
        self._new_page_bg()
        self.y = H - MARGIN_T

    def draw_post(self, code, category, ref, title, body, hashtag):
        cat_col = CATEGORY_COLORS.get(category, COL_HDR)

        # Separate body lines and calculate height
        hash_tag_lines = self._wrap_text(hashtag, 7.5, TEXT_W - 14*mm) if hashtag else []
        hash_box_h = (len(hash_tag_lines) * 4.8*mm + 4*mm + 3*mm) if hash_tag_lines else 0

        body_lines = self._wrap_text(body, 8.5, TEXT_W - 8*mm)
        title_lines = self._wrap_text(title, 10, TEXT_W - 12*mm)

        header_h = 13*mm
        title_h = len(title_lines) * 5.5*mm + 4*mm
        body_h = len(body_lines) * 5.2*mm + 4*mm
        ref_h = 6*mm
        total = header_h + title_h + body_h + ref_h + hash_box_h + 10*mm

        self._check_space(total)

        box_y = self.y - total

        # Shadow
        self.c.setFillColor(COL_SHADOW)
        self.c.roundRect(MARGIN_L + 1.5*mm, box_y - 1.5*mm, TEXT_W, total, 4*mm, fill=1, stroke=0)

        # Card bg
        self.c.setFillColor(COL_CARD)
        self.c.roundRect(MARGIN_L, box_y, TEXT_W, total, 4*mm, fill=1, stroke=0)

        # Left accent bar
        self.c.setFillColor(cat_col)
        self.c.rect(MARGIN_L, box_y, 3*mm, total, fill=1, stroke=0)
        self.c.roundRect(MARGIN_L, box_y, 3*mm, total, 2*mm, fill=1, stroke=0)

        # Header bar
        self.c.setFillColor(COL_HDR)
        self.c.roundRect(MARGIN_L, box_y + total - header_h, TEXT_W, header_h, 4*mm, fill=1, stroke=0)
        self.c.rect(MARGIN_L, box_y + total - header_h, TEXT_W, header_h / 2, fill=1, stroke=0)

        # DEEP DIVE badge
        badge_x = MARGIN_L + 5*mm
        badge_y = box_y + total - header_h + 3*mm
        self.c.setFillColor(COL_BADGE)
        self.c.roundRect(badge_x, badge_y, 22*mm, 5.5*mm, 1*mm, fill=1, stroke=0)
        self.c.setFillColor(white)
        self.c.setFont("JA", 6.5)
        self.c.drawCentredString(badge_x + 11*mm, badge_y + 1.5*mm, "DEEP DIVE")

        # Category badge
        cat_bx = badge_x + 24*mm
        self.c.setFillColor(cat_col)
        cat_label = f"【{category}】"
        cat_w = pdfmetrics.stringWidth(cat_label, "JA", 7) + 4*mm
        self.c.roundRect(cat_bx, badge_y, cat_w, 5.5*mm, 1*mm, fill=1, stroke=0)
        self.c.setFillColor(white)
        self.c.setFont("JA", 7)
        self.c.drawString(cat_bx + 2*mm, badge_y + 1.5*mm, cat_label)

        # Code label right
        self.c.setFillColor(HexColor("#AEB6BF"))
        self.c.setFont("JA", 8)
        self.c.drawRightString(MARGIN_L + TEXT_W - 4*mm, badge_y + 1.5*mm, code)

        # Title
        ty = box_y + total - header_h - 5.5*mm
        self.c.setFillColor(COL_TITLE)
        self.c.setFont("JA", 10)
        for tl in title_lines:
            self.c.drawString(MARGIN_L + 6*mm, ty, tl)
            ty -= 5.5*mm

        # Divider
        self.c.setStrokeColor(COL_ACCENT)
        self.c.setLineWidth(1.0)
        self.c.line(MARGIN_L + 6*mm, ty + 2*mm, MARGIN_L + 6*mm + 30*mm, ty + 2*mm)
        self.c.setStrokeColor(COL_DIVIDER)
        self.c.setLineWidth(0.4)
        self.c.line(MARGIN_L + 36*mm + 6*mm, ty + 2*mm, MARGIN_L + TEXT_W - 6*mm, ty + 2*mm)
        ty -= 4*mm

        # Body text
        self.c.setFont("JA", 8.5)
        stop_y = box_y + hash_box_h + ref_h + 3*mm
        for line in body_lines:
            if ty < stop_y:
                break
            if line.startswith("■") or line.startswith("【"):
                self.c.setFillColor(cat_col)
            elif line.startswith("①") or line.startswith("②") or line.startswith("③"):
                self.c.setFillColor(COL_ACCENT)
            else:
                self.c.setFillColor(COL_BODY)
            self.c.drawString(MARGIN_L + 6*mm, ty, line)
            ty -= 5.2*mm

        # Reference line
        ref_y = box_y + hash_box_h + 3*mm
        self.c.setStrokeColor(COL_DIVIDER)
        self.c.setLineWidth(0.3)
        self.c.line(MARGIN_L + 6*mm, ref_y + 5*mm, MARGIN_L + TEXT_W - 6*mm, ref_y + 5*mm)
        self.c.setFillColor(COL_SOURCE)
        self.c.setFont("JA", 6.5)
        self.c.drawString(MARGIN_L + 6*mm, ref_y + 1.5*mm, f"参考: {ref}")

        # Hashtag box
        if hash_tag_lines:
            inner_h = len(hash_tag_lines) * 4.8*mm + 4*mm
            tag_y = box_y + 3*mm
            self.c.setFillColor(COL_HASH_BG)
            self.c.roundRect(MARGIN_L + 6*mm, tag_y, TEXT_W - 12*mm, inner_h, 2*mm, fill=1, stroke=0)
            self.c.setFillColor(COL_HASH)
            self.c.setFont("JA", 7.5)
            text_y = tag_y + inner_h - 4*mm
            for tl in hash_tag_lines:
                self.c.drawString(MARGIN_L + 9*mm, text_y, tl)
                text_y -= 4.8*mm

        self.y = box_y - 6*mm

    def page_number(self):
        self.c.setFont("JA", 7)
        self.c.setFillColor(COL_SOURCE)
        self.c.drawCentredString(W / 2, 10*mm, f"- {self.page} -")

    def save(self):
        self.page_number()
        self.c.save()


def parse_deepdive(filepath):
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    posts = []
    pattern = re.compile(
        r"### (DD-\d+)\s+【([^】]+)】([^\n]+)\n+"
        r"参考:\s*([^\n]+)\n+"
        r"---\n+"
        r"(.*?)\n+"
        r"(#[^\n]+)\n+"
        r"---",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        code     = m.group(1).strip()
        category = m.group(2).strip()
        title    = m.group(3).strip()
        ref      = m.group(4).strip()
        body     = m.group(5).strip()
        hashtag  = m.group(6).strip()
        posts.append((code, category, ref, title, body, hashtag))
    return posts


if __name__ == "__main__":
    INPUT  = "/home/user/cc-company/marketing/content-plan/hajime-x-deepdive-posts.md"
    OUTPUT = "/home/user/cc-company/marketing/content-plan/hajime-x-deepdive-posts.pdf"

    posts = parse_deepdive(INPUT)
    print(f"Parsed {len(posts)} deep dive posts")

    maker = DeepDivePDF(OUTPUT)
    maker.draw_cover(posts)

    for post in posts:
        maker.draw_post(*post)

    maker.save()
    print(f"PDF saved: {OUTPUT}")
