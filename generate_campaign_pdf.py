#!/usr/bin/env python3
"""
入金ボーナスキャンペーン訴求 本投稿×リプ欄セット PDF生成スクリプト
Output: marketing/content-plan/hajime-campaign-posts.pdf
"""
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
ML, MR, MT, MB = 16*mm, 16*mm, 18*mm, 18*mm
TW = W - ML - MR

# Color palette
NAVY    = HexColor("#0D1B2A")
NAVY2   = HexColor("#1B2A3B")
GREEN   = HexColor("#27AE60")
GREEN_L = HexColor("#EAFAF1")
BLUE    = HexColor("#2980B9")
BLUE_L  = HexColor("#EBF5FB")
GRAY    = HexColor("#7F8C8D")
DGRAY   = HexColor("#BDC3C7")
PAGE_BG = HexColor("#F4F6F9")
GOLD    = HexColor("#D4AC0D")
GOLD_L  = HexColor("#FDFBE4")
RED_L   = HexColor("#FDEDEC")
RED     = HexColor("#C0392B")


def rr(c, x, y, w, h, r=2*mm, fill=1, stroke=0):
    c.roundRect(x, y, w, h, r, fill=fill, stroke=stroke)


def wrap(c, text, fs, max_w):
    c.setFont("JA", fs)
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        cur = ""
        for ch in para:
            test = cur + ch
            if pdfmetrics.stringWidth(test, "JA", fs) > max_w:
                if cur:
                    lines.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            lines.append(cur)
    return lines


