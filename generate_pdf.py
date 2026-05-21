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

# Colors
COL_MORNING = HexColor("#FFF3E0")   # 朝 - 淡オレンジ
COL_EVENING = HexColor("#E8EAF6")   # 夜 - 淡パープル
COL_MORNING_H = HexColor("#E65100") # 朝ヘッダー
COL_EVENING_H = HexColor("#283593") # 夜ヘッダー
COL_AFFILIATE = HexColor("#E8F5E9") # アフィリ - 淡グリーン
COL_AFFILIATE_H = HexColor("#2E7D32")
COL_TITLE = HexColor("#212121")
COL_META = HexColor("#757575")
COL_HR = HexColor("#BDBDBD")
COL_HASH = HexColor("#1565C0")
COL_PAGE_BG = HexColor("#FAFAFA")

class PDFMaker:
    def __init__(self, filename):
        self.c = canvas.Canvas(filename, pagesize=A4)
        self.c.setTitle("はじめさん X投稿 2週間分（28本）")
        self.y = H - MARGIN_T
        self.page = 1
        self._new_page_bg()

    def _new_page_bg(self):
        self.c.setFillColor(COL_PAGE_BG)
        self.c.rect(0, 0, W, H, fill=1, stroke=0)
        self.c.setFillColor(black)

    def _check_space(self, needed):
        if self.y - needed < MARGIN_B:
            self.c.showPage()
            self.page += 1
            self._new_page_bg()
            self.y = H - MARGIN_T
            return True
        return False

    def _font(self, size, bold=False):
        self.c.setFont("JA", size)

    def draw_cover(self):
        # Cover page gradient-like header bar
        self.c.setFillColor(HexColor("#1A237E"))
        self.c.rect(0, H - 80*mm, W, 80*mm, fill=1, stroke=0)

        self.c.setFillColor(white)
        self.c.setFont("JA", 22)
        self.c.drawCentredString(W/2, H - 35*mm, "はじめさん X投稿")
        self.c.setFont("JA", 16)
        self.c.drawCentredString(W/2, H - 48*mm, "2週間コンテンツプラン（新規28本）")
        self.c.setFont("JA", 10)
        self.c.setFillColor(HexColor("#C5CAE9"))
        self.c.drawCentredString(W/2, H - 62*mm, "既存103本と重複なし ｜ @FxRumasan スタイル参考 ｜ はじめさん文体")

        # Stats box
        self.c.setFillColor(white)
        bx, by, bw, bh = MARGIN_L, H - 120*mm, TEXT_W, 28*mm
        self.c.roundRect(bx, by, bw, bh, 4*mm, fill=1, stroke=0)
        self.c.setFillColor(HexColor("#1A237E"))
        cols = [
            ("28本", "投稿総数"),
            ("14本", "朝8時（テクニカル）"),
            ("14本", "夜21時（マインド）"),
            ("2本", "アフィリエイト誘導"),
        ]
        col_w = TEXT_W / len(cols)
        for i, (num, label) in enumerate(cols):
            cx = bx + col_w * i + col_w / 2
            self.c.setFont("JA", 14)
            self.c.setFillColor(HexColor("#1A237E"))
            self.c.drawCentredString(cx, by + 16*mm, num)
            self.c.setFont("JA", 7)
            self.c.setFillColor(COL_META)
            self.c.drawCentredString(cx, by + 9*mm, label)

        # Legend
        y_leg = H - 138*mm
        legends = [
            (COL_MORNING_H, "🌅 朝投稿（おはようございます）"),
            (COL_EVENING_H, "🌙 夜投稿・マインド（お疲れ様です）"),
            (HexColor("#1B5E20"), "🌙 夜投稿・用語解説（こんばんは）"),
            (COL_AFFILIATE_H, "🔗 アフィリエイト誘導あり"),
        ]
        self.c.setFont("JA", 8)
        for i, (col, text) in enumerate(legends):
            lx = MARGIN_L + (i % 2) * (TEXT_W / 2)
            ly = y_leg - (i // 2) * 10*mm
            self.c.setFillColor(col)
            self.c.rect(lx, ly + 1*mm, 4*mm, 4*mm, fill=1, stroke=0)
            self.c.setFillColor(COL_TITLE)
            self.c.drawString(lx + 6*mm, ly + 1.5*mm, text)

        # Table of contents header
        y_toc = y_leg - 30*mm
        self.c.setFillColor(HexColor("#E3F2FD"))
        self.c.rect(MARGIN_L, y_toc - 8*mm, TEXT_W, 10*mm, fill=1, stroke=0)
        self.c.setFillColor(HexColor("#0D47A1"))
        self.c.setFont("JA", 10)
        self.c.drawString(MARGIN_L + 4*mm, y_toc - 3*mm, "投稿スケジュール一覧")

        schedule = [
            (1, "ダウ理論・トレンドの正しい定義", "「今月プラスで終わらせないと」の危険", False),
            (2, "環境認識の具体的な手順", "予想が当たっても利益が出ない3つの理由", False),
            (3, "押し目・戻り目の見つけ方", "FX取引所の選び方", True),
            (4, "本物と偽ブレイクの見分け方", "ルールを破って勝った経験の危険", False),
            (5, "パーフェクトオーダーとは", "FX用語を覚えたのにチャートが読めなかった", False),
            (6, "エリオット波動・第3波だけ狙う理由", "「この通貨ペアが熱い」に乗って失敗した話", False),
            (7, "グランビルの法則", "1回の損失額を固定したら心が楽になった", False),
            (8, "チャートパターン入門", "ルールを作ったのに守れない時に必要なこと", False),
            (9, "経済指標カレンダーの使い方", "スランプの本当の原因", False),
            (10, "ドル円以外の通貨ペアの選び方", "ロットを増やしたら利益が全部消えた話", False),
            (11, "自動売買・コピートレードの落とし穴", "勝てる日と勝てない日の違いを言語化できるか", False),
            (12, "「勝つ」と「稼ぐ」は別物", "FXを始める資金", True),
            (13, "スマホだけでFXを始める注意点", "トレードノートの具体的な書き方", False),
            (14, "FXの税金・確定申告の基本", "初めてFXで利益が出た日を覚えているか", False),
        ]

        row_h = 6.5 * mm
        y_row = y_toc - 8*mm - row_h
        col_widths = [12*mm, 73*mm, 73*mm, 16*mm]
        headers = ["Day", "🌅 朝テーマ", "🌙 夜テーマ", ""]
        self.c.setFont("JA", 7.5)
        self.c.setFillColor(HexColor("#37474F"))
        x = MARGIN_L
        for w, h in zip(col_widths, headers):
            self.c.drawString(x + 1.5*mm, y_row + 1.5*mm, h)
            x += w
        y_row -= row_h

        for day, morning, evening, is_aff in schedule:
            if y_row < MARGIN_B + 5*mm:
                break
            bg = COL_AFFILIATE if is_aff else (HexColor("#F5F5F5") if day % 2 == 0 else white)
            self.c.setFillColor(bg)
            self.c.rect(MARGIN_L, y_row, TEXT_W, row_h, fill=1, stroke=0)
            self.c.setFillColor(COL_TITLE)
            self.c.setFont("JA", 7.5)
            x = MARGIN_L
            for w, txt in zip(col_widths, [f"Day{day}", morning[:22], evening[:22], "🔗" if is_aff else ""]):
                self.c.drawString(x + 1.5*mm, y_row + 1.5*mm, txt)
                x += w
            self.c.setFillColor(COL_HR)
            self.c.line(MARGIN_L, y_row, MARGIN_L + TEXT_W, y_row)
            y_row -= row_h

        self.c.showPage()
        self.page += 1
        self._new_page_bg()
        self.y = H - MARGIN_T

    def draw_week_header(self, week):
        self._check_space(20*mm)
        self.c.setFillColor(HexColor("#1A237E"))
        self.c.rect(MARGIN_L, self.y - 12*mm, TEXT_W, 12*mm, fill=1, stroke=0)
        self.c.setFillColor(white)
        self.c.setFont("JA", 13)
        self.c.drawCentredString(W/2, self.y - 8*mm, f"第{week}週")
        self.y -= 16*mm

    def _wrap_text(self, text, font_size, max_w):
        """Wrap Japanese text to fit max_w."""
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

    def draw_post(self, day, is_morning, title, meta, body, is_affiliate=False):
        # Determine colors
        if is_affiliate:
            bg = COL_AFFILIATE
            hdr_col = COL_AFFILIATE_H
        elif is_morning:
            bg = COL_MORNING
            hdr_col = COL_MORNING_H
        else:
            bg = COL_EVENING
            hdr_col = COL_EVENING_H

        time_label = "🌅 朝8時" if is_morning else "🌙 夜21時"

        # Pre-calculate height needed
        body_lines = self._wrap_text(body, 8.5, TEXT_W - 8*mm)
        n_body = len(body_lines)
        # Find hashtag line index
        hash_idx = None
        for i, l in enumerate(body_lines):
            if l.startswith("#"):
                hash_idx = i
                break

        header_h = 10*mm
        body_h = n_body * 5.2*mm + 6*mm
        total = header_h + body_h + 8*mm

        self._check_space(total)

        box_y = self.y - total
        # Shadow
        self.c.setFillColor(HexColor("#E0E0E0"))
        self.c.roundRect(MARGIN_L + 1*mm, box_y - 1*mm, TEXT_W, total, 3*mm, fill=1, stroke=0)
        # Card bg
        self.c.setFillColor(bg)
        self.c.roundRect(MARGIN_L, box_y, TEXT_W, total, 3*mm, fill=1, stroke=0)

        # Header bar
        self.c.setFillColor(hdr_col)
        self.c.roundRect(MARGIN_L, box_y + total - header_h, TEXT_W, header_h, 3*mm, fill=1, stroke=0)
        self.c.rect(MARGIN_L, box_y + total - header_h, TEXT_W, header_h/2, fill=1, stroke=0)

        # Header text
        self.c.setFillColor(white)
        self.c.setFont("JA", 8)
        self.c.drawString(MARGIN_L + 3*mm, box_y + total - 4.5*mm, f"Day{day}  {time_label}  {meta}")
        if is_affiliate:
            self.c.setFont("JA", 7)
            self.c.setFillColor(HexColor("#A5D6A7"))
            self.c.drawRightString(MARGIN_L + TEXT_W - 3*mm, box_y + total - 4.5*mm, "🔗 アフィリエイト")

        # Title
        self.c.setFillColor(COL_TITLE)
        self.c.setFont("JA", 9)
        title_lines = self._wrap_text(title, 9, TEXT_W - 8*mm)
        ty = box_y + total - header_h - 5*mm
        for tl in title_lines:
            self.c.drawString(MARGIN_L + 4*mm, ty, tl)
            ty -= 5*mm

        # Divider
        self.c.setStrokeColor(hdr_col)
        self.c.setLineWidth(0.5)
        self.c.line(MARGIN_L + 4*mm, ty + 1.5*mm, MARGIN_L + TEXT_W - 4*mm, ty + 1.5*mm)
        ty -= 3*mm

        # Body text
        self.c.setFont("JA", 8.5)
        for i, line in enumerate(body_lines):
            if ty < box_y + 2*mm:
                break
            if line.startswith("#"):
                self.c.setFillColor(COL_HASH)
            elif line.startswith("【") or line.startswith("■"):
                self.c.setFillColor(hdr_col)
            else:
                self.c.setFillColor(COL_TITLE)
            self.c.drawString(MARGIN_L + 4*mm, ty, line)
            ty -= 5.2*mm

        self.y = box_y - 5*mm

    def page_number(self):
        self.c.setFont("JA", 7)
        self.c.setFillColor(COL_META)
        self.c.drawCentredString(W/2, 10*mm, f"- {self.page} -")

    def save(self):
        self.c.save()


def parse_posts(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    posts = []
    # Split by Day markers in the schedule
    # Parse each post block
    pattern = re.compile(
        r"###\s+(Day\d+)\s+(🌅|🌙)[^\n]+\n+(.*?)\n+(?:🟣|🟢|🟠|🔵|🟤)[^\n]+\n+(.*?)\n+---",
        re.DOTALL
    )
    for m in pattern.finditer(content):
        day_str = m.group(1)  # e.g. "Day1"
        sun = m.group(2)       # 🌅 or 🌙
        title_meta = m.group(3).strip()
        body = m.group(4).strip()
        day = int(day_str.replace("Day", ""))
        is_morning = sun == "🌅"
        posts.append((day, is_morning, title_meta, body))
    return posts


def read_posts_manual(filepath):
    """Read the file and extract posts by parsing sections."""
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    posts = []
    # Split on ### Day headers
    sections = re.split(r'\n(?=### Day)', text)
    for sec in sections:
        m = re.match(r'### (Day\d+)\s+(🌅|🌙)\s+(?:朝|夜)【([^】]+)】([^\n]+)', sec)
        if not m:
            continue
        day = int(m.group(1).replace("Day",""))
        is_morning = m.group(2) == "🌅"
        theme_short = m.group(3)
        rest_of_header = m.group(4)

        # Find meta line (カテゴリ line)
        meta_m = re.search(r'(?:🟣|🟢|🟠|🔵|🟤)[^\n]+\|[^\n]+\|([^\n]+)\n', sec)
        meta = meta_m.group(1).strip() if meta_m else ""

        # Find body: everything between first --- divider and final ---
        dividers = [m2.start() for m2 in re.finditer(r'\n---\n', sec)]
        if len(dividers) >= 2:
            body = sec[dividers[0]+5:dividers[1]].strip()
        elif len(dividers) == 1:
            body = sec[dividers[0]+5:].strip()
        else:
            continue

        # Title: first 【…】 line in body
        title_m = re.search(r'【([^】]+)】', body)
        title = f"【{title_m.group(1)}】" if title_m else theme_short

        is_aff = "アフィリエイト" in sec

        posts.append((day, is_morning, title, meta, body, is_aff))
    return posts


if __name__ == "__main__":
    INPUT = "/home/user/cc-company/marketing/content-plan/hajime-x-2week-posts.md"
    OUTPUT = "/home/user/cc-company/marketing/content-plan/hajime-x-2week-posts.pdf"

    posts = read_posts_manual(INPUT)
    print(f"Parsed {len(posts)} posts")

    maker = PDFMaker(OUTPUT)
    maker.draw_cover()

    week = 0
    current_week = 0
    for day, is_morning, title, meta, body, is_aff in sorted(posts, key=lambda x: (x[0], not x[1])):
        wk = (day - 1) // 7 + 1
        if wk != current_week:
            current_week = wk
            maker.draw_week_header(wk)

        maker.draw_post(day, is_morning, title, meta, body, is_aff)

    maker.page_number()
    maker.save()
    print(f"PDF saved: {OUTPUT}")
