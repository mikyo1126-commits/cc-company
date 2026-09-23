#!/usr/bin/env python3
"""
@hajime_cp の過去ツイートを多角的に分析するスクリプト

分析項目:
  基本指標  : 文字数・行数・段落数・文章構造
  内容分類  : テーマ（BTC/Gold/FX/マクロ/マインド/その他）
  言語特徴  : 口語度・絵文字・疑問文・引用符・省略記号
  個人性    : 体験談・一人称使用・感情表現
  要素      : URL・チャート用語・具体的数値
  時間帯    : 曜日・時刻
"""

import os
import re
import sys
import json
import tweepy
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from pathlib import Path

JST = timezone(timedelta(hours=9))
ROOT_DIR = Path(__file__).parent.parent

# ----- 分類ルール -----

BTC_KEYWORDS   = ["ビットコイン", "BTC", "bitcoin", "btc"]
GOLD_KEYWORDS  = ["ゴールド", "金", "gold", "XAU"]
FX_KEYWORDS    = ["ドル円", "ユーロ", "ポンド", "為替", "FX", "fx", "ドル"]
MACRO_KEYWORDS = ["FOMC", "fomc", "日銀", "FRB", "CPI", "雇用統計", "GDP", "利上げ", "利下げ"]
MIND_KEYWORDS  = ["心理", "メンタル", "感情", "バイアス", "失敗", "経験", "学び", "思う", "感じ", "怖", "欲"]

CHART_TERMS    = ["三尊", "ネックライン", "押し目", "戻り目", "移動平均", "週足", "日足", "月足",
                  "ピンバー", "ブレイク", "サポート", "レジスタンス", "トレンド転換", "ダイバージェンス",
                  "エリオット", "フィボナッチ", "ボリンジャー", "ゴールデンクロス", "デッドクロス"]

COLLOQUIAL     = ["けど", "だけど", "でも", "なんか", "かも", "っぽい", "謎に", "なんで",
                  "ちゃんと", "やっぱ", "やっぱり", "ぶっちゃけ", "正直", "わりと", "割と",
                  "ちょっと", "どっち", "どうせ", "とか", "みたいな", "じゃん", "じゃないか",
                  "よな", "よね", "よ", "ね", "かな", "かね", "し", "まじ", "マジ"]

PERSONAL_EXP   = ["昨日", "先週", "先月", "今日", "今週", "今朝", "今夜", "さっき",
                  "経験", "失敗", "やらかし", "やってしまっ", "食あたり", "体調", "忘れられない"]

EMOTION_MARKERS = ["🚀", "🤔", "😅", "💪", "🔥", "⚡", "🎯", "😭", "！", "!"]

UNCERTAINTY    = ["かも", "かもしれ", "っぽい", "気がする", "思う", "じゃないか", "可能性",
                  "〜かな", "〜かね", "でしょう", "と見ている", "ではないか"]


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


def count_colloquial(text):
    return sum(text.count(k) for k in COLLOQUIAL)


def count_personal(text):
    return sum(text.count(k) for k in PERSONAL_EXP)


def count_chart_terms(text):
    return sum(1 for k in CHART_TERMS if k in text)


def count_emotions(text):
    return sum(text.count(k) for k in EMOTION_MARKERS)


def count_uncertainty(text):
    return sum(text.count(k) for k in UNCERTAINTY)


def has_specific_number(text):
    return bool(re.search(r'\d{4,}', text))  # 4桁以上の数値


def analyze_tweet(t):
    m = t.public_metrics
    text = t.text
    lines = [l for l in text.strip().split("\n") if l.strip()]
    paragraphs = text.strip().split("\n\n")
    score = (
        m["like_count"] * 3
        + m["retweet_count"] * 5
        + m["reply_count"] * 2
        + m.get("bookmark_count", 0) * 2
    )

    created = t.created_at.astimezone(JST) if t.created_at else None

    return {
        "id": t.id,
        "created_at": created.strftime("%Y-%m-%d %H:%M JST") if created else "",
        "weekday": created.weekday() if created else -1,  # 0=月 6=日
        "hour": created.hour if created else -1,
        "text": text,
        # 基本
        "chars": len(text),
        "lines": len(lines),
        "paragraphs": max(1, len([p for p in paragraphs if p.strip()])),
        "has_blank_line": "\n\n" in text,
        "has_url": "http" in text,
        "has_question": "？" in text or "?" in text,
        "has_emoji": bool(re.search(r'[\U00010000-\U0010ffff]|[🚀🤔😅💪🔥⚡🎯😭]', text)),
        # 分類
        "topic": classify_topic(text),
        # 言語特徴
        "colloquial_score": count_colloquial(text),
        "personal_score": count_personal(text),
        "chart_terms": count_chart_terms(text),
        "emotion_score": count_emotions(text),
        "uncertainty_score": count_uncertainty(text),
        "has_specific_number": has_specific_number(text),
        "first_word": lines[0][:10] if lines else "",
        # エンゲージメント
        "likes": m["like_count"],
        "retweets": m["retweet_count"],
        "replies": m["reply_count"],
        "bookmarks": m.get("bookmark_count", 0),
        "impressions": m.get("impression_count", 0),
        "score": score,
    }


def avg(lst, key):
    vals = [x[key] for x in lst if isinstance(x[key], (int, float))]
    return sum(vals) / len(vals) if vals else 0


def pct(lst, condition):
    return int(sum(1 for x in lst if condition(x)) / len(lst) * 100) if lst else 0


