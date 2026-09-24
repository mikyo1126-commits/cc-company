#!/usr/bin/env python3
"""
多角的分析結果を workflow/insights.md に書き込む
analyze_posts.py と同じロジックを内包して単独実行可能
"""

import os
import re
import sys
import tweepy
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pathlib import Path

JST = timezone(timedelta(hours=9))
ROOT_DIR = Path(__file__).parent.parent
INSIGHTS_PATH = ROOT_DIR / "workflow" / "insights.md"

BTC_KEYWORDS    = ["ビットコイン", "BTC", "bitcoin", "btc"]
GOLD_KEYWORDS   = ["ゴールド", "金", "gold", "XAU"]
FX_KEYWORDS     = ["ドル円", "ユーロ", "ポンド", "為替", "FX", "fx", "ドル"]
MACRO_KEYWORDS  = ["FOMC", "fomc", "日銀", "FRB", "CPI", "雇用統計", "GDP", "利上げ", "利下げ"]
MIND_KEYWORDS   = ["心理", "メンタル", "感情", "バイアス", "失敗", "経験", "学び", "思う", "感じ", "怖", "欲"]
CHART_TERMS     = ["三尊", "ネックライン", "押し目", "戻り目", "移動平均", "週足", "日足", "月足",
                   "ピンバー", "ブレイク", "サポート", "レジスタンス", "トレンド転換", "MACD"]
COLLOQUIAL      = ["けど", "だけど", "でも", "なんか", "かも", "っぽい", "謎に", "なんで",
                   "ちゃんと", "やっぱ", "やっぱり", "ぶっちゃけ", "正直", "わりと", "割と",
                   "ちょっと", "どっち", "どうせ", "とか", "みたいな", "じゃん", "じゃないか",
                   "よな", "よね", "かな", "かね", "し", "まじ", "マジ"]
PERSONAL_EXP    = ["昨日", "先週", "先月", "今日", "今週", "今朝", "今夜", "さっき",
                   "経験", "失敗", "やらかし", "やってしまっ"]
EMOTION_MARKERS = ["🚀", "🤔", "😅", "💪", "🔥", "⚡", "🎯", "😭", "！"]
UNCERTAINTY     = ["かも", "かもしれ", "っぽい", "気がする", "思う", "じゃないか", "可能性",
                   "でしょう", "と見ている", "ではないか"]


def get_client():
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )


def classify_topic(text):
    t = text.lower()
    if any(k.lower() in t for k in BTC_KEYWORDS):   return "BTC"
    if any(k.lower() in t for k in GOLD_KEYWORDS):  return "ゴールド"
    if any(k.lower() in t for k in MACRO_KEYWORDS): return "マクロ"
    if any(k.lower() in t for k in FX_KEYWORDS):    return "FX"
    if any(k in t for k in MIND_KEYWORDS):           return "マインド"
    return "その他"


def score_tweet(m):
    return (m["like_count"] * 3 + m["retweet_count"] * 5
            + m["reply_count"] * 2 + m.get("bookmark_count", 0) * 2)


def analyze_tweet(t):
    m = t.public_metrics
    text = t.text
    lines = [l for l in text.strip().split("\n") if l.strip()]
    paragraphs = [p for p in text.strip().split("\n\n") if p.strip()]
    created = t.created_at.astimezone(JST) if t.created_at else None

    return {
        "text": text,
        "chars": len(text),
        "lines": len(lines),
        "paragraphs": max(1, len(paragraphs)),
        "has_blank_line": "\n\n" in text,
        "has_url": "http" in text,
        "has_question": "？" in text or "?" in text,
        "has_emoji": bool(re.search(r'[🚀🤔😅💪🔥⚡🎯😭]', text)),
        "topic": classify_topic(text),
        "colloquial_score": sum(text.count(k) for k in COLLOQUIAL),
        "personal_score": sum(text.count(k) for k in PERSONAL_EXP),
        "chart_terms": sum(1 for k in CHART_TERMS if k in text),
        "emotion_score": sum(text.count(k) for k in EMOTION_MARKERS),
        "uncertainty_score": sum(text.count(k) for k in UNCERTAINTY),
        "has_specific_number": bool(re.search(r'\d{4,}', text)),
        "likes": m["like_count"],
        "retweets": m["retweet_count"],
        "impressions": m.get("impression_count", 0),
        "score": score_tweet(m),
        "hour": created.hour if created else -1,
        "weekday": created.weekday() if created else -1,
    }


