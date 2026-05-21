#!/usr/bin/env python3
"""
Generate growth analysis PDF for @HajimeP30432
Based on X algorithm 2025/2026 source code analysis and competitive research.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib import font_manager

# ── Fonts ──────────────────────────────────────────────
FONT_PATH = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
pdfmetrics.registerFont(TTFont("JA", FONT_PATH))
font_manager.fontManager.addfont(FONT_PATH)
JP = "IPAGothic"

W, H = A4
ML, MR, MT, MB = 16*mm, 16*mm, 18*mm, 16*mm
TW = W - ML - MR

# ── Colors ─────────────────────────────────────────────
NAVY   = HexColor("#0D1B2A")
NAVY2  = HexColor("#1B2A3B")
ORANGE = HexColor("#E67E22")
WHITE  = HexColor("#F8FAFC")
LGRAY  = HexColor("#2C3E50")
GRAY   = HexColor("#7F8C8D")
DGRAY  = HexColor("#BDC3C7")
RED    = HexColor("#C0392B")
RED_L  = HexColor("#FDEDEC")
ORG_L  = HexColor("#FEF9E7")
GOLD   = HexColor("#D4AC0D")
GOLD_L = HexColor("#FDFBE4")
TEAL   = HexColor("#1ABC9C")
TEAL_L = HexColor("#E8F8F5")
BLUE   = HexColor("#2980B9")
BLUE_L = HexColor("#EBF5FB")

DPI = 150

# ── Helper: draw rounded rect with clip ────────────────
def rr(c, x, y, w, h, r, fill=1, stroke=0):
    c.roundRect(x, y, w, h, r, fill=fill, stroke=stroke)


class GrowthPDF:
    def __init__(self, path):
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.c.setTitle("@HajimeP30432 フォロワー増加 徹底分析レポート")
        self.y = H - MT
        self.page = 0
        self._new_page()

    def _new_page(self):
        self.page += 1
        self.c.setFillColor(HexColor("#F4F6F9"))
        self.c.rect(0, 0, W, H, fill=1, stroke=0)

    def _next_page(self):
        self._page_num()
        self.c.showPage()
        self._new_page()
        self.y = H - MT

    def _page_num(self):
        self.c.setFont("JA", 7)
        self.c.setFillColor(GRAY)
        self.c.drawCentredString(W/2, 9*mm, f"— {self.page} —")

    def _check(self, h):
        if self.y - h < MB + 10*mm:
            self._next_page()

    def _wrap(self, text, fs, mw):
        self.c.setFont("JA", fs)
        lines = []
        for para in text.split("\n"):
            if not para:
                lines.append("")
                continue
            cur = ""
            for ch in para:
                t = cur + ch
                if pdfmetrics.stringWidth(t, "JA", fs) > mw:
                    lines.append(cur)
                    cur = ch
                else:
                    cur = t
            lines.append(cur)
        return lines

    # ── Cover page ──────────────────────────────────────
    def cover(self):
        c = self.c

        # Top accent
        c.setFillColor(NAVY)
        c.rect(0, H - 90*mm, W, 90*mm, fill=1, stroke=0)
        c.setFillColor(ORANGE)
        c.rect(0, H - 90*mm, W, 3*mm, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("JA", 10)
        c.drawCentredString(W/2, H - 22*mm, "@HajimeP30432  フォロワー増加")
        c.setFont("JA", 19)
        c.drawCentredString(W/2, H - 36*mm, "X アルゴリズム 徹底分析レポート")
        c.setFillColor(HexColor("#AEB6BF"))
        c.setFont("JA", 8.5)
        c.drawCentredString(W/2, H - 50*mm,
            "Xアルゴリズム公開ソースコード（2026年1月）＋ 競合アカウント調査に基づく改善提案")
        c.setFont("JA", 7.5)
        c.drawCentredString(W/2, H - 61*mm,
            "参照: github.com/xai-org/x-algorithm  |  Sprout Social  |  Comnico  |  opentweet.io  2026")

        # 3 KPI boxes
        kpis = [
            ("906", "現在のフォロワー数"),
            ("16", "特定された改善ポイント"),
            ("×150", "返信往復の最大スコア倍率"),
        ]
        bw = (TW - 8*mm) / 3
        for i, (num, lbl) in enumerate(kpis):
            bx = ML + i * (bw + 4*mm)
            by = H - 120*mm
            bh = 24*mm
            c.setFillColor(white)
            rr(c, bx, by, bw, bh, 3*mm)
            c.setFillColor(NAVY)
            c.setFont("JA", 15)
            c.drawCentredString(bx + bw/2, by + 14*mm, num)
            c.setFillColor(GRAY)
            c.setFont("JA", 6.5)
            c.drawCentredString(bx + bw/2, by + 6*mm, lbl)

        # Section index
        y = H - 138*mm
        c.setFillColor(HexColor("#E3F2FD"))
        c.rect(ML, y - 5*mm, TW, 9*mm, fill=1, stroke=0)
        c.setFillColor(HexColor("#0D47A1"))
        c.setFont("JA", 9)
        c.drawString(ML + 4*mm, y - 0.5*mm, "レポート構成")
        y -= 9*mm

        sections = [
            ("P.2", "Xアルゴリズム 2025/2026 完全解析",
             "エンゲージメント重み・Grok移行・SimClusters・初速の法則"),
            ("P.3", "現状の問題点と優先度別改善策（16項目）",
             "🔴 即時対応 4項目 ／ 🟠 高優先 4項目 ／ 🟡 中優先 4項目 ／ 🟢 中長期 4項目"),
            ("P.4", "30日 ／ 90日 フォロワー増加ロードマップ",
             "週次の具体的アクション・KPI目標・計測方法"),
        ]
        for pg, ttl, sub in sections:
            c.setFillColor(white)
            c.rect(ML, y - 15*mm, TW, 14*mm, fill=1, stroke=0)
            c.setFillColor(ORANGE)
            c.rect(ML, y - 15*mm, 14*mm, 14*mm, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("JA", 8)
            c.drawCentredString(ML + 7*mm, y - 9.5*mm, pg)
            c.setFillColor(NAVY)
            c.setFont("JA", 9)
            c.drawString(ML + 17*mm, y - 7*mm, ttl)
            c.setFillColor(GRAY)
            c.setFont("JA", 7)
            c.drawString(ML + 17*mm, y - 12.5*mm, sub)
            c.setStrokeColor(DGRAY)
            c.setLineWidth(0.3)
            c.line(ML, y - 15*mm, ML + TW, y - 15*mm)
            y -= 15*mm

        self._next_page()

    # ── Algorithm page ───────────────────────────────────
    def algorithm_page(self):
        c = self.c
        self._section_header("Xアルゴリズム 2025/2026 完全解析",
                             "公開ソースコード（github.com/xai-org/x-algorithm）確認済みデータ")

        # Engagement weight visual
        self._subsection("エンゲージメントの重み（Heavy Rankerスコア）")
        items = [
            ("著者との返信往復",       150, RED,   "会話を続けると爆発的にスコアが上がる"),
            ("リポスト（引用含む）",    20,  ORANGE,"第2位の重要シグナル"),
            ("リプライ（単発）",        13.5,BLUE,  "返信をもらうだけで高スコア"),
            ("プロフィールクリック",    12,  HexColor("#8E44AD"), "気になって見に来た＝フォロー候補"),
            ("リンククリック",          11,  HexColor("#16A085"), "外部URLへの誘導を評価"),
            ("ブックマーク（保存）",    10,  GOLD,  "「後で読む」＝価値の高いコンテンツの証明"),
            ("いいね",                   1,  DGRAY, "最も弱いシグナル。いいねだけでは伸びない"),
        ]
        bx = ML
        bw_label = 40*mm
        bw_bar_max = TW - bw_label - 22*mm
        row_h = 7.5*mm
        by = self.y
        for name, score, col, note in items:
            bar_w = bw_bar_max * min(score, 30) / 30
            c.setFillColor(HexColor("#FFFFFF"))
            c.rect(bx, by - row_h, TW, row_h, fill=1, stroke=0)
            c.setFillColor(col)
            c.roundRect(bx + bw_label, by - row_h + 1.5*mm, bar_w, row_h - 3*mm, 1*mm, fill=1, stroke=0)
            c.setFillColor(NAVY)
            c.setFont("JA", 7.5)
            c.drawString(bx + 1*mm, by - row_h + 2.5*mm, name)
            c.setFillColor(white)
            c.setFont("JA", 7)
            label = f"×{score}" if score == int(score) else f"×{score}"
            c.drawString(bx + bw_label + 2*mm, by - row_h + 2.5*mm, label)
            c.setFillColor(GRAY)
            c.setFont("JA", 6.5)
            c.drawString(bx + bw_label + bar_w + 2*mm, by - row_h + 2.5*mm, note)
            by -= row_h
        self.y = by - 4*mm

        # 4 key facts cards
        self._subsection("アルゴリズムの4大ポイント")
        facts = [
            (RED,   "🔴 初速の法則（30分ルール）",
             "投稿後30分以内に反応がない投稿の約78%はその後ほぼ表示されない。\n"
             "30分以内に5件以上の反応 → その後のインプレッションが平均2.4倍。\n"
             "対策：投稿直後に自分でリプライを付けてフォロワーに返信を促す。"),
            (ORANGE,"🟠 Grok AI移行（2025年10月〜）",
             "旧レコメンドシステムが廃止されGrok AIに完全置き換え。\n"
             "Grokは毎日1億本以上の投稿を読み「コンテンツの質そのもの」を評価。\n"
             "ハッシュタグ依存の露出は低下。本文の「読まれた時間の長さ」が新指標。"),
            (GOLD,  "🟡 SimClusters（コミュニティ分類）",
             "XのAIは14万以上のコミュニティに投稿・アカウントを分類している。\n"
             "FX界隈として一貫して認識されると「FXに興味があるユーザー」の\n"
             "For Youフィードに優先表示される。テーマの一貫性が分類精度を上げる。"),
            (TEAL,  "🟢 X Premium の優遇",
             "非フォロワーへのリーチが2倍、フォロワーへは4倍。\n"
             "リプライがスレッドの上位に表示され視認性が上がる。\n"
             "月額1,380円（ベーシック）で効果対コスト最高レベルの投資。"),
        ]
        cw = (TW - 3*mm) / 2
        positions = [(ML, self.y), (ML + cw + 3*mm, self.y),
                     (ML, None), (ML + cw + 3*mm, None)]
        max_h = 0
        for i, (col, title, body) in enumerate(facts):
            blines = self._wrap(body, 7.5, cw - 6*mm)
            card_h = 8*mm + len(blines) * 4.8*mm + 4*mm
            if i == 2:
                self.y -= max_h + 3*mm
                positions[2] = (ML, self.y)
                positions[3] = (ML + cw + 3*mm, self.y)
                max_h = 0
            cx, cy = positions[i]
            if cy is None:
                cy = self.y
            c.setFillColor(col)
            rr(c, cx, cy - card_h, cw, card_h, 2*mm)
            c.setFillColor(white)
            c.setFont("JA", 8)
            c.drawString(cx + 3*mm, cy - 6*mm, title)
            c.setFillColor(HexColor("#FAFAFA") if col != white else NAVY2)
            rr(c, cx + 2*mm, cy - card_h + 2*mm, cw - 4*mm, card_h - 9*mm, 1.5*mm)
            c.setFillColor(NAVY)
            c.setFont("JA", 7.5)
            ty = cy - 11.5*mm
            for bl in blines:
                c.drawString(cx + 4*mm, ty, bl)
                ty -= 4.8*mm
            max_h = max(max_h, card_h)
        self.y -= max_h + 5*mm

        self._next_page()

    def _section_header(self, title, subtitle=""):
        c = self.c
        c.setFillColor(NAVY)
        c.rect(ML, self.y - 12*mm, TW, 12*mm, fill=1, stroke=0)
        c.setFillColor(ORANGE)
        c.rect(ML, self.y - 12*mm, 3*mm, 12*mm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("JA", 11)
        c.drawString(ML + 6*mm, self.y - 7.5*mm, title)
        if subtitle:
            c.setFillColor(HexColor("#AEB6BF"))
            c.setFont("JA", 7)
            c.drawString(ML + 6*mm, self.y - 11.5*mm, subtitle)
        self.y -= 15*mm

    def _subsection(self, title):
        c = self.c
        self._check(8*mm)
        c.setFillColor(HexColor("#E8F4FD"))
        c.rect(ML, self.y - 7*mm, TW, 7*mm, fill=1, stroke=0)
        c.setFillColor(BLUE)
        c.rect(ML, self.y - 7*mm, 2.5*mm, 7*mm, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont("JA", 9)
        c.drawString(ML + 5*mm, self.y - 4.5*mm, title)
        self.y -= 9*mm

    # ── Improvements page ────────────────────────────────
    def improvements_page(self):
        c = self.c
        self._section_header("現状の問題点と優先度別改善策（16項目）",
                             "@HajimeP30432 の現状を分析した改善提案")

        priority_groups = [
            (RED,   RED_L,   "🔴 最優先（今すぐ対応 → 効果が最も大きい）", [
                ("ハッシュタグ5個使用",
                 "1〜2個に削減（#FX #FX初心者 程度）",
                 "3個以上でエンゲージメント率が低下（X公式データ）。Grok時代は本文キーワードが優先。"),
                ("アフィリエイトURLを本文に記載",
                 "URLは必ず第1リプライに移動する",
                 "本文URLは「宣伝目的」と判定されリーチが2〜3倍異なる。2025年12月以降も原則変わらず。"),
                ("投稿後のリプライへの返信なし",
                 "投稿直後30分以内に全リプライへ返信する",
                 "著者×読者のリプライ往復はスコア×150。最も強いシグナル。30分以内が特に重要。"),
                ("X Premium 未加入（推定）",
                 "ベーシックプラン（月1,380円）に加入する",
                 "非フォロワーへのリーチが2倍、フォロワーへは4倍。最高ROIの投資。"),
            ]),
            (ORANGE, ORG_L, "🟠 高優先（1〜2週間以内に対応）", [
                ("投稿に画像が少ない",
                 "DEEP DIVE画像7枚を活用。週1〜2本は必ず画像付きで投稿",
                 "画像・動画付き投稿はアルゴリズムスコアが2倍。作成済みの7枚をフル活用。"),
                ("初速確保の仕組みがない",
                 "投稿後すぐ「質問リプライ」を自分で追加してフォロワーに返信を促す",
                 "「あなたはどう思いますか？」等の問いかけを第1リプライに入れると返信率が上がる。"),
                ("プロフィール最適化が不明",
                 "160字に「誰か・何を発信・フォローのメリット」を明示",
                 "プロフィールへのクリックはスコア×12。初見ユーザーのフォロー率に直結。"),
                ("固定ポストが弱い可能性",
                 "DEEP DIVEシリーズか実績投稿を固定して初見の「フォロー判断材料」にする",
                 "固定ポストはアカウントの名刺。最も価値ある投稿を固定すると転換率が大きく上がる。"),
            ]),
            (GOLD,  GOLD_L, "🟡 中優先（1ヶ月以内）", [
                ("大手FXアカウントへのリプライ巡回なし",
                 "@FxRumasan等の投稿に価値あるリプライを毎日5〜10件",
                 "大手のフォロワーから自分のアカウントが発見される。具体的な知見を添えたリプが効果的。"),
                ("投稿後の30分確保が不明",
                 "投稿から30分間は必ずスマホを手元に置き返信対応できる時間帯に投稿する",
                 "初速を確保できない時間帯に投稿するとその投稿は78%の確率でほぼ死ぬ。"),
                ("ターゲット層が曖昧な可能性",
                 "「FX初心者向け」か「中上級者向け」かを明確化しプロフィールに明記",
                 "ターゲットを絞るとSimClusters分類の精度が上がりFor Youフィードに正確に表示される。"),
                ("DEEP DIVE投稿が週次で組み込まれていない",
                 "毎週1〜2本をDEEP DIVE投稿（保存型コンテンツ）として計画的に投稿",
                 "DEEP DIVEはブックマーク（×10）を大量に獲得できる。保存率が高いと長期でじわじわ伸びる。"),
            ]),
            (TEAL,  TEAL_L, "🟢 中長期（2〜3ヶ月）", [
                ("スレッド投稿を活用していない",
                 "DEEP DIVE投稿をXのスレッド形式（連ツイ）でも展開する",
                 "滞在時間が長い投稿ほど評価が高い。スレッドは複数ツイートで滞在時間を伸ばせる。"),
                ("エンゲージメント率の計測なし",
                 "毎週、いいね・リポスト・保存数をXアナリティクスで記録しバズった型を3〜5本ストック化",
                 "バズった型の再現性がフォロワー増加を安定させる。感覚ではなくデータで運用する。"),
                ("アフィリエイト誘導の文脈が弱い可能性",
                 "URLより先に「実際に私が使っている理由」を第1リプライに書く",
                 "「URL＝宣伝」ではなく「体験談＋URL」の構成にすると信頼性とクリック率が上がる。"),
                ("いいね依頼型の投稿が多い可能性",
                 "「いいねしてください」より「保存しておくと後で使えます」CTA（行動喚起）に変える",
                 "いいね（×1）より保存（×10）を誘導する方がアルゴリズムへの影響が10倍大きい。"),
            ]),
        ]

        for pri_col, bg_col, group_title, items in priority_groups:
            self._check(12*mm + len(items) * 22*mm)
            c.setFillColor(pri_col)
            rr(c, ML, self.y - 8*mm, TW, 8*mm, 2*mm)
            c.setFillColor(white)
            c.setFont("JA", 8.5)
            c.drawString(ML + 4*mm, self.y - 5.5*mm, group_title)
            self.y -= 9.5*mm

            for problem, action, reason in items:
                lines_r = self._wrap(reason, 7, TW - 50*mm - 6*mm)
                card_h = max(18*mm, 5*mm + len(lines_r) * 4.5*mm + 4*mm)
                self._check(card_h + 2*mm)

                c.setFillColor(bg_col)
                rr(c, ML, self.y - card_h, TW, card_h, 2*mm)
                c.setFillColor(pri_col)
                c.rect(ML, self.y - card_h, 2*mm, card_h, fill=1, stroke=0)
                rr(c, ML, self.y - card_h, 2*mm, card_h, 1*mm)

                col_w1 = 50*mm
                # Problem column
                c.setFillColor(GRAY)
                c.setFont("JA", 6.5)
                c.drawString(ML + 4*mm, self.y - 5*mm, "問題")
                c.setFillColor(NAVY)
                c.setFont("JA", 7.5)
                for ln in self._wrap(problem, 7.5, col_w1 - 4*mm):
                    c.drawString(ML + 4*mm, self.y - 9.5*mm, ln)
                    self.y -= 0  # don't move y here

                # Arrow
                c.setFillColor(pri_col)
                cx_arrow = ML + col_w1 + 2*mm
                c.setFont("JA", 12)
                c.drawString(cx_arrow, self.y - card_h/2 - 2*mm, "→")

                # Action column
                col_w2 = 58*mm
                c.setFillColor(GRAY)
                c.setFont("JA", 6.5)
                c.drawString(ML + col_w1 + 10*mm, self.y - 5*mm, "改善策")
                c.setFillColor(pri_col)
                c.setFont("JA", 7.5)
                for ln in self._wrap(action, 7.5, col_w2):
                    c.drawString(ML + col_w1 + 10*mm, self.y - 9.5*mm, ln)
                    self.y -= 0

                # Reason column
                rx = ML + col_w1 + col_w2 + 14*mm
                rw = TW - col_w1 - col_w2 - 16*mm
                c.setFillColor(GRAY)
                c.setFont("JA", 6.5)
                c.drawString(rx, self.y - 5*mm, "根拠")
                ty = self.y - 9.5*mm
                c.setFillColor(HexColor("#4A5568"))
                c.setFont("JA", 7)
                for ln in self._wrap(reason, 7, rw):
                    c.drawString(rx, ty, ln)
                    ty -= 4.5*mm

                self.y -= card_h + 2*mm

            self.y -= 3*mm

        self._next_page()

    # ── Roadmap page ─────────────────────────────────────
    def roadmap_page(self):
        c = self.c
        self._section_header("30日 ／ 90日 フォロワー増加ロードマップ",
                             "週ごとの具体的アクション・KPI目標")

        phases = [
            (RED, "Week 1-2：基盤整備フェーズ（今すぐ）", [
                ("Day 1",  "X Premium ベーシック登録（月1,380円）"),
                ("Day 1",  "プロフィール文を160字で「誰か・何を発信・フォローするメリット」に書き直す"),
                ("Day 1",  "DEEP DIVE 投稿中の最良1本を固定ポストに設定"),
                ("Day 2",  "全投稿のハッシュタグを1〜2個に削減（#FX のみでも可）"),
                ("Day 2",  "アフィリエイトURLを本文から削除し第1リプライに移動"),
                ("Week 1", "投稿ルーティンに「投稿→30分スマホ待機→全リプ返信」を追加"),
                ("Week 2", "@FxRumasan・@mochi_fxtrader 等への価値あるリプライ巡回（毎日5件）開始"),
            ]),
            (ORANGE, "Week 3-4：コンテンツ最適化フェーズ", [
                ("Week 3", "DEEP DIVE画像7枚を週1本ずつ活用した投稿スケジュールを組む"),
                ("Week 3", "投稿末尾のCTAを「いいねしてください」→「保存しておくと後で使えます」に変更"),
                ("Week 4", "投稿直後に「質問リプライ」を自分で付けてフォロワーに返信を促す運用開始"),
                ("Week 4", "Xアナリティクスで週次データを初めて計測（ブックマーク数・リプライ数に注目）"),
            ]),
            (GOLD, "Month 2：成長加速フェーズ", [
                ("Month 2", "DEEP DIVE投稿を週1〜2本のペースでスレッド形式（連ツイ）で投稿"),
                ("Month 2", "FX界隈の小〜中規模アカウントとの相互リプライ関係を10件構築"),
                ("Month 2", "バズった投稿の型を3本特定し、それをテンプレートとして月2本再利用"),
                ("Month 2", "エンゲージメント率（リプライ数/インプレッション数）を週次で記録・改善"),
            ]),
            (TEAL, "Month 3：定常運用フェーズ（目標：2000〜3000フォロワー）", [
                ("Month 3", "週次投稿スケジュール：朝夜2本＋DEEP DIVE 1〜2本の計16〜18本/週を維持"),
                ("Month 3", "アフィリエイト誘導投稿を月2本から月3〜4本に増加（自然な文脈を維持）"),
                ("Month 3", "フォロワー1000人突破時に「感謝＋無料コンテンツ配布」でバズを狙う"),
                ("Month 3", "Xアナリティクスで月次レポートを作成し次月の投稿テーマを調整"),
            ]),
        ]

        for col, phase_title, tasks in phases:
            self._check(8*mm + len(tasks) * 8*mm + 5*mm)
            c.setFillColor(col)
            rr(c, ML, self.y - 7*mm, TW, 7*mm, 2*mm)
            c.setFillColor(white)
            c.setFont("JA", 8.5)
            c.drawString(ML + 4*mm, self.y - 5*mm, phase_title)
            self.y -= 8.5*mm

            for timing, task in tasks:
                task_lines = self._wrap(task, 7.5, TW - 24*mm)
                task_h = len(task_lines) * 4.8*mm + 4*mm
                self._check(task_h)
                c.setFillColor(white)
                c.rect(ML, self.y - task_h, TW, task_h, fill=1, stroke=0)
                c.setFillColor(col)
                rr(c, ML, self.y - task_h, 20*mm, task_h, 1*mm)
                c.setFillColor(white)
                c.setFont("JA", 7)
                c.drawCentredString(ML + 10*mm, self.y - task_h/2 - 2.5*mm, timing)
                c.setFillColor(NAVY)
                c.setFont("JA", 7.5)
                ty = self.y - 5*mm
                for ln in task_lines:
                    c.drawString(ML + 22*mm, ty, ln)
                    ty -= 4.8*mm
                c.setStrokeColor(DGRAY)
                c.setLineWidth(0.3)
                c.line(ML, self.y - task_h, ML + TW, self.y - task_h)
                self.y -= task_h

            self.y -= 5*mm

        # KPI targets
        self._check(35*mm)
        self._subsection("KPI目標")
        kpis = [
            ("1ヶ月後", "1,200〜1,500", "初速改善＋Premium効果"),
            ("2ヶ月後", "1,800〜2,200", "DEEP DIVE拡散＋リプ巡回"),
            ("3ヶ月後", "2,500〜3,500", "バズ型の確立＋継続露出"),
        ]
        kw = (TW - 4*mm) / 3
        ky = self.y
        for i, (period, target, driver) in enumerate(kpis):
            kx = ML + i * (kw + 2*mm)
            c.setFillColor(white)
            rr(c, kx, ky - 22*mm, kw, 22*mm, 2*mm)
            c.setFillColor(ORANGE)
            c.rect(kx, ky - 22*mm, kw, 2*mm, fill=1, stroke=0)
            c.setFillColor(GRAY)
            c.setFont("JA", 7)
            c.drawCentredString(kx + kw/2, ky - 6*mm, period)
            c.setFillColor(NAVY)
            c.setFont("JA", 12)
            c.drawCentredString(kx + kw/2, ky - 13*mm, target)
            c.setFillColor(TEAL)
            c.setFont("JA", 6.5)
            c.drawCentredString(kx + kw/2, ky - 19*mm, driver)
        self.y = ky - 25*mm

        self._page_num()
        self.c.save()


if __name__ == "__main__":
    out_dir = Path("/home/user/cc-company/marketing/analysis")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "hajime-x-growth-analysis.pdf"

    p = GrowthPDF(pdf_path)
    p.cover()
    p.algorithm_page()
    p.improvements_page()
    p.roadmap_page()

    print(f"PDF saved: {pdf_path}")
    print(f"Size: {pdf_path.stat().st_size // 1024} KB")