# ─────────────────────────────────────────────────────────
# Post data
# ─────────────────────────────────────────────────────────
PATTERNS = [
    {
        "num": "①",
        "name": "介入後のタイミング訴求型",
        "target": "ターゲット：相場を見ている既存ユーザー　主な目的：入金額アップ",
        "desc": "「今が入金するベストタイミング」という文脈でボーナスに自然につなぐ。\n既存ユーザーの入金額アップに最も刺さるパターン。",
        "post": (
            "為替介入で160円→155円まで動いたとき、\n"
            "一番後悔したのは「証拠金に余裕がなかったこと」。\n\n"
            "大きく動く相場って、資金に余裕がある人が\n"
            "一番おいしく取れるんですよね。\n\n"
            "その後悔があって、今は意識的に\n"
            "口座の資金に余裕を持つようにしています。\n\n"
            "今ちょうど使っている口座でキャンペーンがあって、\n"
            "入金したら結構お得なことに気づいたので\n"
            "↓リプに書いておきます。"
        ),
        "post_hash": "#FX #ドル円",
        "reply": (
            "今Vantageで入金ボーナスキャンペーン中です。\n\n"
            "入金額に応じてボーナスが上乗せされるので、\n"
            "そのまま証拠金として使えます。\n\n"
            "介入みたいに突然動く相場で\n"
            "「もう少し資金があれば…」と思ったことある人には\n"
            "特に今がお得なタイミングだと思います。\n\n"
            "もちろん新規の方も\n"
            "口座開設 → そのまま入金でボーナス受け取れます。\n\n"
            "既に口座持っている方も、新しく始める方も👇\n"
            "▶️ my78p.com/l/u/vtg\n\n"
            "※キャンペーンは5月26日(火)23:59まで"
        ),
    },
    {
        "num": "②",
        "name": "ボーナス＝バッファ教育型",
        "target": "ターゲット：初中級者・FX初心者　主な目的：新規獲得＋入金額アップ 両取り",
        "desc": "「ボーナスが守りになる」という知識提供型。\n保存・RTされやすく、そのままURL訴求につながる。",
        "post": (
            "日銀が6月に利上げするかどうか、\n"
            "今まさにトレーダーが注目している。\n\n"
            "こういう「動くかもしれない」という局面で\n"
            "意外と大事なのが証拠金に余裕を持つこと。\n\n"
            "ポジションを持つ余力があるかどうかで\n"
            "同じ予測をしていても結果が変わる。\n\n"
            "資金の余裕を作る方法はいくつかあるけど、\n"
            "今私が使っている一番コスパの良い方法を\n"
            "↓リプに書きます。"
        ),
        "post_hash": "#FX #FX初心者",
        "reply": (
            "入金ボーナスキャンペーンを使うのが\n"
            "今一番コスパがいいと思っています。\n\n"
            "Vantageでは今、入金額の+10%ボーナスが\n"
            "上乗せされるキャンペーン中。\n\n"
            "たとえば10万円入金したら+1万円ボーナスが付いて\n"
            "実質11万円の証拠金として動かせる計算になります。\n\n"
            "このボーナス分がそのまま損失時のクッションにもなるので、\n"
            "メンタル的にも余裕が出ます。\n\n"
            "まだ口座を持っていない方は\n"
            "開設 → 入金でそのままボーナス受け取れます👇\n"
            "▶️ my78p.com/l/u/vtg\n\n"
            "5月26日(火)23:59まで。お早めに。"
        ),
    },
    {
        "num": "③",
        "name": "比較・損得提示型",
        "target": "ターゲット：入金を迷っている人　主な目的：入金額アップ（決断を後押し）",
        "desc": "「やらないと損」の心理が働く。\n入金を迷っている人の背中を最も強く押せるパターン。",
        "post": (
            "FXで地味に損してることに\n"
            "気づいていない人が多いと思う話。\n\n"
            "同じ10万円を口座に入れても、\n"
            "キャンペーン期間中に入れるかどうかで\n"
            "実際に動かせる証拠金が変わる。\n\n"
            "ボーナスの有無で戦える資金量が違うのに、\n"
            "それを知らずに普通のタイミングで入金するのは\n"
            "純粋にもったいない。\n\n"
            "今私が使っている口座で\n"
            "ちょうど入金ボーナスキャンペーンが来てるので\n"
            "↓リプに詳細書いておきます。"
        ),
        "post_hash": "#FX #副業",
        "reply": (
            "Vantageで入金ボーナスキャンペーン中です。\n\n"
            "入金額の+10%ボーナスが上乗せされる仕組みで、\n"
            "キャンペーン期間外に入金するより明らかにお得。\n\n"
            "私は毎回こういうタイミングに合わせて\n"
            "入金するようにしています。\n\n"
            "新規で口座を作る方も\n"
            "今始めると開設 + 入金ボーナスの両方が取れます。\n\n"
            "損したくない人はとりあえず確認だけでも👇\n"
            "▶️ my78p.com/l/u/vtg\n\n"
            "※5月26日(火)23:59まで。逃さないように"
        ),
    },
    {
        "num": "④",
        "name": "相場の本音トーク型",
        "target": "ターゲット：機会損失を感じているトレーダー　主な目的：入金額アップ",
        "desc": "「正直に言うと」系は信頼感が高まりやすい。\n広告に見えにくく、自然にURLへ誘導できるパターン。",
        "post": (
            "正直に言います。\n\n"
            "ドル円が160円を超えて\n"
            "介入→急落を繰り返している今の相場、\n"
            "資金力がない状態だと見ているだけになりがちです。\n\n"
            "大きく動く時間帯に\n"
            "「入れるポジションがない」のは\n"
            "機会損失以外の何でもない。\n\n"
            "この問題を解決する方法として\n"
            "今私が実際にやっていることを\n"
            "↓リプに書いておきます。\n\n"
            "正直これはもっと早く知りたかった。"
        ),
        "post_hash": "#FX #ドル円",
        "reply": (
            "答えを書くと、\n"
            "入金ボーナスキャンペーンを活用することです。\n\n"
            "Vantageが今、入金額の+10%ボーナスキャンペーン中。\n\n"
            "つまり入金額より10%多い証拠金で\n"
            "トレードをスタートできる。\n\n"
            "自分のお金は同じでも\n"
            "動かせる資金が増えるので\n"
            "ポジションの選択肢が広がります。\n\n"
            "口座をまだ持っていない方も今が開設のタイミング。\n"
            "+10%ボーナスで\n"
            "最初から余裕のある状態で始められます👇\n"
            "▶️ my78p.com/l/u/vtg\n\n"
            "※5月26日(火)23:59まで"
        ),
    },
    {
        "num": "⑤",
        "name": "体験談＋数字型",
        "target": "ターゲット：具体的な情報が欲しい人　主な目的：新規獲得寄り",
        "desc": "具体的な数字を入れることで信頼性が跳ね上がる。\n最もクリック・登録につながりやすいパターン。",
        "post": (
            "今月、口座への入金タイミングを変えただけで\n"
            "実際に動かせる証拠金が増えた話。\n\n"
            "お金を増やしたわけじゃなくて、\n"
            "キャンペーンのタイミングに合わせて\n"
            "入金しただけです。\n\n"
            "この差、地味にでかい。\n\n"
            "相場のボラが高い今、\n"
            "証拠金に余裕があるかどうかって\n"
            "結構トレード結果に響いてくると思ってる。\n\n"
            "詳しくは↓リプに。"
        ),
        "post_hash": "#FX #FX初心者",
        "reply": (
            "Vantageの+10%入金ボーナスキャンペーンを使いました。\n\n"
            "10万円入金したら+1万円のボーナスが加算されて、\n"
            "実際に動かせる証拠金が11万円になった感じです。\n\n"
            "ボーナス分はそのままトレードに使えるので\n"
            "実質的に資金効率が上がっています。\n\n"
            "「同じ入金額でも証拠金が多い状態で始められる」\n"
            "これ、特に今の相場では差が出ると思います。\n\n"
            "まだ口座を持っていない方は\n"
            "新規開設 + 入金で+10%ボーナスが取れます👇\n"
            "▶️ my78p.com/l/u/vtg\n\n"
            "5月26日(火)23:59まで。お早めに。"
        ),
    },
]

