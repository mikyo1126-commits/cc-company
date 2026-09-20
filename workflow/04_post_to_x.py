#!/usr/bin/env python3
"""
Step 4: X API 投稿スクリプト
- marketing/content-plan/drafts/DATE/SLOT/draft.md の内容を X に投稿する
- 環境変数: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET

Usage:
    python3 workflow/04_post_to_x.py --date 2026-09-19 --slot morning
"""

import argparse
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DRAFTS_DIR = ROOT_DIR / "marketing" / "content-plan" / "drafts"


def load_draft(date_str: str, slot: str) -> str:
    draft_path = DRAFTS_DIR / date_str / slot / "draft.md"
    if not draft_path.exists():
        print(f"ERROR: Draft not found: {draft_path}", file=sys.stderr)
        sys.exit(1)
    return draft_path.read_text(encoding="utf-8").strip()


def post_tweet(text: str, credentials: dict) -> dict:
    import tweepy
    client = tweepy.Client(
        consumer_key=credentials["api_key"],
        consumer_secret=credentials["api_secret"],
        access_token=credentials["access_token"],
        access_token_secret=credentials["access_token_secret"],
    )
    response = client.create_tweet(text=text)
    return {"data": {"id": response.data["id"]}}


def main():
    parser = argparse.ArgumentParser(description="draft.md を X に投稿する")
    parser.add_argument("--date", required=True, help="投稿日付 YYYY-MM-DD")
    parser.add_argument("--slot", required=True, choices=["morning", "noon", "evening"])
    args = parser.parse_args()

    credentials = {
        "api_key": os.environ.get("TWITTER_API_KEY", ""),
        "api_secret": os.environ.get("TWITTER_API_SECRET", ""),
        "access_token": os.environ.get("TWITTER_ACCESS_TOKEN", ""),
        "access_token_secret": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", ""),
    }

    missing = [k for k, v in credentials.items() if not v]
    if missing:
        print(f"ERROR: Missing environment variables: {missing}", file=sys.stderr)
        sys.exit(1)

    text = load_draft(args.date, args.slot)
    print(f"Posting to X ({args.date}/{args.slot}):")
    print("-" * 40)
    print(text)
    print("-" * 40)

    result = post_tweet(text, credentials)
    tweet_id = result.get("data", {}).get("id", "unknown")
    print(f"Posted successfully. Tweet ID: {tweet_id}")
    print(f"URL: https://x.com/hajime_cp/status/{tweet_id}")


if __name__ == "__main__":
    main()
