#!/usr/bin/env python3
"""
@hajime_cp の過去ツイートをX APIから取得し、
エンゲージメントが高い投稿の特徴を分析するスクリプト

Usage:
    python3 workflow/analyze_posts.py
"""

import os
import json
import sys
import re
import tweepy
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def get_client():
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )


def fetch_tweets(client, max_results=100):
    me = client.get_me(user_auth=True)
    user_id = me.data.id
    print(f"User ID: {user_id}", file=sys.stderr)

    response = client.get_users_tweets(
        id=user_id,
        max_results=max_results,
        tweet_fields=["public_metrics", "created_at", "text"],
        exclude=["retweets", "replies"],
        user_auth=True,
    )

    if not response.data:
        print("ツイートが見つかりませんでした", file=sys.stderr)
        return []

    return response.data


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

        # エンゲージメントスコア（いいね×3 + RT×5 + 返信×2 + ブックマーク×2）
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


def print_report(data):
    print("=" * 60)
    print(f"@hajime_cp 投稿分析レポート（{len(data)}件）")
    print("=" * 60)

    # TOP10
    print("\n▼ エンゲージメントTOP10\n")
    for i, d in enumerate(data[:10], 1):
        print(f"#{i} スコア:{d['score']} (いいね:{d['likes']} RT:{d['retweets']} 返信:{d['replies']} BM:{d['bookmarks']})")
        print(f"   {d['created_at']} / {d['chars']}文字 / {d['lines']}行 / {d['structure']}")
        preview = d["text"][:80].replace("\n", " ")
        print(f"   「{preview}…」")
        print()

    # 統計分析
    high = data[:max(1, len(data) // 3)]   # 上位1/3
    low = data[-(max(1, len(data) // 3)):]  # 下位1/3

    def avg(lst, key):
        return sum(x[key] for x in lst) / len(lst) if lst else 0

    print("\n▼ 高エンゲージメント vs 低エンゲージメント 比較\n")
    print(f"{'指標':<15} {'高(上位1/3)':<15} {'低(下位1/3)':<15}")
    print("-" * 45)
    print(f"{'文字数':<15} {avg(high, 'chars'):<15.0f} {avg(low, 'chars'):<15.0f}")
    print(f"{'行数':<15} {avg(high, 'lines'):<15.1f} {avg(low, 'lines'):<15.1f}")
    print(f"{'いいね':<15} {avg(high, 'likes'):<15.1f} {avg(low, 'likes'):<15.1f}")
    print(f"{'RT':<15} {avg(high, 'retweets'):<15.1f} {avg(low, 'retweets'):<15.1f}")
    print(f"{'インプレ':<15} {avg(high, 'impressions'):<15.0f} {avg(low, 'impressions'):<15.0f}")

    # 構造の分布
    from collections import Counter
    struct_high = Counter(d["structure"] for d in high)
    struct_low = Counter(d["structure"] for d in low)
    print(f"\n▼ 文章構造\n  高: {dict(struct_high)}\n  低: {dict(struct_low)}")

    # 時間帯
    print("\n▼ 時間帯別平均スコア\n")
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
    for h in sorted(hour_scores):
        scores = hour_scores[h]
        print(f"  {h:02d}時: 平均スコア {sum(scores)/len(scores):.1f}（{len(scores)}件）")

    # JSON出力（後続処理用）
    with open("/tmp/post_analysis.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n→ 詳細データ: /tmp/post_analysis.json")


def main():
    client = get_client()
    print("ツイート取得中...", file=sys.stderr)
    tweets = fetch_tweets(client, max_results=100)
    print(f"{len(tweets)}件取得", file=sys.stderr)
    data = analyze(tweets)
    print_report(data)


if __name__ == "__main__":
    main()
