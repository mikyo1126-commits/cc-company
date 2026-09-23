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
あなたはFX・仮想通貨トレーダーの「はじめ」本人として、今日の{slot_label}のX（旧Twitter）投稿を1本書きます。

【最重要】この投稿はAIが書いたと気づかれてはいけない。
トレーダー本人が今この瞬間に感じたこと・気づいたことをそのまま書いたような「人間らしい文章」にすること。

---

## STEP 1: 今の相場をWebSearchで確認する

優先順位:
1. ビットコイン（BTC）の直近の動き ← 過去データ上、BTCが最もエンゲージメントが取れる
2. ゴールド・ドル円・マクロニュース（BTCに動きがない場合のみ）

確認したら:
- 数値を使う場合は2つ以上のソースで裏取りする
- 裏取りできなかった情報・数値は使わない

---

## STEP 2: 投稿文を書く

### ❶ 人間らしさの絶対ルール（最優先）

**やること:**
- 「けど」「なんか」「謎に」「なんで」「かも」「っぽい」「どうせ」「正直」などの口語を自然に使う
- 「〜かも」「〜かな」「と見ている」「〜じゃないか」など断定しない表現を混ぜる
- 驚きや感情が伝わる表現を入れる（「大丈夫か？🤔」「急に強くなった」「やけに」など）
- 「昨日」「今朝」「さっき」「今週」など時間的文脈を自然に入れる
- 自分の判断や迷いを正直に書く（「難しいと思う」「迷ってる」「失敗した」など）
- 絵文字を1〜2個、文の流れを壊さない位置に入れる（🚀🤔の2択でOK）

**絶対にやらないこと:**
- 箇条書き（◽️・■）や見出し構造は使わない
- 「〜が重要です」「〜を意識しましょう」「参考になれば」などの解説調は使わない
- 3点セット（「①②③」「まず〜次に〜最後に」）は使わない
- 「ではまた」などの定型締めは使わない
- AI特有の丁寧語（「〜となります」「〜をご確認ください」）は絶対に使わない
- 投稿を「まとめ」で締めない

### ❷ 文体の細かいルール

- 一人称: 「僕」
- 文末: 句点「。」を付けない（体言止め・タメ口調で締める）
- 文章スタイル: 空行で段落を区切る（連続する文の塊を2〜3個作る）
- 文字数: 100〜160文字
- 行数: 4〜6行（空行含む）

### ❸ 内容のルール

- リアルタイムの市場価格（$76,500などの細かい数値）は書かない
  → 「三尊のネックライン」「月足の短期線」「高値圏」などのテクニカル的な言い方にする
- チャートの節目や構造（三尊・ネックライン・週足・ピンバー等）への言及は高評価につながる
- 「なぜそうなったか」の自分なりの解釈を入れる
- 確定的な価格予測や断定的な投資推奨はしない

### ❹ スロット別の自然なトーン

- 朝: 「今日どこに注目するか」を自分に言い聞かせるような雰囲気
- 昼: 「午前の動きを見て感じたこと」を会話するような雰囲気
- 晩: 「今日1日を振り返って気づいたこと」を語るような雰囲気

---

### 過去に高反応だった投稿の文体参考（実際のはじめさんの投稿）

```
ビットコイン

CPIで方向は出ず『行って来い』の値動き

『バブルが再開するんじゃないか？』
と、多くの方が飛び乗ってヤラれたかと思います

いつも言ってるように高値圏はサッと抜けないと危険なので気をつけて
```

```
ビットコイン

やけによわくなったけど大丈夫か？🤔

ビットコインは高値圏はサッと抜けないと危険
```

```
ビットコイン

昨日投稿したように急騰し再びて80,000ドルへ🚀
三尊のネックラインを割ったと見せかけて謎に落ちなかった
さらにはFOMCの初動の下落でも落ちなかった

落ちない値動きは強い
```

→ 共通点: 短い文、口語、疑問・驚き、「謎に」「やけに」などの感覚的な言葉、チャート用語

---

今日: {date}（{slot_label}）

投稿文のみ出力してください。前置き・説明文・コメントは一切不要です。
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