def avg(lst, key):
    vals = [x[key] for x in lst]
    return sum(vals) / len(vals) if vals else 0


def pct(lst, key):
    return int(sum(1 for x in lst if x[key]) / len(lst) * 100) if lst else 0


def generate_md(data, total):
    today = datetime.now(JST).strftime("%Y-%m-%d")
    high = data[:max(1, total // 3)]
    low  = data[-(max(1, total // 3)):]

    # テーマ別
    topic_scores = defaultdict(list)
    for d in data:
        topic_scores[d["topic"]].append(d["score"])
    topic_ranking = sorted(topic_scores.items(), key=lambda x: -sum(x[1])/len(x[1]))

    # 時間帯別
    hour_scores = defaultdict(list)
    for d in data:
        if d["hour"] >= 0:
            hour_scores[d["hour"]].append(d["score"])
    top_hours = sorted(hour_scores.items(), key=lambda x: -sum(x[1])/len(x[1]))[:5]

    # 曜日別
    days_jp = ["月", "火", "水", "木", "金", "土", "日"]
    day_scores = defaultdict(list)
    for d in data:
        if d["weekday"] >= 0:
            day_scores[d["weekday"]].append(d["score"])
    top_days = sorted(day_scores.items(), key=lambda x: -sum(x[1])/len(x[1]))[:3]

    # 最重要インサイト: 差が大きい指標を自動抽出
    diff_chars = avg(high, "chars") - avg(low, "chars")
    diff_coll  = avg(high, "colloquial_score") - avg(low, "colloquial_score")
    diff_chart = avg(high, "chart_terms") - avg(low, "chart_terms")
    diff_emot  = avg(high, "emotion_score") - avg(low, "emotion_score")
    diff_pers  = avg(high, "personal_score") - avg(low, "personal_score")
    diff_unc   = avg(high, "uncertainty_score") - avg(low, "uncertainty_score")
    diff_blank = pct(high, "has_blank_line") - pct(low, "has_blank_line")
    diff_emoji = pct(high, "has_emoji") - pct(low, "has_emoji")
    diff_quest = pct(high, "has_question") - pct(low, "has_question")
    diff_num   = pct(high, "has_specific_number") - pct(low, "has_specific_number")

    top_topic = topic_ranking[0][0] if topic_ranking else "BTC"
    top_topic_score = sum(topic_ranking[0][1]) / len(topic_ranking[0][1]) if topic_ranking else 0

    md = f"""# @hajime_cp 投稿インサイト（自動更新）

最終更新: {today}（過去ツイート{total}件分析）

---

## A. テーマ別 平均スコア（重要度順）

"""
    for topic, scores in topic_ranking:
        s = sum(scores) / len(scores)
        n = len(scores)
        bar = "▓" * max(1, int(s / 5))
        md += f"- **{topic}** {bar} {s:.1f}pt（{n}件）\n"

    md += f"""
→ **{top_topic}が最強（平均{top_topic_score:.1f}pt）。毎回まず{top_topic}を調べること**

---

## B. 高エンゲージメント vs 低エンゲージメント 比較

| 指標 | 高（上位1/3） | 低（下位1/3） | 差 |
|---|---|---|---|
| 文字数 | {avg(high, 'chars'):.0f}字 | {avg(low, 'chars'):.0f}字 | {diff_chars:+.0f} |
| 行数 | {avg(high, 'lines'):.1f}行 | {avg(low, 'lines'):.1f}行 | {avg(high,'lines')-avg(low,'lines'):+.1f} |
| 段落数 | {avg(high, 'paragraphs'):.1f} | {avg(low, 'paragraphs'):.1f} | {avg(high,'paragraphs')-avg(low,'paragraphs'):+.1f} |
| 空行あり | {pct(high, 'has_blank_line')}% | {pct(low, 'has_blank_line')}% | {diff_blank:+}% |
| 絵文字あり | {pct(high, 'has_emoji')}% | {pct(low, 'has_emoji')}% | {diff_emoji:+}% |
| 疑問文あり | {pct(high, 'has_question')}% | {pct(low, 'has_question')}% | {diff_quest:+}% |
| 具体数値あり | {pct(high, 'has_specific_number')}% | {pct(low, 'has_specific_number')}% | {diff_num:+}% |
| 口語スコア | {avg(high, 'colloquial_score'):.2f} | {avg(low, 'colloquial_score'):.2f} | {diff_coll:+.2f} |
| チャート用語 | {avg(high, 'chart_terms'):.2f} | {avg(low, 'chart_terms'):.2f} | {diff_chart:+.2f} |
| 感情表現 | {avg(high, 'emotion_score'):.2f} | {avg(low, 'emotion_score'):.2f} | {diff_emot:+.2f} |
| 体験談表現 | {avg(high, 'personal_score'):.2f} | {avg(low, 'personal_score'):.2f} | {diff_pers:+.2f} |
| 不確実表現 | {avg(high, 'uncertainty_score'):.2f} | {avg(low, 'uncertainty_score'):.2f} | {diff_unc:+.2f} |

### ✅ 高エンゲに多いパターン（差がプラスの項目）

"""
    if diff_blank > 10:
        md += f"- **空行で段落を区切る**（高エンゲの{pct(high, 'has_blank_line')}%が使用）\n"
    if diff_emoji > 5:
        md += f"- **絵文字を1〜2個入れる**（高エンゲの{pct(high, 'has_emoji')}%が使用）\n"
    if diff_coll > 0.1:
        md += f"- **口語的表現を積極使用**（「けど」「なんか」「謎に」等、高エンゲ平均{avg(high,'colloquial_score'):.1f}個）\n"
    if diff_chart > 0.1:
        md += f"- **チャート専門用語を含める**（三尊・ネックライン等、高エンゲ平均{avg(high,'chart_terms'):.1f}個）\n"
    if diff_num > 5:
        md += f"- **具体的な数値・価格帯を入れる**（高エンゲの{pct(high,'has_specific_number')}%が含む）\n"
    if diff_quest > 5:
        md += f"- **疑問文を入れる**（「〜では？」「大丈夫か？」等、高エンゲの{pct(high,'has_question')}%が使用）\n"
    if diff_pers > 0.1:
        md += f"- **体験談・時間的文脈を入れる**（「昨日」「今週」等、高エンゲ平均{avg(high,'personal_score'):.1f}個）\n"
    if diff_unc > 0.1:
        md += f"- **不確実表現で断定を避ける**（「かも」「と見ている」等、高エンゲ平均{avg(high,'uncertainty_score'):.1f}個）\n"

    md += """
### ❌ 避けるべきパターン（低エンゲに多い）

- 箇条書き・見出し（◽️■）主体の構成
- 改行なし連続文章
- 断定的・説教的なトーン
- BTCに触れない投稿

---

## C. 最適な投稿スペック

"""
    ideal_chars_low  = max(80, int(avg(high, 'chars') * 0.85))
    ideal_chars_high = min(280, int(avg(high, 'chars') * 1.15))
    ideal_lines_low  = max(3, int(avg(high, 'lines') * 0.8))
    ideal_lines_high = min(10, int(avg(high, 'lines') * 1.2))

    md += f"- **文字数**: {ideal_chars_low}〜{ideal_chars_high}文字\n"
    md += f"- **行数**: {ideal_lines_low}〜{ideal_lines_high}行（空行込み）\n"
    md += f"- **段落**: {avg(high,'paragraphs'):.0f}段落前後\n"
    md += f"- **空行**: 必ず使う（段落を区切る）\n"

    md += """
---

## D. 時間帯別 平均スコア（上位5）

"""
    for h, scores in top_hours:
        n = len(scores)
        s = sum(scores)/n
        md += f"- **{h:02d}時**: 平均{s:.1f}pt（{n}件）\n"

    md += f"""
現在のスケジュール: 朝7時 / 昼13時 / 晩19時

---

## E. 曜日別 平均スコア（上位3）

"""
    for wd, scores in top_days:
        n = len(scores)
        s = sum(scores)/n
        md += f"- **{days_jp[wd]}曜**: 平均{s:.1f}pt（{n}件）\n"

    return md


def main():
    client = get_client()
    me = client.get_me(user_auth=True)
    user_id = me.data.id

    response = client.get_users_tweets(
        id=user_id,
        max_results=100,
        tweet_fields=["public_metrics", "created_at", "text"],
        exclude=["retweets", "replies"],
        user_auth=True,
    )
    if not response.data:
        print("ツイートが見つかりません")
        return

    tweets = response.data
    data = sorted([analyze_tweet(t) for t in tweets], key=lambda x: x["score"], reverse=True)
    md = generate_md(data, len(data))
    INSIGHTS_PATH.write_text(md, encoding="utf-8")
    print(f"insights.md を更新しました（{len(data)}件分析）")


if __name__ == "__main__":
    main()
