#!/usr/bin/env python3
"""
入金ボーナスキャンペーン訴求 Vol.2  本投稿×リプ欄セット PDF生成スクリプト
Output: marketing/content-plan/hajime-campaign2-posts.pdf
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
# Reply base text (user-provided, shared across all patterns with first-line variation)
# ─────────────────────────────────────────────────────────
def _reply(first_line: str) -> str:
    return (
        f"{first_line}\n\n"
        "10万円入金したら+1万円のボーナスが加算されて、実際に動かせる証拠金が11万円になった感じです\n\n"
        "ボーナス分はそのままトレードに使えるので実質的に資金効率が上がっています\n\n"
        "「同じ入金額でも証拠金が多い状態で始められる」\n\n"
        "これ、特に今の相場では差が出ると思います\n\n"
        "まだ口座を持っていない方は新規開設 + 入金で+10%ボーナスが取れます\n"
        "▶my78p.com/l/u/vtg\n\n"
        "6月9日(火)23:59まで。お早めに"
    )


# ─────────────────────────────────────────────────────────
# Post data — 10 patterns
# ─────────────────────────────────────────────────────────
PATTERNS = [
    {
        "num": "①",
        "name": "BTC急落×証拠金余裕型",
        "target": "ターゲット：FX×暗号資産層　主な目的：入金額アップ",
        "desc": "BTCが$69k→$62kに急落した局面を切り口に、証拠金不足による機会損失を語る。\n暗号資産とFXを両方見ている層に刺さるパターン。",
        "post": (
            "ビットコインが$69,000から$62,000まで\n"
            "たった数日で約-10%落ちた。\n\n"
            "こういう急落のとき、FXで動けるかどうかは\n"
            "証拠金に余裕があるかどうかで決まる。\n\n"
            "私はあの局面で\n"
            "「ポジションを追加したいのに証拠金が足りない」\n"
            "という状態になった。\n\n"
            "同じ分析をしていても、\n"
            "資金に余裕がある人とない人では\n"
            "取れるポジションの量がまるで変わる。\n\n"
            "暴落相場で動けないのは予測の問題じゃなく、\n"
            "資金設計の問題だったと気づいた。\n\n"
            "↓リプに今実際に使っている資金効率の上げ方を書きます"
        ),
        "post_hash": "#FX #ビットコイン",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
    {
        "num": "②",
        "name": "半導体株暴落×機会型",
        "target": "ターゲット：株もウォッチする層　主な目的：新規獲得＋入金額アップ",
        "desc": "6/4の半導体株急落でFXにチャンスが生まれた事実を伝える。\n株とFXを両方見ている層に「FXなら動ける」という意識を植え付けるパターン。",
        "post": (
            "6月4日、半導体株が軒並み急落した日のこと。\n\n"
            "エヌビディア・TSMC・ASMLが\n"
            "一斉に売られた局面。\n\n"
            "面白いのはここで\n"
            "「株が売られたとき、FXにチャンスが来た」こと。\n\n"
            "リスクオフの動きでドル円に\n"
            "明確な方向性が出た場面があった。\n\n"
            "この「株安がFXに連動するタイミング」で\n"
            "ポジションを取れるかどうかは\n"
            "口座の証拠金に余裕があるかどうかで変わってくる。\n\n"
            "↓リプに今の相場で特に有効だと思う方法を書いておきます"
        ),
        "post_hash": "#FX #半導体株",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使っています(人によっては+20％+30％になるのでかなりデカい)"),
    },
    {
        "num": "③",
        "name": "ゴールド最高値×資金力型",
        "target": "ターゲット：マルチ資産層　主な目的：入金額アップ（資金力の差を意識させる）",
        "desc": "金$4,500最高値という事実から「一方向に強く動く相場ほど資金力が勝負を決める」を伝える。\nマルチアセット層の証拠金意識を高めるパターン。",
        "post": (
            "ゴールドが$4,500を超えて史上最高値を更新した。\n\n"
            "2025年初から+25%、\n"
            "株でも暗号資産でもなく、\n"
            "金が最も上がっている相場。\n\n"
            "こういう「一方向に強く動く相場」ほど\n"
            "証拠金に余裕がないと乗れない。\n\n"
            "「チャートは読めていた\n"
            "方向感も合っていた\n"
            "でもポジションが小さすぎて大した利益にならなかった」\n\n"
            "これ、実は証拠金の問題です。\n\n"
            "予測が正しくても資金が少なければ\n"
            "結果は変わらない。\n\n"
            "↓リプに今一番コスパよく証拠金を増やせる方法を書きます"
        ),
        "post_hash": "#FX #ゴールド",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
    {
        "num": "④",
        "name": "相場荒れリスト×バッファ教育型",
        "target": "ターゲット：初中級者全般　主な目的：新規獲得＋既存の入金額アップ 両取り",
        "desc": "今週の相場が荒れた5つの理由をリスト化してから証拠金余裕の重要性に誘導する。\n保存・RTされやすく、初中級者に刺さるパターン。",
        "post": (
            "今週相場が大きく動いた理由を整理すると：\n\n"
            "■ BTC が$62,000台まで急落（-10%）\n"
            "■ S&P500 が-2.6%の急落\n"
            "■ 半導体株が軒並み大幅安\n"
            "■ ゴールドが史上最高値を更新\n"
            "■ 米10%関税が相場の重石に\n\n"
            "これだけのイベントが重なる相場で\n"
            "「証拠金に余裕がない」状態だと\n"
            "動けるチャンスが大幅に限られる。\n\n"
            "ボラが高い相場こそ\n"
            "証拠金バッファが決め手になる。\n\n"
            "↓リプに今私が使っている証拠金を増やす方法を書きます"
        ),
        "post_hash": "#FX #相場分析",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
    {
        "num": "⑤",
        "name": "関税ショック×機会損失型",
        "target": "ターゲット：機会損失を感じている層　主な目的：入金額アップ（感情に訴える）",
        "desc": "米10%関税で相場が動いた日に証拠金がなくて動けなかった経験を語る。\n「だけ」「だけで」の悔しさに共感させるパターン。",
        "post": (
            "米国の10%関税が相場を動かしたとき、\n"
            "ドル円に明確な方向性が出た。\n\n"
            "あの動きを見ながら\n"
            "「証拠金が足りなくてポジションを取れなかった」\n"
            "という経験をした人は多いと思う。\n\n"
            "機会損失って、実際に損したわけじゃないから\n"
            "見えにくい。\n\n"
            "でも「あのとき動けていたら」という後悔は\n"
            "じわじわきつい。\n\n"
            "予測はできていた\n"
            "チャートも読めていた\n"
            "ただ証拠金が足りなかっただけ\n\n"
            "この「だけ」が一番もったいない。\n\n"
            "↓リプに証拠金余裕を作るために今やっていることを書きます"
        ),
        "post_hash": "#FX #ドル円",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
    {
        "num": "⑥",
        "name": "6月やること3選型",
        "target": "ターゲット：実行力の高い層　主な目的：期限意識を高めて今週中に動かせる",
        "desc": "「6月中にやること3選」形式で、自然にキャンペーンを2番目に配置する。\n期限（6月9日）が近いことで行動を促すパターン。",
        "post": (
            "FXトレーダーが6月中にやっておくべきこと3つ\n\n"
            "■ 今週の暴落局面を振り返り\n"
            "　どのポジションが取れたか確認する\n\n"
            "■ 証拠金のキャンペーンを使って\n"
            "　来月の資金効率を上げておく\n\n"
            "■ S&P500とドル円の連動を意識した\n"
            "　トレード記録をつけ始める\n\n"
            "この3つのうち、即効性があるのは②です。\n\n"
            "キャンペーン期限が6月9日（火）なので、\n"
            "今週中に動かないと間に合わない。\n\n"
            "来週も今週と同じくらい動く相場なら、\n"
            "証拠金に余裕がある状態で向かえるかどうかは\n"
            "今週の行動次第。\n\n"
            "↓リプに具体的なキャンペーン内容を書きます"
        ),
        "post_hash": "#FX #FX初心者",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
    {
        "num": "⑦",
        "name": "S&P500急落×ドル円連動型",
        "target": "ターゲット：株FX相関を意識する層　主な目的：入金額アップ",
        "desc": "S&P500が-2.6%下げた日のドル円の動きと、入れなかった悔しさを語る。\n株とFXの相関を意識する中上級者に刺さるパターン。",
        "post": (
            "S&P500が-2.6%下落した日のドル円を見ていた。\n\n"
            "米国株が売られるとリスクオフで\n"
            "ドル売り・円買いの動きが出やすい。\n\n"
            "あの日、ドル円は下方向に\n"
            "明確なモメンタムがあった。\n\n"
            "でも入れなかった。\n\n"
            "理由は単純で、\n"
            "既存ポジションの証拠金がギリギリで\n"
            "新規注文を入れる余力がなかった。\n\n"
            "「分析は合っていた\n"
            "動けなかったのは資金の問題」\n\n"
            "これが一番悔しいパターン。\n\n"
            "↓リプにこの問題を解決するために今やっていることを書きます"
        ),
        "post_hash": "#FX #S&P500",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
    {
        "num": "⑧",
        "name": "「始めるなら今週中」型",
        "target": "ターゲット：FX未経験・始めたばかり層　主な目的：新規獲得（期限訴求）",
        "desc": "FXをこれから始める人に「始めるタイミングで証拠金が変わる」を伝える。\n期限（6/9）の近さで緊急性を演出するパターン。",
        "post": (
            "これからFXを始めようとしている人に\n"
            "正直に伝えたいことがある。\n\n"
            "「いつ始めても同じ」は間違いで、\n"
            "始めるタイミングで実際に動かせる証拠金が\n"
            "変わることがある。\n\n"
            "6月9日（火）23:59まで\n"
            "Vantageで入金ボーナスキャンペーンをやっている。\n\n"
            "今週中に口座を開設して入金すれば、\n"
            "最初から証拠金に余裕がある状態でスタートできる。\n\n"
            "今の相場（BTC急落・株安・ゴールド最高値）は\n"
            "初心者が動きを学ぶ絶好の機会でもある。\n\n"
            "同じスタートなら、キャンペーンを使った方がいい。\n\n"
            "↓リプにキャンペーン詳細を書いておきます"
        ),
        "post_hash": "#FX #FX初心者",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
    {
        "num": "⑨",
        "name": "証拠金3択教育型",
        "target": "ターゲット：資金効率を上げたい層　主な目的：入金額アップ（教育型）",
        "desc": "証拠金を増やす3つの方法を提示→③がコスパ最高という構成で自然にボーナスに誘導。\n保存率が高く、知識系として広まりやすいパターン。",
        "post": (
            "FXの証拠金を増やす方法は大きく3つある\n\n"
            "■ 追加入金（自己資金を増やす）\n"
            "■ 利益を出して口座残高を増やす\n"
            "■ キャンペーンのボーナスを活用する\n\n"
            "①は当然だし、②は結果論。\n\n"
            "今一番コスパがいいのは③です。\n\n"
            "自分のお金を増やすわけじゃなく、\n"
            "入金タイミングを合わせるだけで\n"
            "口座の証拠金が10%増える。\n\n"
            "今の相場みたいにボラが高い時期こそ、\n"
            "この10%の差が実際のトレード結果に響いてくる。\n\n"
            "↓リプに今使えるキャンペーン詳細を書きます"
        ),
        "post_hash": "#FX #資金管理",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
    {
        "num": "⑩",
        "name": "本音トーク×今週の後悔型",
        "target": "ターゲット：機会損失を感じているトレーダー　主な目的：入金額アップ（共感誘導）",
        "desc": "「今週取れなかったポジションがある」という正直な話から入るパターン。\n広告に見えず、信頼感から自然にURLへ誘導できる最も共感型のセット。",
        "post": (
            "正直に言うと、\n"
            "今週の相場で取れなかったポジションがある。\n\n"
            "BTCが$62,000台まで落ちた局面\n"
            "半導体株が一斉に売られた日\n"
            "S&P500が-2.6%下げた場面\n\n"
            "全部「方向感はあった」のに、\n"
            "証拠金不足で動けなかった。\n\n"
            "後悔してもどうにもならないけど、\n"
            "「来週は同じ悔しさをしたくない」\n"
            "と思ったのは本音。\n\n"
            "準備できることはしておく、という話を\n"
            "↓リプに書きます"
        ),
        "post_hash": "#FX #トレード記録",
        "reply": _reply("Vantageの+10%入金ボーナスキャンペーンを使いました(人によっては+20％+30％で超デカい)"),
    },
]

GUIDE_ROWS = [
    ("①BTC急落×証拠金型",    "FX×暗号資産層",           "入金額アップ寄り"),
    ("②半導体株暴落×機会型",  "株もウォッチする層",       "新規＋既存 両取り"),
    ("③ゴールド最高値×資金型","マルチ資産層",             "入金額アップ寄り"),
    ("④相場荒れリスト型",      "初中級者全般",             "新規＋既存 両取り"),
    ("⑤関税ショック×損失型",  "機会損失を感じている層",   "入金額アップ寄り"),
    ("⑥6月やること3選型",     "実行力の高い層",           "期限訴求・今週行動"),
    ("⑦S&P500×ドル円型",     "株FX相関を意識する層",     "入金額アップ寄り"),
    ("⑧始めるなら今週中型",   "FX未経験・初心者層",       "新規獲得寄り"),
    ("⑨証拠金3択教育型",      "資金効率を上げたい層",     "入金額アップ寄り"),
    ("⑩本音トーク×後悔型",   "機会損失を感じている層",   "入金額アップ寄り"),
]

CTA_TIPS = [
    ("期間が短い時",       "「6月9日まで」を明記する（すでにリプ欄に入っています）"),
    ("+20%/+30%の場合",   "「人によっては+20%+30%」を強調して期待値を上げる"),
    ("新規にも訴求",       "「開設 + 入金でそのままボーナス適用」と書く"),
    ("入金額を増やしたい", "「入金額が多いほどボーナスも増える」と伝える"),
]


# ─────────────────────────────────────────────────────────
# PDF class
# ─────────────────────────────────────────────────────────
class PDF:
    def __init__(self, path):
        self.c    = canvas.Canvas(str(path), pagesize=A4)
        self.c.setTitle("Vantage +10%入金ボーナスキャンペーン Vol.2 投稿セット")
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
    def _post_card(self, label, body_text, hashtag, accent_col, bg_col):
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

        # label badge
        c.setFillColor(accent_col)
        rr(c, ML + 6*mm, ty - LINE_L + 1*mm,
           pdfmetrics.stringWidth(label_lines[0], "JA", FS_LABEL) + 6*mm, LINE_L, 1.5*mm)
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
        c.drawCentredString(W/2, H - 18*mm, "@HajimeP30432  FXアフィリエイト施策  Vol.2")
        c.setFillColor(white)
        c.setFont("JA", 17)
        c.drawCentredString(W/2, H - 32*mm, "入金ボーナスキャンペーン訴求")
        c.setFont("JA", 13)
        c.drawCentredString(W/2, H - 44*mm, "本投稿 × リプ欄 セット集")
        c.setFillColor(HexColor("#A9DFBF"))
        c.setFont("JA", 8)
        c.drawCentredString(W/2, H - 56*mm,
            "Vantage +10%入金ボーナス  |  6月9日(火)23:59まで  |  2026年6月トレンド使用")

        # KPI boxes
        kpis = [("10パターン", "訴求セット数"), ("入金額アップ", "主な目的①"), ("新規獲得", "主な目的②")]
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
        c.drawString(ML + 4*mm, self.y - 1.5*mm, "パターン一覧（全10本）")
        self.y -= 9*mm

        entries = [
            ("パターン①", "BTC急落×証拠金余裕型",       "FX×暗号資産層"),
            ("パターン②", "半導体株暴落×機会型",         "株もウォッチする層"),
            ("パターン③", "ゴールド最高値×資金力型",     "マルチ資産層"),
            ("パターン④", "相場荒れリスト×バッファ型",   "初中級者全般"),
            ("パターン⑤", "関税ショック×機会損失型",     "機会損失を感じている層"),
            ("パターン⑥", "6月やること3選型",           "実行力の高い層"),
            ("パターン⑦", "S&P500急落×ドル円連動型",   "株FX相関を意識する層"),
            ("パターン⑧", "始めるなら今週中型",         "FX未経験・初心者層"),
            ("パターン⑨", "証拠金3択教育型",           "資金効率を上げたい層"),
            ("パターン⑩", "本音トーク×今週の後悔型",   "機会損失を感じている層"),
        ]
        for num, name, note in entries:
            c.setFillColor(white)
            rr(c, ML, self.y - 8*mm, TW, 8*mm, 2*mm)
            c.setFillColor(GREEN); c.setFont("JA", 7.5)
            c.drawString(ML + 4*mm, self.y - 5.5*mm, num)
            c.setFillColor(NAVY); c.setFont("JA", 7.5)
            c.drawString(ML + 23*mm, self.y - 5.5*mm, name)
            c.setFillColor(GRAY); c.setFont("JA", 7)
            c.drawString(ML + 95*mm, self.y - 5.5*mm, f"→ {note}")
            self.y -= 9*mm

        # Design legend
        self.y -= 3*mm
        c.setFillColor(white)
        rr(c, ML, self.y - 22*mm, TW, 22*mm, 2*mm)
        c.setFillColor(NAVY); c.setFont("JA", 8.5)
        c.drawString(ML + 5*mm, self.y - 5*mm, "カード凡例")
        c.setFillColor(GREEN_L); rr(c, ML + 5*mm, self.y - 15*mm, 48*mm, 8*mm, 1.5*mm)
        c.setFillColor(GREEN);   c.rect(ML + 5*mm, self.y - 15*mm, 3*mm, 8*mm, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("JA", 7.5)
        c.drawString(ML + 11*mm, self.y - 11.5*mm, "本投稿カード")
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
        for hdr, cw in zip(headers, cols):
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
        self._ensure(28*mm)
        c.setFillColor(RED_L)
        rr(c, ML, self.y - 26*mm, TW, 26*mm, 2*mm)
        c.setFillColor(RED)
        c.rect(ML, self.y - 26*mm, 3*mm, 26*mm, fill=1, stroke=0)
        rr(c, ML, self.y - 26*mm, 3*mm, 26*mm, 2*mm)
        c.setFillColor(RED); c.setFont("JA", 8)
        c.drawString(ML + 6*mm, self.y - 5.5*mm,
                     "キャンペーン詳細：Vantage +10%入金ボーナス  |  6月9日(火)23:59まで")
        c.setFillColor(NAVY); c.setFont("JA", 7.5)
        notes = [
            "・URL: my78p.com/l/u/vtg（新規開設 + 入金でそのままボーナス適用）",
            "・10万円入金 → +1万円 / 5万円入金 → +5,000円（入金額の10%）",
            "・人によっては +20% / +30% になる場合あり（リプ欄に明記済み）",
        ]
        ny = self.y - 13*mm
        for n in notes:
            c.drawString(ML + 6*mm, ny, n)
            ny -= 5*mm
        self.y -= 28*mm

    # ════════════════════════════════════════════════════════
    # Save
    # ════════════════════════════════════════════════════════
    def save(self):
        self._pnum()
        self.c.save()


# ─────────────────────────────────────────────────────────
def main():
    out = Path("marketing/content-plan/hajime-campaign2-posts.pdf")
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
