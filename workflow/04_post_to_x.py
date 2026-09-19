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
import json
import hmac
import hashlib
import base64
import time
import random
import string
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT_DIR = Path(__file__).parent.parent
DRAFTS_DIR = ROOT_DIR / "marketing" / "content-plan" / "drafts"
JST = timezone(timedelta(hours=9))

X_API_URL = "https://api.twitter.com/2/tweets"


def load_draft(date_str: str, slot: str) -> str:
    draft_path = DRAFTS_DIR / date_str / slot / "draft.md"
    if not draft_path.exists():
        print(f"ERROR: Draft not found: {draft_path}", file=sys.stderr)
        sys.exit(1)
    return draft_path.read_text(encoding="utf-8").strip()


def oauth1_header(method: str, url: str, params: dict, credentials: dict) -> str:
    nonce = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    timestamp = str(int(time.time()))

    oauth_params = {
        "oauth_consumer_key": credentials["api_key"],
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp,
        "oauth_token": credentials["access_token"],
        "oauth_version": "1.0",
    }

    all_params = {**params, **oauth_params}
    sorted_params = "&".join(
        f"{quote(k, safe='')}={quote(v, safe='')}"
        for k, v in sorted(all_params.items())
    )

    base_string = "&".join([
        method.upper(),
        quote(url, safe=""),
        quote(sorted_params, safe=""),
    ])

    signing_key = "&".join([
        quote(credentials["api_secret"], safe=""),
        quote(credentials["access_token_secret"], safe=""),
    ])

    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()

    oauth_params["oauth_signature"] = signature
    header_value = "OAuth " + ", ".join(
        f'{quote(k, safe="")}="{quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return header_value


def post_tweet(text: str, credentials: dict) -> dict:
    body = json.dumps({"text": text}).encode("utf-8")
    auth_header = oauth1_header("POST", X_API_URL, {}, credentials)

    req = Request(
        X_API_URL,
        data=body,
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"HTTP {e.code}: {error_body}", file=sys.stderr)
        raise


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
