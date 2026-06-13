#!/usr/bin/env python3
"""
Generate Twitter/X-optimized images (1200×675px) for DEEP DIVE posts.
Target posts: DD-01, DD-04, DD-05, DD-06, DD-07, DD-08, DD-10
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as patches
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

# Register Japanese font
font_manager.fontManager.addfont("/usr/share/fonts/truetype/fonts-japanese-gothic.ttf")
JP = "IPAGothic"
matplotlib.rcParams["font.family"] = JP
matplotlib.rcParams["axes.unicode_minus"] = False

OUT = Path("/home/user/cc-company/marketing/content-plan/images")
OUT.mkdir(exist_ok=True)

# Brand colors
NAVY    = "#0D1B2A"
ORANGE  = "#E67E22"
WHITE   = "#F0F4F8"
GRAY    = "#7F8C8D"
LGRAY   = "#2C3E50"
GREEN   = "#27AE60"
RED     = "#C0392B"
BLUE    = "#2980B9"
PURPLE  = "#8E44AD"
GOLD    = "#F1C40F"
TEAL    = "#1ABC9C"

W, H, DPI = 1200, 675, 150


def fig_base(title_jp, subtitle=""):
    """Create a base dark figure with title."""
    fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI, facecolor=NAVY)
    # Top accent bar
    ax_bar = fig.add_axes([0, 0.96, 1, 0.04])
    ax_bar.set_facecolor(ORANGE)
    ax_bar.set_xticks([]); ax_bar.set_yticks([])
    for sp in ax_bar.spines.values(): sp.set_visible(False)
    # Title area
    ax_ttl = fig.add_axes([0, 0.82, 1, 0.14])
    ax_ttl.set_facecolor(NAVY)
    ax_ttl.set_xlim(0, 1); ax_ttl.set_ylim(0, 1)
    ax_ttl.set_xticks([]); ax_ttl.set_yticks([])
    for sp in ax_ttl.spines.values(): sp.set_visible(False)
    ax_ttl.text(0.04, 0.72, title_jp, color=WHITE, fontsize=15,
                fontweight="bold", va="top", fontfamily=JP)
    if subtitle:
        ax_ttl.text(0.04, 0.28, subtitle, color=GRAY, fontsize=9,
                    va="bottom", fontfamily=JP)
    # Watermark
    ax_ttl.text(0.97, 0.5, "@hajime_fx", color=GRAY, fontsize=8,
                ha="right", va="center", fontfamily=JP)
    return fig


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=NAVY)
    plt.close(fig)
    print(f"  Saved: {path.name}")


# ─────────────────────────────────────────────
# DD-01: 流動性スイープ概念図
# ─────────────────────────────────────────────
def make_dd01():
    fig = fig_base(
        "DD-01  スマートマネーの「流動性スイープ」とは",
        "機関投資家はなぜ個人のストップを狩るのか"
    )
    ax = fig.add_axes([0.04, 0.06, 0.92, 0.74])
    ax.set_facecolor(LGRAY)
    for sp in ax.spines.values():
        sp.set_color("#4A5568"); sp.set_linewidth(0.5)
    ax.tick_params(colors=GRAY, labelsize=7)
    ax.set_xlabel("時間 →", color=GRAY, fontsize=8, fontfamily=JP)
    ax.set_ylabel("価格", color=GRAY, fontsize=8, fontfamily=JP)
    ax.yaxis.label.set_rotation(0)

    # Price path
    np.random.seed(42)
    p = [100.0]
    for _ in range(30): p.append(p[-1] + np.random.randn()*0.4)
    for i in range(20): p.append(p[-1] + (103.5 - p[-1])/(20-i+1))
    for _ in range(15): p.append(p[-1] + np.random.randn()*0.25)
    sweep_start = len(p)
    # Sweep down below support
    support = min(p[-15:]) - 0.3
    for i in range(8):
        val = p[-1] - (p[-1] - (support - 0.8)) * (i+1) / 8
        p.append(val)
    # Bounce up strong
    sweep_low = p[-1]
    for i in range(15):
        p.append(sweep_low + (106.0 - sweep_low) * (i+1) / 15 * (1 + 0.05*np.random.randn()))
    p = np.array(p)
    x = np.arange(len(p))

    support_level = min(p[35:sweep_start]) - 0.2

    # Plot price line
    ax.plot(x[:sweep_start], p[:sweep_start], color=WHITE, linewidth=2, alpha=0.9)
    ax.plot(x[sweep_start:sweep_start+8], p[sweep_start:sweep_start+8],
            color=RED, linewidth=2.5, label="スイープ（罠）")
    ax.plot(x[sweep_start+8:], p[sweep_start+8:],
            color=GREEN, linewidth=2.5, label="強い反転上昇")

    # Support line
    ax.axhline(support_level, color=ORANGE, linewidth=1.5, linestyle="--", alpha=0.8)
    ax.text(2, support_level + 0.1, "サポートライン", color=ORANGE,
            fontsize=8, fontfamily=JP, va="bottom")

    # Annotation: Stop clusters below support
    ax.scatter([sweep_start-2, sweep_start-3, sweep_start-4],
               [support_level-0.05, support_level-0.1, support_level-0.08],
               color=RED, s=40, zorder=5, marker="x", linewidths=2)
    ax.annotate("個人のストップロス注文が集中",
                xy=(sweep_start-3, support_level-0.1),
                xytext=(sweep_start-18, support_level-1.0),
                color=RED, fontsize=8, fontfamily=JP,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))

    # Annotation: Sweep
    sweep_idx = sweep_start + 4
    ax.annotate("ストップを根こそぎ刈り取る\n（流動性スイープ）",
                xy=(sweep_idx, p[sweep_idx]),
                xytext=(sweep_idx + 5, p[sweep_idx] - 1.5),
                color=RED, fontsize=8.5, fontfamily=JP,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))

    # Annotation: Reversal
    rev_idx = sweep_start + 20
    ax.annotate("機関が本来の方向へ\n（強い上昇開始）",
                xy=(rev_idx, p[rev_idx]),
                xytext=(rev_idx + 2, p[rev_idx] - 2),
                color=GREEN, fontsize=8.5, fontfamily=JP,
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))

    ax.legend(loc="upper left", facecolor=LGRAY, edgecolor=GRAY,
              labelcolor=WHITE, fontsize=8, prop={"family": JP, "size": 8})
    ax.set_xlim(0, len(p) + 2)
    ax.grid(axis="y", color="#4A5568", linewidth=0.4, alpha=0.5)

    save(fig, "dd01-liquidity-sweep.png")


# ─────────────────────────────────────────────
# DD-04: リスクリワード比較
# ─────────────────────────────────────────────
def make_dd04():
    fig = fig_base(
        "DD-04  「1:3 RR」が最強ではない理由",
        "期待値が同じでも、メンタル負荷は全く違う"
    )
    ax = fig.add_axes([0.06, 0.08, 0.88, 0.72])
    ax.set_facecolor(LGRAY)
    for sp in ax.spines.values(): sp.set_color("#4A5568"); sp.set_linewidth(0.5)

    # Simulate 30-trade sequence for each trader
    np.random.seed(7)
    n = 30

    def simulate(win_rate, rr, n=30, seed=7):
        np.random.seed(seed)
        results = np.where(np.random.rand(n) < win_rate, rr, -1.0)
        return np.cumsum(results)

    curveA = simulate(0.30, 3.0)
    curveB = simulate(0.60, 1.0)

    x = np.arange(1, n + 1)
    ax.plot(x, curveA, color=ORANGE, linewidth=2.5, label="Trader A: 勝率30% / 1:3 RR", marker="o",
            markersize=4, markevery=5)
    ax.plot(x, curveB, color=TEAL, linewidth=2.5, label="Trader B: 勝率60% / 1:1 RR", marker="s",
            markersize=4, markevery=5)
    ax.axhline(0, color=WHITE, linewidth=0.8, linestyle=":")

    # Expected value labels
    ev_a = 0.30 * 3 - 0.70 * 1
    ev_b = 0.60 * 1 - 0.40 * 1
    ax.text(n + 0.5, curveA[-1], f" 期待値 +{ev_a:.1f}R", color=ORANGE, fontsize=9, fontfamily=JP, va="center")
    ax.text(n + 0.5, curveB[-1], f" 期待値 +{ev_b:.1f}R", color=TEAL, fontsize=9, fontfamily=JP, va="center")

    ax.set_xlabel("トレード回数", color=GRAY, fontsize=9, fontfamily=JP)
    ax.set_ylabel("累積損益（R）", color=GRAY, fontsize=9, fontfamily=JP)
    ax.yaxis.label.set_rotation(0); ax.yaxis.set_label_coords(-0.06, 0.5)
    ax.tick_params(colors=GRAY, labelsize=8)
    ax.grid(color="#4A5568", linewidth=0.4, alpha=0.5)
    ax.legend(loc="upper left", facecolor=LGRAY, edgecolor=GRAY,
              labelcolor=WHITE, prop={"family": JP, "size": 9})

    # Infobox
    info_ax = fig.add_axes([0.72, 0.12, 0.24, 0.30])
    info_ax.set_facecolor(NAVY); info_ax.set_xlim(0, 1); info_ax.set_ylim(0, 1)
    for sp in info_ax.spines.values(): sp.set_color(ORANGE); sp.set_linewidth(1)
    info_ax.set_xticks([]); info_ax.set_yticks([])
    lines = [
        ("期待値は同じ", WHITE, 11),
        ("でも A は", GRAY, 9),
        ("10回に7回負ける", RED, 10),
        ("B は", GRAY, 9),
        ("10回に4回しか負けない", TEAL, 10),
    ]
    for i, (txt, col, fs) in enumerate(lines):
        info_ax.text(0.5, 0.88 - i * 0.17, txt, color=col, fontsize=fs,
                     ha="center", va="top", fontfamily=JP, fontweight="bold" if fs > 9 else "normal")

    save(fig, "dd04-riskreward.png")


# ─────────────────────────────────────────────
# DD-05: ケリー基準 資産推移
# ─────────────────────────────────────────────
def make_dd05():
    fig = fig_base(
        "DD-05  リスク%を変えると資産曲線はどう変わるか",
        "勝率60% / 同じ手法でもロットが命運を分ける"
    )
    ax = fig.add_axes([0.07, 0.08, 0.88, 0.72])
    ax.set_facecolor(LGRAY)
    for sp in ax.spines.values(): sp.set_color("#4A5568"); sp.set_linewidth(0.5)

    np.random.seed(99)
    n = 200
    win_rate = 0.60
    results = np.where(np.random.rand(n) < win_rate, 1, -1)  # +1 win -1 loss

    risks = [0.01, 0.05, 0.10, 0.20]
    colors_r = [TEAL, ORANGE, GOLD, RED]
    labels_r = ["1% リスク（推奨）", "5% リスク", "10% リスク", "20% リスク（危険）"]

    for risk, col, lbl in zip(risks, colors_r, labels_r):
        account = [1.0]
        for r in results:
            if r == 1:
                account.append(account[-1] * (1 + risk))
            else:
                account.append(account[-1] * (1 - risk))
        ax.plot(np.arange(n + 1), account, color=col, linewidth=2, label=lbl, alpha=0.9)

    ax.axhline(1.0, color=WHITE, linewidth=0.6, linestyle=":")
    ax.set_xlabel("トレード回数", color=GRAY, fontsize=9, fontfamily=JP)
    ax.set_ylabel("資産倍率", color=GRAY, fontsize=9, fontfamily=JP)
    ax.yaxis.label.set_rotation(0); ax.yaxis.set_label_coords(-0.07, 0.5)
    ax.tick_params(colors=GRAY, labelsize=8)
    ax.grid(color="#4A5568", linewidth=0.4, alpha=0.5)
    ax.legend(loc="upper left", facecolor=LGRAY, edgecolor=GRAY,
              labelcolor=WHITE, prop={"family": JP, "size": 9})
    ax.set_ylim(bottom=0)

    save(fig, "dd05-kelly-criterion.png")


# ─────────────────────────────────────────────
# DD-06: キルゾーン 24時間タイムライン
# ─────────────────────────────────────────────
def make_dd06():
    fig = fig_base(
        "DD-06  相場が動く「キルゾーン」（日本時間）",
        "プロはこの時間帯だけに集中する"
    )
    ax = fig.add_axes([0.04, 0.08, 0.92, 0.70])
    ax.set_facecolor(LGRAY)
    for sp in ax.spines.values(): sp.set_color("#4A5568"); sp.set_linewidth(0.5)
    ax.set_xlim(0, 24); ax.set_ylim(0, 1)
    ax.set_xticks(range(0, 25, 1))
    ax.set_xticklabels([f"{h}時" if h % 3 == 0 else "" for h in range(25)],
                       color=GRAY, fontsize=7, fontfamily=JP)
    ax.set_yticks([])

    sessions = [
        # (start, end, color, label, y_offset)
        (0,   6,   "#1A252F", "薄商い（トレード非推奨）", 0.55),
        (6,   9,   "#1A3A4A", "アジア移行", 0.55),
        (9,   11,  "#F39C12", "東京キルゾーン", 0.55),
        (11,  15,  "#2E4057", "欧州オープン待ち", 0.55),
        (15,  17,  "#2980B9", "ロンドン\nキルゾーン", 0.55),
        (17,  21,  "#2E4057", "NY オープン待ち", 0.55),
        (21,  23,  "#C0392B", "NY キルゾーン", 0.55),
        (23,  24,  "#1A252F", "薄商い", 0.55),
    ]
    kill_sessions = {
        (9, 11):  (ORANGE, "東京キルゾーン\n9:00〜11:00"),
        (15, 17): (BLUE,   "ロンドン\nキルゾーン\n15:00〜17:00"),
        (21, 23): (RED,    "NY キルゾーン\n21:00〜23:00"),
    }

    # Background blocks
    for start, end, col, label, _ in sessions:
        ax.barh(0.5, end - start, left=start, height=0.5,
                color=col, alpha=0.9, edgecolor="#4A5568", linewidth=0.3)
        mid = (start + end) / 2
        if end - start >= 2:
            ax.text(mid, 0.5, label, ha="center", va="center",
                    color=WHITE if col not in ("#1A252F", "#2E4057", "#2E4057") else GRAY,
                    fontsize=7, fontfamily=JP, multialignment="center")

    # Kill zone arrows + labels
    label_heights = [0.08, 0.22, 0.08]
    for (s, e), (col, lbl) in kill_sessions.items():
        mid = (s + e) / 2
        ax.annotate("", xy=(mid, 0.24), xytext=(mid, 0.06),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2))
        ax.text(mid, 0.04, lbl, ha="center", va="top",
                color=col, fontsize=7.5, fontfamily=JP,
                fontweight="bold", multialignment="center")

    # Danger zone annotation
    ax.annotate("注意：ロンドンが\nアジアのレンジを\n「狩る」動き多発",
                xy=(16, 0.75), xytext=(18, 0.75),
                color=ORANGE, fontsize=7.5, fontfamily=JP,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2),
                ha="left", va="center")

    ax.set_xlabel("日本時間（JST）", color=GRAY, fontsize=9, fontfamily=JP)
    ax.grid(axis="x", color="#4A5568", linewidth=0.3, alpha=0.4)

    save(fig, "dd06-killzones.png")


# ─────────────────────────────────────────────
# DD-07: チャートパターン成功率
# ─────────────────────────────────────────────
def make_dd07():
    fig = fig_base(
        "DD-07  チャートパターンの本当の成功率",
        "Peter Brandt / Bulkowski 調査ベース"
    )
    ax = fig.add_axes([0.32, 0.10, 0.62, 0.70])
    ax.set_facecolor(LGRAY)
    for sp in ax.spines.values(): sp.set_color("#4A5568"); sp.set_linewidth(0.5)

    patterns = [
        ("カップアンドハンドル",     65, TEAL),
        ("フラッグ・ペナント",        65, TEAL),
        ("ヘッドアンドショルダー",   60, ORANGE),
        ("ウェッジ（収束型）",        58, ORANGE),
        ("対称三角保ち合い",          54, GOLD),
        ("ダブルトップ・ボトム",      58, ORANGE),
    ]

    labels = [p[0] for p in patterns]
    rates  = [p[1] for p in patterns]
    colors = [p[2] for p in patterns]
    y_pos  = range(len(labels))

    bars = ax.barh(y_pos, rates, color=colors, edgecolor=NAVY, linewidth=0.5, height=0.6)
    ax.axvline(50, color=WHITE, linewidth=1, linestyle=":", alpha=0.5)
    ax.text(50.5, len(labels) - 0.1, "コイントスライン\n（50%）",
            color=WHITE, fontsize=7, fontfamily=JP, alpha=0.6)

    for bar, rate in zip(bars, rates):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{rate}%", va="center", ha="left", color=WHITE,
                fontsize=10, fontfamily=JP, fontweight="bold")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=WHITE, fontsize=9, fontfamily=JP)
    ax.set_xlim(40, 75)
    ax.set_xlabel("成功率 (%)", color=GRAY, fontsize=9, fontfamily=JP)
    ax.tick_params(colors=GRAY, labelsize=8)
    ax.grid(axis="x", color="#4A5568", linewidth=0.4, alpha=0.5)

    # Legend
    handles = [
        mpatches.Patch(color=TEAL, label="比較的高い"),
        mpatches.Patch(color=ORANGE, label="中程度"),
        mpatches.Patch(color=GOLD, label="ほぼコイントス"),
    ]
    ax.legend(handles=handles, loc="lower right", facecolor=LGRAY,
              edgecolor=GRAY, labelcolor=WHITE, prop={"family": JP, "size": 8})

    # Side note
    note_ax = fig.add_axes([0.04, 0.10, 0.26, 0.70])
    note_ax.set_facecolor(NAVY); note_ax.set_xlim(0, 1); note_ax.set_ylim(0, 1)
    for sp in note_ax.spines.values(): sp.set_color(ORANGE); sp.set_linewidth(1)
    note_ax.set_xticks([]); note_ax.set_yticks([])
    note_ax.text(0.5, 0.95, "有効な条件", color=ORANGE, fontsize=10,
                 ha="center", va="top", fontfamily=JP, fontweight="bold")
    conditions = [
        "① 上位足の\nトレンドと\n同方向",
        "② 出来高が\n収束→\nブレイクで急増",
        "③ 十分な\n「ため」が\nある",
    ]
    for i, c in enumerate(conditions):
        note_ax.text(0.5, 0.78 - i * 0.27, c, color=WHITE, fontsize=9,
                     ha="center", va="top", fontfamily=JP, multialignment="center")
        if i < 2:
            note_ax.axhline(0.64 - i * 0.27, color="#4A5568", linewidth=0.5)

    save(fig, "dd07-chart-patterns.png")


# ─────────────────────────────────────────────
# DD-08: プロスペクト理論（損失回避バイアス）
# ─────────────────────────────────────────────
def make_dd08():
    fig = fig_base(
        "DD-08  損切りできないのは「脳の本能」",
        "プロスペクト理論：損失の痛みは利益の喜びの2〜2.5倍"
    )
    ax = fig.add_axes([0.08, 0.10, 0.88, 0.70])
    ax.set_facecolor(LGRAY)
    for sp in ax.spines.values(): sp.set_color("#4A5568"); sp.set_linewidth(0.5)

    x_gain = np.linspace(0, 100, 300)
    x_loss = np.linspace(0, -100, 300)

    # Concave gain curve (diminishing sensitivity)
    y_gain = 80 * (x_gain / 100) ** 0.6
    # Convex loss curve (steeper, loss aversion = 2.25x)
    y_loss = -2.25 * 80 * (-x_loss / 100) ** 0.6

    ax.plot(x_gain, y_gain, color=GREEN, linewidth=3, label="利益（喜び）")
    ax.plot(x_loss, y_loss, color=RED, linewidth=3, label="損失（痛み）")

    ax.axhline(0, color=WHITE, linewidth=0.6, linestyle=":")
    ax.axvline(0, color=WHITE, linewidth=0.6, linestyle=":")

    # Annotation: 5万円
    v = 50
    y_g = 80 * (v / 100) ** 0.6
    y_l = -2.25 * 80 * (v / 100) ** 0.6
    ax.annotate(f"+{v}万円の喜び\n= {y_g:.0f}",
                xy=(v, y_g), xytext=(v + 15, y_g + 8),
                color=GREEN, fontsize=9, fontfamily=JP,
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))
    ax.annotate(f"−{v}万円の痛み\n= {y_l:.0f}（2.25倍！）",
                xy=(-v, y_l), xytext=(-v - 15, y_l - 12),
                color=RED, fontsize=9, fontfamily=JP,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))

    # Reference lines
    ax.plot([v, v], [0, y_g], color=GREEN, linewidth=1, linestyle="--", alpha=0.5)
    ax.plot([-v, -v], [0, y_l], color=RED, linewidth=1, linestyle="--", alpha=0.5)
    ax.plot([0, v], [y_g, y_g], color=GREEN, linewidth=1, linestyle="--", alpha=0.5)
    ax.plot([0, -v], [y_l, y_l], color=RED, linewidth=1, linestyle="--", alpha=0.5)

    ax.set_xlabel("損益金額（万円）", color=GRAY, fontsize=9, fontfamily=JP)
    ax.set_ylabel("心理的な価値", color=GRAY, fontsize=9, fontfamily=JP)
    ax.yaxis.set_label_coords(-0.07, 0.5)
    ax.tick_params(colors=GRAY, labelsize=8)
    ax.grid(color="#4A5568", linewidth=0.4, alpha=0.5)
    ax.legend(loc="upper left", facecolor=LGRAY, edgecolor=GRAY,
              labelcolor=WHITE, prop={"family": JP, "size": 10})

    save(fig, "dd08-prospect-theory.png")


# ─────────────────────────────────────────────
# DD-10: ドローダウン回復率
# ─────────────────────────────────────────────
def make_dd10():
    fig = fig_base(
        "DD-10  ドローダウンが大きいほど「回復が不可能」になる",
        "大きく負けないことが、大きく勝うことより重要"
    )
    ax = fig.add_axes([0.10, 0.12, 0.85, 0.68])
    ax.set_facecolor(LGRAY)
    for sp in ax.spines.values(): sp.set_color("#4A5568"); sp.set_linewidth(0.5)

    drawdowns = [10, 20, 30, 40, 50, 60, 70, 80]
    recovery  = [dd / (1 - dd / 100) for dd in drawdowns]

    bar_colors = [TEAL if r < 30 else (ORANGE if r < 80 else RED) for r in recovery]
    bars = ax.bar(drawdowns, recovery, width=7, color=bar_colors, edgecolor=NAVY,
                  linewidth=0.5, zorder=3)

    # Value labels on top of bars
    for bar, rec in zip(bars, recovery):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                f"+{rec:.0f}%", ha="center", va="bottom",
                color=WHITE, fontsize=9.5, fontfamily=JP, fontweight="bold")

    ax.set_xlabel("ドローダウン (%)", color=GRAY, fontsize=10, fontfamily=JP)
    ax.set_ylabel("回復に必要な利益率 (%)", color=GRAY, fontsize=9, fontfamily=JP)
    ax.yaxis.set_label_coords(-0.09, 0.5)
    ax.set_xticks(drawdowns)
    ax.set_xticklabels([f"−{d}%" for d in drawdowns], color=GRAY, fontsize=9, fontfamily=JP)
    ax.tick_params(axis="y", colors=GRAY, labelsize=8)
    ax.set_ylim(0, max(recovery) * 1.18)
    ax.grid(axis="y", color="#4A5568", linewidth=0.4, alpha=0.5, zorder=0)

    # Danger threshold line
    ax.axvline(20, color=ORANGE, linewidth=1.5, linestyle="--", alpha=0.8, zorder=4)
    ax.text(20.5, max(recovery) * 0.9, "要注意ライン\n（20% DD）",
            color=ORANGE, fontsize=8, fontfamily=JP, va="top")

    # Color legend
    handles = [
        mpatches.Patch(color=TEAL, label="安全圏"),
        mpatches.Patch(color=ORANGE, label="要注意"),
        mpatches.Patch(color=RED, label="危険域"),
    ]
    ax.legend(handles=handles, loc="upper left", facecolor=LGRAY,
              edgecolor=GRAY, labelcolor=WHITE, prop={"family": JP, "size": 9})

    save(fig, "dd10-drawdown-recovery.png")


if __name__ == "__main__":
    print("Generating Deep Dive images...")
    make_dd01()
    make_dd04()
    make_dd05()
    make_dd06()
    make_dd07()
    make_dd08()
    make_dd10()
    print(f"Done! 7 images saved to {OUT}")