def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_report(data, total):
    print_section(f"@hajime_cp 投稿分析レポート（{total}件）")

    high = data[:max(1, total // 3)]
    low  = data[-(max(1, total // 3)):]

    # ── TOP10 ──
    print_section("TOP10 エンゲージメント")
    for i, d in enumerate(data[:10], 1):
        preview = d["text"][:70].replace("\n", " ")
        print(f"\n#{i}  スコア:{d['score']}  いいね:{d['likes']} RT:{d['retweets']} "
              f"返信:{d['replies']} BM:{d['bookmarks']} インプレ:{d['impressions']}")
        print(f"    {d['created_at']} / {d['chars']}文字/{d['lines']}行/{d['paragraphs']}段落 / {d['topic']}")
        print(f"    「{preview}…」")

    # ── 基本指標 比較 ──
    print_section("基本指標：高エンゲ vs 低エンゲ")
    rows = [
        ("文字数",       lambda d: d["chars"]),
        ("行数",         lambda d: d["lines"]),
        ("段落数",       lambda d: d["paragraphs"]),
        ("いいね",       lambda d: d["likes"]),
        ("インプレ",     lambda d: d["impressions"]),
    ]
    print(f"\n{'指標':<12} {'高(上位1/3)':<14} {'低(下位1/3)':<14}")
    print("-" * 40)
    for label, fn in rows:
        h_val = sum(fn(d) for d in high) / len(high)
        l_val = sum(fn(d) for d in low) / len(low)
        print(f"{label:<12} {h_val:<14.1f} {l_val:<14.1f}")

    # ── テーマ別 ──
    print_section("テーマ別 平均スコア")
    topic_data = defaultdict(list)
    for d in data:
        topic_data[d["topic"]].append(d["score"])
    for topic, scores in sorted(topic_data.items(), key=lambda x: -sum(x[1])/len(x[1])):
        print(f"  {topic:<10} 平均スコア:{sum(scores)/len(scores):.1f}  件数:{len(scores)}")

    # ── 言語特徴 比較 ──
    print_section("言語特徴：高エンゲ vs 低エンゲ")
    lang_rows = [
        ("口語スコア",   lambda d: d["colloquial_score"]),
        ("体験談スコア", lambda d: d["personal_score"]),
        ("チャート用語", lambda d: d["chart_terms"]),
        ("感情表現",     lambda d: d["emotion_score"]),
        ("不確実表現",   lambda d: d["uncertainty_score"]),
    ]
    print(f"\n{'指標':<14} {'高(上位1/3)':<14} {'低(下位1/3)':<14}")
    print("-" * 42)
    for label, fn in lang_rows:
        h_val = sum(fn(d) for d in high) / len(high)
        l_val = sum(fn(d) for d in low) / len(low)
        print(f"{label:<14} {h_val:<14.2f} {l_val:<14.2f}")

    bool_rows = [
        ("空行あり%",   lambda d: d["has_blank_line"]),
        ("疑問文あり%", lambda d: d["has_question"]),
        ("絵文字あり%", lambda d: d["has_emoji"]),
        ("URL含む%",    lambda d: d["has_url"]),
        ("具体数値%",   lambda d: d["has_specific_number"]),
    ]
    print(f"\n{'フラグ指標':<14} {'高(上位1/3)%':<14} {'低(下位1/3)%':<14}")
    print("-" * 42)
    for label, fn in bool_rows:
        h_pct = pct(high, fn)
        l_pct = pct(low, fn)
        print(f"{label:<14} {h_pct:<14} {l_pct:<14}")

    # ── 時間帯 ──
    print_section("時間帯別 平均スコア")
    hour_data = defaultdict(list)
    for d in data:
        if d["hour"] >= 0:
            hour_data[d["hour"]].append(d["score"])
    for h in sorted(hour_data):
        scores = hour_data[h]
        bar = "█" * int(sum(scores)/len(scores) / 5)
        print(f"  {h:02d}時  {bar:<15} {sum(scores)/len(scores):.1f}（{len(scores)}件）")

    # ── 曜日 ──
    print_section("曜日別 平均スコア")
    days = ["月", "火", "水", "木", "金", "土", "日"]
    day_data = defaultdict(list)
    for d in data:
        if d["weekday"] >= 0:
            day_data[d["weekday"]].append(d["score"])
    for wd in range(7):
        if wd in day_data:
            scores = day_data[wd]
            print(f"  {days[wd]}曜  平均スコア:{sum(scores)/len(scores):.1f}（{len(scores)}件）")

    # JSON保存
    out_path = "/tmp/post_analysis.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n→ 詳細データ: {out_path}")

    return {
        "total": total,
        "high": high,
        "low": low,
        "topic_data": {k: {"avg": sum(v)/len(v), "count": len(v)} for k, v in topic_data.items()},
        "hour_data": {str(h): {"avg": sum(v)/len(v), "count": len(v)} for h, v in hour_data.items()},
        "day_data": {str(d): {"avg": sum(v)/len(v), "count": len(v)} for d, v in day_data.items()},
    }


def main():
    client = get_client()
    me = client.get_me(user_auth=True)
    user_id = me.data.id
    print(f"User ID: {user_id}", file=sys.stderr)

    response = client.get_users_tweets(
        id=user_id,
        max_results=100,
        tweet_fields=["public_metrics", "created_at", "text"],
        exclude=["retweets", "replies"],
        user_auth=True,
    )
    if not response.data:
        print("ツイートが見つかりませんでした")
        return

    tweets = response.data
    print(f"{len(tweets)}件取得", file=sys.stderr)

    data = sorted([analyze_tweet(t) for t in tweets], key=lambda x: x["score"], reverse=True)
    print_report(data, len(data))


if __name__ == "__main__":
    main()