GUIDE_ROWS = [
    ("①介入タイミング型",  "相場を見ている既存ユーザー",   "入金額アップ寄り"),
    ("②バッファ教育型",    "初中級者・FX初心者",           "新規＋既存 両取り"),
    ("③比較・損得型",      "入金を迷っている人",           "入金額アップ寄り"),
    ("④本音トーク型",      "機会損失を感じている人",       "入金額アップ寄り"),
    ("⑤体験談数字型",      "具体的な情報が欲しい人",       "新規獲得寄り"),
]

CTA_TIPS = [
    ("期間が短い時",       "「〇日まで」「今月末まで」を明記する"),
    ("上限がある時",       "「先着〇名」「受取上限あり」を添える"),
    ("新規にも訴求",       "「開設 + 入金でダブルボーナス」と書く"),
    ("入金額を増やしたい", "「入金額が多いほどボーナスも増える」と伝える"),
]


# ─────────────────────────────────────────────────────────
# PDF class
# ─────────────────────────────────────────────────────────
class PDF:
    def __init__(self, path):
        self.c    = canvas.Canvas(str(path), pagesize=A4)
        self.c.setTitle("Vantage +10%入金ボーナスキャンペーン 投稿セット")
        self.page = 0
        self.y    = H - MT
        self._bg()

    def _bg(self):
        self.page += 1
        self.c.setFillColor(PAGE_BG)
        self.c.rect(0, 0, W, H, fill=1, stroke=0)

    def _new_page(self):
        self._pnum()
        self.c.showPage()
        self._bg()
        self.y = H - MT

    def _pnum(self):
        self.c.setFont("JA", 7)
        self.c.setFillColor(GRAY)
        self.c.drawCentredString(W / 2, 9*mm, f"— {self.page} —")

    def _ensure(self, needed):
        if self.y - needed < MB + 4*mm:
            self._new_page()

    def _w(self, text, fs, mw=None):
        return wrap(self.c, text, fs, mw or TW - 8*mm)

    # ── Section header ──────────────────────────────────────
    def _section_hdr(self, num, name, target):
        h = 16*mm
        self._ensure(h + 5*mm)
        c = self.c
        ct = self.y

        c.setFillColor(NAVY)
        rr(c, ML, ct - h, TW, h, 3*mm)
        # green left bar
        c.setFillColor(GREEN)
        c.rect(ML, ct - h, 4*mm, h, fill=1, stroke=0)
        rr(c, ML, ct - h, 4*mm, h, 2*mm)

        c.setFillColor(GREEN)
        c.setFont("JA", 9)
        c.drawString(ML + 7*mm, ct - 5.5*mm, f"パターン {num}")
        c.setFillColor(white)
        c.setFont("JA", 11)
        c.drawString(ML + 7*mm, ct - 11.5*mm, name)

        # target chip (right side)
        c.setFillColor(HexColor("#1E3A2F"))
        chip_w = pdfmetrics.stringWidth(target, "JA", 6.5) + 8*mm
        chip_x = ML + TW - chip_w - 2*mm
        rr(c, chip_x, ct - 13*mm, chip_w, 6.5*mm, 2*mm)
        c.setFillColor(HexColor("#A9DFBF"))
        c.setFont("JA", 6.5)
        c.drawString(chip_x + 4*mm, ct - 9.5*mm, target)

        self.y -= h + 4*mm

    # ── Description strip ───────────────────────────────────
    def _desc(self, text):
        lines = self._w(text, 8, TW - 6*mm)
        h = len(lines) * 5*mm + 5*mm
        self._ensure(h + 3*mm)
        c = self.c
        ct = self.y

        c.setFillColor(GOLD_L)
        rr(c, ML, ct - h, TW, h, 2*mm)
        c.setFillColor(GOLD)
        c.rect(ML, ct - h, 3*mm, h, fill=1, stroke=0)
        rr(c, ML, ct - h, 3*mm, h, 2*mm)

        ty = ct - 3.5*mm
        c.setFillColor(NAVY)
        c.setFont("JA", 8)
        for ln in lines:
            c.drawString(ML + 6*mm, ty - 4*mm, ln)
            ty -= 5*mm
        self.y -= h + 4*mm

    # ── Post card (本投稿 or リプ欄) ─────────────────────────
    def _post_card(self, label, body_text, hashtag, accent_col, bg_col, label_text_col=None):
        inner_w = TW - 10*mm
        FS_LABEL = 8
        FS_BODY  = 8.5
        FS_HASH  = 8
        LINE_L   = 5.5*mm
        LINE_B   = 5*mm
        LINE_H   = 5.5*mm
        PAD      = 4*mm

        label_lines = self._w(label, FS_LABEL, inner_w)
        body_lines  = self._w(body_text, FS_BODY, inner_w)
        hash_lines  = self._w(hashtag, FS_HASH, inner_w) if hashtag else []

        label_h = len(label_lines) * LINE_L + PAD
        body_h  = len(body_lines) * LINE_B + PAD
        hash_h  = (len(hash_lines) * LINE_H + PAD + 2*mm) if hash_lines else 0
        total   = label_h + body_h + hash_h + PAD

        self._ensure(total + 4*mm)
        c  = self.c
        ct = self.y

        # card bg
        c.setFillColor(bg_col)
        rr(c, ML, ct - total, TW, total, 3*mm)
        # accent bar
        c.setFillColor(accent_col)
        c.rect(ML, ct - total, 4*mm, total, fill=1, stroke=0)
        rr(c, ML, ct - total, 4*mm, total, 2*mm)

        ty = ct - PAD

        # label
        lc = label_text_col or accent_col
        c.setFillColor(accent_col)
        rr(c, ML + 6*mm, ty - LINE_L + 1*mm, pdfmetrics.stringWidth(label_lines[0], "JA", FS_LABEL) + 6*mm, LINE_L, 1.5*mm)
        c.setFillColor(white)
        c.setFont("JA", FS_LABEL)
        c.drawString(ML + 9*mm, ty - LINE_L + 2.5*mm, label_lines[0])
        ty -= label_h

        # body
        c.setFillColor(NAVY)
        c.setFont("JA", FS_BODY)
        for ln in body_lines:
            c.drawString(ML + 8*mm, ty, ln)
            ty -= LINE_B
        ty -= 1*mm

        # hashtag box
        if hash_lines:
            hbox_h = len(hash_lines) * LINE_H + 2.5*mm
            c.setFillColor(HexColor("#DFF0FE"))
            rr(c, ML + 7*mm, ty - hbox_h, TW - 11*mm, hbox_h, 1.5*mm)
            c.setFillColor(BLUE)
            c.setFont("JA", FS_HASH)
            hy = ty - 2*mm
            for ln in hash_lines:
                c.drawString(ML + 10*mm, hy - LINE_H + 2*mm, ln)
                hy -= LINE_H

        self.y -= total + 5*mm

    # ════════════════════════════════════════════════════════
    # Cover page
    # ════════════════════════════════════════════════════════
    def cover(self):
        c = self.c

        # Header band
        c.setFillColor(NAVY)
        c.rect(0, H - 82*mm, W, 82*mm, fill=1, stroke=0)
        c.setFillColor(GREEN)
        c.rect(0, H - 82*mm, W, 3*mm, fill=1, stroke=0)

        c.setFillColor(HexColor("#A9DFBF"))
        c.setFont("JA", 9)
        c.drawCentredString(W/2, H - 18*mm, "@HajimeP30432  FXアフィリエイト施策")
        c.setFillColor(white)
        c.setFont("JA", 17)
        c.drawCentredString(W/2, H - 32*mm, "入金ボーナスキャンペーン訴求")
        c.setFont("JA", 13)
        c.drawCentredString(W/2, H - 44*mm, "本投稿 × リプ欄 セット集")
        c.setFillColor(HexColor("#A9DFBF"))
        c.setFont("JA", 8)
        c.drawCentredString(W/2, H - 56*mm,
            "Vantage +10%入金ボーナス  |  5月26日(火)23:59まで  |  2026年5月トレンド使用")

        # KPI boxes
        kpis = [("5パターン", "訴求セット数"), ("入金額アップ", "主な目的①"), ("新規獲得", "主な目的②")]
        bw = (TW - 6*mm) / 3
        by, bh = H - 106*mm, 20*mm
        for i, (num, lbl) in enumerate(kpis):
            bx = ML + i * (bw + 3*mm)
            c.setFillColor(white); rr(c, bx, by, bw, bh, 3*mm)
            c.setFillColor(NAVY);  c.setFont("JA", 11)
            c.drawCentredString(bx + bw/2, by + 12*mm, num)
            c.setFillColor(GRAY);  c.setFont("JA", 6.5)
            c.drawCentredString(bx + bw/2, by + 5*mm, lbl)

        # Pattern index
        self.y = H - 118*mm
        c.setFillColor(HexColor("#D5F5E3"))
        c.rect(ML, self.y - 7*mm, TW, 8*mm, fill=1, stroke=0)
        c.setFillColor(HexColor("#1E8449")); c.setFont("JA", 9)
        c.drawString(ML + 4*mm, self.y - 1.5*mm, "パターン一覧")
        self.y -= 9*mm

        entries = [
            ("パターン①", "介入後のタイミング訴求型", "既存ユーザーの入金額アップ"),
            ("パターン②", "ボーナス＝バッファ教育型", "新規獲得＋既存 両取り"),
            ("パターン③", "比較・損得提示型",         "入金決断を後押し"),
            ("パターン④", "相場の本音トーク型",       "機会損失を感じている層"),
            ("パターン⑤", "体験談＋数字型",           "新規獲得寄り"),
        ]
        for num, name, note in entries:
            c.setFillColor(white)
            rr(c, ML, self.y - 9*mm, TW, 9*mm, 2*mm)
            c.setFillColor(GREEN); c.setFont("JA", 7.5)
            c.drawString(ML + 4*mm, self.y - 6*mm, num)
            c.setFillColor(NAVY); c.setFont("JA", 8)
            c.drawString(ML + 22*mm, self.y - 6*mm, name)
            c.setFillColor(GRAY); c.setFont("JA", 7)
            c.drawString(ML + 86*mm, self.y - 6*mm, f"→ {note}")
            self.y -= 10*mm

        # Design legend
        self.y -= 4*mm
        c.setFillColor(white)
        rr(c, ML, self.y - 22*mm, TW, 22*mm, 2*mm)
        c.setFillColor(NAVY); c.setFont("JA", 8.5)
        c.drawString(ML + 5*mm, self.y - 5*mm, "カード凡例")
        # green bar sample
        c.setFillColor(GREEN_L); rr(c, ML + 5*mm, self.y - 15*mm, 48*mm, 8*mm, 1.5*mm)
        c.setFillColor(GREEN);   c.rect(ML + 5*mm, self.y - 15*mm, 3*mm, 8*mm, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("JA", 7.5)
        c.drawString(ML + 11*mm, self.y - 11.5*mm, "本投稿カード")
        # blue bar sample
        c.setFillColor(BLUE_L); rr(c, ML + 62*mm, self.y - 15*mm, 48*mm, 8*mm, 1.5*mm)
        c.setFillColor(BLUE);   c.rect(ML + 62*mm, self.y - 15*mm, 3*mm, 8*mm, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("JA", 7.5)
        c.drawString(ML + 68*mm, self.y - 11.5*mm, "リプ欄カード")
        self.y -= 22*mm

        self._pnum()
        self.c.showPage()
        self._bg()
        self.y = H - MT

    # ════════════════════════════════════════════════════════
    # Pattern pages
    # ════════════════════════════════════════════════════════
    def pattern_page(self, pat):
        self._section_hdr(pat["num"], pat["name"], pat["target"][:20])
        self._desc(pat["desc"])
        self._post_card("本投稿", pat["post"], pat["post_hash"], GREEN, GREEN_L)
        self._post_card("リプ欄", pat["reply"], "", BLUE, BLUE_L)

    # ════════════════════════════════════════════════════════
    # Guide page
    # ════════════════════════════════════════════════════════
    def guide_page(self):
        c = self.c

        # Section header
        h = 12*mm
        self._ensure(h + 4*mm)
        ct = self.y
        c.setFillColor(NAVY)
        rr(c, ML, ct - h, TW, h, 3*mm)
        c.setFillColor(GREEN)
        c.rect(ML, ct - h, 4*mm, h, fill=1, stroke=0)
        rr(c, ML, ct - h, 4*mm, h, 2*mm)
        c.setFillColor(white); c.setFont("JA", 11)
        c.drawString(ML + 8*mm, ct - 7.5*mm, "使い分けガイド")
        self.y -= h + 5*mm

        # Table header
        cols = [48*mm, 56*mm, 52*mm]
        headers = ["パターン", "刺さる対象", "主な目的"]
        row_h = 8*mm
        self._ensure(row_h * (len(GUIDE_ROWS) + 2) + 10*mm)
        ty = self.y

        c.setFillColor(NAVY2)
        c.rect(ML, ty - row_h, TW, row_h, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("JA", 8)
        x = ML + 3*mm
        for i, (hdr, cw) in enumerate(zip(headers, cols)):
            c.drawString(x, ty - 5.5*mm, hdr)
            x += cw
        ty -= row_h

        for ri, (p, tgt, purpose) in enumerate(GUIDE_ROWS):
            bg = HexColor("#FFFFFF") if ri % 2 == 0 else HexColor("#F0F9F4")
            c.setFillColor(bg)
            c.rect(ML, ty - row_h, TW, row_h, fill=1, stroke=0)
            c.setFillColor(GREEN); c.setFont("JA", 7.5)
            c.drawString(ML + 3*mm, ty - 5.5*mm, p)
            c.setFillColor(NAVY); c.setFont("JA", 7.5)
            c.drawString(ML + cols[0] + 3*mm, ty - 5.5*mm, tgt)
            c.setFillColor(GRAY); c.setFont("JA", 7.5)
            c.drawString(ML + cols[0] + cols[1] + 3*mm, ty - 5.5*mm, purpose)
            ty -= row_h

        self.y = ty - 6*mm

        # CTA tips
        self._ensure(12*mm)
        c.setFillColor(HexColor("#D5F5E3"))
        c.rect(ML, self.y - 7*mm, TW, 7*mm, fill=1, stroke=0)
        c.setFillColor(HexColor("#1E8449")); c.setFont("JA", 8.5)
        c.drawString(ML + 4*mm, self.y - 4.5*mm, "リプ欄に追加すると効果が上がる一言")
        self.y -= 9*mm

        for sit, tip in CTA_TIPS:
            tip_h = 9*mm
            self._ensure(tip_h + 1*mm)
            ct2 = self.y
            c.setFillColor(white)
            rr(c, ML, ct2 - tip_h, TW, tip_h, 2*mm)
            c.setFillColor(GREEN); c.setFont("JA", 7.5)
            c.drawString(ML + 4*mm, ct2 - 5.5*mm, sit)
            c.setFillColor(NAVY); c.setFont("JA", 7.5)
            tip_lines = self._w(tip, 7.5, TW - 52*mm)
            for i, ln in enumerate(tip_lines):
                c.drawString(ML + 48*mm, ct2 - 5.5*mm - i * 5*mm, ln)
            self.y -= tip_h + 2*mm

        # Notes
        self.y -= 4*mm
        self._ensure(22*mm)
        c.setFillColor(RED_L)
        rr(c, ML, self.y - 20*mm, TW, 20*mm, 2*mm)
        c.setFillColor(RED)
        c.rect(ML, self.y - 20*mm, 3*mm, 20*mm, fill=1, stroke=0)
        rr(c, ML, self.y - 20*mm, 3*mm, 20*mm, 2*mm)
        c.setFillColor(RED); c.setFont("JA", 8)
        c.drawString(ML + 6*mm, self.y - 5.5*mm, "キャンペーン詳細：Vantage +10%入金ボーナス  |  5月26日(火)23:59まで")
        c.setFillColor(NAVY); c.setFont("JA", 7.5)
        notes = [
            "・URL: my78p.com/l/u/vtg（新規開設 + 入金でそのままボーナス適用）",
            "・10万円入金 → +1万円 / 5万円入金 → +5,000円（入金額の10%）",
        ]
        ny = self.y - 11*mm
        for n in notes:
            c.drawString(ML + 6*mm, ny, n)
            ny -= 5*mm
        self.y -= 22*mm

    # ════════════════════════════════════════════════════════
    # Save
    # ════════════════════════════════════════════════════════
    def save(self):
        self._pnum()
        self.c.save()


# ─────────────────────────────────────────────────────────
def main():
    out = Path("marketing/content-plan/hajime-campaign-posts.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    pdf = PDF(out)
    pdf.cover()

    for pat in PATTERNS:
        pdf.pattern_page(pat)

    pdf.guide_page()
    pdf.save()

    size_kb = out.stat().st_size // 1024
    print(f"PDF saved: {out}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
