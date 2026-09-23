#!/usr/bin/env python3
"""
分析結果をもとに workflow/insights.md を自動更新するスクリプト
analyze_posts.py の後に実行する
"""

import os
import json
import sys
import re
import tweepy
from datetime import datetime, timezone, timedelta
from collections import Counter
from pathlib import Path

JST = timezone(timedelta(hours=9))
ROOT_DIR = Path(__file__).parent.parent
INSIGHTS_PATH = ROOT_DIR / "workflow" / "insights.md"


def get_client():
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )


def count_lines(text):
    return len([l for l in text.strip().split("\n") if l.strip()])


def detect_structure(text):
    if re.search(r"[◽️■]", text):
        return "箇条書き/見出しあり"
    elif text.count("\n\n") >= 2:
        return "段落分け"
    else:
        return "連続文章"


def analyze(tweets):
    data = []
    for t in tweets:
        m = t.public_metrics
        text = t.text
        score = (
            m["like_count"] * 3
            + m["retweet_count"] * 5
            + m["reply_count"] * 2
            + m.get("bookmark_count", 0) * 2
        )
        data.append({
            "id": t.id,
            "created_at": t.created_at.astimezone(JST).strftime("%Y-%m-%d %H:%M JST") if t.created_at else "",
            "text": text,
            "chars": len(text),
            "lines": count_lines(text),
            "structure": detect_structure(text),
            "likes": m["like_count"],
            "retweets": m["retweet_count"],
            "replies": m["reply_count"],
            "bookmarks": m.get("bookmark_count", 0),
            "impressions": m.get("impression_count", 0),
            "score": score,
        })
    return sorted(data, key=lambda x: x["score"], reverse=True)


def avg(lst, key):
    return sum(x[key] for x in lst) / len(lst) if lst else 0


def generate_insights_md(data, total):
    today = datetime.now(JST).strftime("%Y-%m-%d")
    high = data[:max(1, total // 3)]
    low = data[-(max(1, total // 3)):]

    # テーマ分析（BTCキーワード）
    btc_keywords = ["ビットコイン", "BTC", "bitcoin"]
    btc_count = sum(1 for d in high if any(k.lower() in d["text"].lower() for k in btc_keywords))
    btc_pct = int(btc_count / len(high) * 100) if high else 0

    # 構造
    struct_high = Counter(d["structure"] for d in high)
    struct_low = Counter(d["structure"] for d in low)

    # 時間帯
    hour_scores = {}
    for d in data:
        if not d["created_at"]:
            continue
        try:
            hour = int(d["created_at"].split(" ")[1].split(":")[0])
            if hour not in hour_scores:
                hour_scores[hour] = []
            hour_scores[hour].append(d["score"])
        except Exception:
            pass
    hour_avg = {h: sum(v)/len(v) for h, v in hour_scores.items()}
    top_hours = sorted(hour_avg.items(), key=lambda x: x[1], reverse=True)[:5]

    # TOP5
    top5_lines = []
    for i, d in enumerate(data[:5], 1):
        preview = d["text"][:60].replace("\n", " ")
        top5_lines.append(
            f"{i}. スコア{d['score']}（いいね:{d['likes']} RT:{d['retweets']}）"
            f" {d['chars']}文字/{d['lines']}行/{d['structure']}\n"
            f"   「{preview}…」"
        )

    md = f"""# @hajime_cp 投稿インサイト（自動更新）

最終更新: {today}（過去ツイート{total}件分析）

---

## 最重要インサイト

### 1. テーマ：ビットコインが最重要
高エンゲ上位1/3のうち**{btc_pct}%がBTC関連**の投稿。
→ **毎回BTCの動きを最初に調べ、優先的にテーマにすること**

### 2. 文章構造：段落分けが最強
- 高エンゲ: {dict(struct_high)}
- 低エンゲ: {dict(struct_low)}
→ **箇条書き（◽️）や見出し（■）は使わない。空行で段落を区切るスタイルにする**

### 3. 理想的な長さ
- 高エンゲ平均: {avg(high, 'chars'):.0f}文字 / {avg(high, 'lines'):.1f}行
- 目標: **100〜160文字、4〜6行**

### 4. 反応が良い時間帯（上位5）
"""
    for h, s in top_hours:
        n = len(hour_scores[h])
        md += f"- {h:02d}時: 平均スコア{s:.1f}（{n}件）\n"

    md += f"""
現在のスケジュール: 朝7時 / 昼13時 / 晩19時

---

## TOP5投稿

"""
    md += "\n\n".join(top5_lines)

    md += """

---

## 避けるべきパターン
- ◽️箇条書き・■見出し主体の構成（低エンゲに多い）
- BTCに触れない投稿（FX・ゴールドのみ）
- 改行なしの連続文章
"""
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
        print("ツイートが見つかりませんでした")
        return

    tweets = response.data
    data = analyze(tweets)
    md = generate_insights_md(data, len(tweets))
    INSIGHTS_PATH.write_text(md, encoding="utf-8")
    print(f"insights.md を更新しました（{len(tweets)}件分析）")


if __name__ == "__main__":
    main()
