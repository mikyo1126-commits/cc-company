#!/usr/bin/env python3
"""
シンプル自動投稿スクリプト
1. Claude CLI (WebSearch付き) で投稿文を生成
2. X API で即時投稿

Usage:
    python3 workflow/auto_post.py morning
    python3 workflow/auto_post.py noon
    python3 workflow/auto_post.py evening
"""

import os
import re
import sys
import subprocess
import tweepy
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))
SLOT_LABELS = {"morning": "朝", "noon": "昼", "evening": "晩"}
ROOT_DIR = Path(__file__).parent.parent
INSIGHTS_PATH = ROOT_DIR / "workflow" / "insights.md"

PROMPT = """\
あなたは @hajime_cp（FX・ゴールド・仮想通貨トレーダー）のX運用エージェントです。
今日の{slot_label}投稿を1本生成してください。

---

## ステップ1: 直近ニュースをWebSearchで調べる

以下の優先順位で調べてください。

**優先1（最重要）: ビットコイン**
BTCの直近2〜3時間の値動き、注目される価格帯、テクニカルの節目、マーケットの反応。
過去の分析で、BTCに関する投稿がエンゲージメントTOP10を独占している。

**優先2: ゴールド・FX・マクロ**
BTCで書けるネタがない場合にのみ選ぶ。

数値を使う場合は**独立した2つ以上のソースで裏取りすること**。
裏取りできなかった数値・情報は使わない。

---

## ステップ2: 投稿を生成する

### 文体ルール（必須）
- 一人称は「僕」
- 文末に句点「。」を付けない
- **段落分けスタイルで書く**（空行で段落を区切る。箇条書き・見出しは使わない）
- 「ではまた明日」などの定型締めは禁止
- 思考の流れが自然に続く文章にする

### 構成の参考（高エンゲージメント投稿のパターン）
1. 「ビットコイン」等で始まるトピック提示
2. 直近の値動き・状況を端的に描写
3. 「なぜそうなったか」「何が起きているか」の解説（独自の切り口）
4. 「これからどう見るか」「今日の判断ポイント」

### 目標仕様
- **文字数: 100〜160文字**
- **行数: 4〜6行**（段落間の空行も含む）

### 内容ルール
- リアルタイム市場価格（$5,602など）は書かない
  → 代わりに「月足の短期線まで急騰」「三尊のネックラインを試す」などの表現を使う
- FOMCの政策金利など公式決定値はOK（リアルタイム変動しない）
- 確定的な価格予測・断定的な投資推奨はしない
- @hajime_cp 独自の切り口・経験・見方を通した内容にする
- 宗教・政治・他トレーダーへの批判はNG

### スロット別の傾向（参考）
- 朝: 今日意識すべき値動きの焦点・トレードの準備
- 昼: 午前の動きの解説・心理面・チャートの読み方
- 晩: 1日の振り返り・明日の注目点

### 本日のコンテキスト
- 日時: {date}（{slot_label}）

---

**投稿文のみ出力してください。前置き・説明・コメントは一切不要です。**
"""


def build_prompt(date_str: str, slot: str) -> str:
    slot_label = SLOT_LABELS.get(slot, "朝")
    base = PROMPT.format(date=date_str, slot=slot, slot_label=slot_label)
    if INSIGHTS_PATH.exists():
        insights = INSIGHTS_PATH.read_text(encoding="utf-8")
        base += f"\n\n---\n\n## 過去分析インサイト（毎週更新）\n\n{insights}"
    return base


def generate_post(date_str: str, slot: str) -> str:
    prompt = build_prompt(date_str, slot)

    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions", "-"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
    )

    if result.returncode != 0:
        print(f"ERROR: claude CLI failed\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)

    text = result.stdout.strip()

    # コードフェンスで囲まれていたら中身だけ抽出
    m = re.search(r"```[^\n]*\n(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()

    return text


def post_to_x(text: str) -> str:
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )
    try:
        response = client.create_tweet(text=text)
        return str(response.data["id"])
    except tweepy.errors.Unauthorized as e:
        resp_text = e.response.text if hasattr(e, "response") else str(e)
        print(f"401 Unauthorized: {resp_text}", file=sys.stderr)
        raise
    except tweepy.errors.Forbidden as e:
        resp_text = e.response.text if hasattr(e, "response") else str(e)
        print(f"403 Forbidden: {resp_text}", file=sys.stderr)
        raise


def main():
    slot = sys.argv[1] if len(sys.argv) > 1 else "morning"
    if slot not in SLOT_LABELS:
        print(f"ERROR: slot must be morning/noon/evening, got: {slot}", file=sys.stderr)
        sys.exit(1)

    date_str = datetime.now(JST).strftime("%Y-%m-%d")
    slot_label = SLOT_LABELS[slot]

    print(f"[{date_str} {slot_label}] 投稿生成中...")
    text = generate_post(date_str, slot)

    print(f"\n--- 生成された投稿 ({len(text)}文字) ---")
    print(text)
    print("-" * 40)

    if not os.environ.get("TWITTER_API_KEY"):
        print("TWITTER_API_KEY未設定のため投稿をスキップ（ドライラン）")
        return

    tweet_id = post_to_x(text)
    print(f"\n投稿完了: https://x.com/hajime_cp/status/{tweet_id}")


if __name__ == "__main__":
    main()
