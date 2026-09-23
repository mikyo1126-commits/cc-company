#!/usr/bin/env python3
"""
自動投稿スクリプト（生成→検証→修正ループ→投稿）

フロー:
  1. 投稿文を生成（WebSearch付きClaude）
  2. 全ての事実主張を検証（WebSearchで裏取り）
  3. 問題があれば修正し再検証（最大3回）
  4. 検証パスのみ投稿、失敗なら中断

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
MAX_VERIFY_ATTEMPTS = 3

# ──────────────────────────────────────────
# プロンプト定義
# ──────────────────────────────────────────

GENERATE_PROMPT = """\
あなたはFX・仮想通貨トレーダーの「はじめ」本人として、今日の{slot_label}のX（旧Twitter）投稿を1本書きます。

【最重要】この投稿はAIが書いたと気づかれてはいけない。
トレーダー本人が今この瞬間に感じたこと・気づいたことをそのまま書いたような「人間らしい文章」にすること。

---

## STEP 1: 今の相場をWebSearchで確認する

優先順位:
1. ビットコイン（BTC）の直近の動き ← 過去データ上、BTCが最もエンゲージメントが取れる
2. ゴールド・ドル円・マクロニュース（BTCに動きがない場合のみ）

確認したら:
- **数値を使う場合は必ず2つ以上の独立したソースで裏取りする**
- 裏取りできなかった情報・数値は絶対に使わない
- 「〜に向かっているかも」「〜を試す可能性」など方向感は書いてよいが、断定はしない

---

## STEP 2: 投稿文を書く

### ❶ 人間らしさの絶対ルール（最優先）

**やること:**
- 「けど」「なんか」「謎に」「なんで」「かも」「っぽい」「どうせ」「正直」などの口語を自然に使う
- 「〜かも」「〜かな」「と見ている」「〜じゃないか」など断定しない表現を混ぜる
- 驚きや感情が伝わる表現を入れる（「大丈夫か？🤔」「急に強くなった」「やけに」など）
- 「昨日」「今朝」「さっき」「今週」など時間的文脈を自然に入れる
- 自分の判断や迷いを正直に書く（「難しいと思う」「迷ってる」など）
- 絵文字を1〜2個、文の流れを壊さない位置に入れる（🚀🤔を推奨）

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
- 文章スタイル: 空行で段落を区切る
- 文字数: 100〜160文字
- 行数: 4〜6行（空行含む）

### ❸ 内容のルール

- リアルタイムの市場価格（$76,500などの細かい数値）は書かない
  → 「三尊のネックライン」「月足の短期線」「高値圏」などのテクニカル的な表現にする
- チャートの節目・構造（三尊・ネックライン・週足・ピンバー等）への言及は高評価につながる
- 「なぜそうなったか」の自分なりの解釈を入れる
- 方向感（「上を試しそう」「下に向かうかも」）はOK。断定はNG

### ❹ スロット別の自然なトーン

- 朝: 「今日どこに注目するか」を自分に言い聞かせるような雰囲気
- 昼: 「午前の動きを見て感じたこと」を会話するような雰囲気
- 晩: 「今日1日を振り返って気づいたこと」を語るような雰囲気

---

### 過去に高反応だった投稿の文体参考（実際のはじめさんの投稿）

例1:
ビットコイン

CPIで方向は出ず『行って来い』の値動き

『バブルが再開するんじゃないか？』
と、多くの方が飛び乗ってヤラれたかと思います

いつも言ってるように高値圏はサッと抜けないと危険なので気をつけて

例2:
ビットコイン

やけによわくなったけど大丈夫か？🤔

ビットコインは高値圏はサッと抜けないと危険

例3:
ビットコイン

昨日投稿したように急騰し再びて80,000ドルへ🚀
三尊のネックラインを割ったと見せかけて謎に落ちなかった
さらにはFOMCの初動の下落でも落ちなかった

落ちない値動きは強い

→ 共通点: 短い文、口語、疑問・驚き、「謎に」「やけに」などの感覚的な言葉、チャート用語

---

今日: {date}（{slot_label}）

投稿文のみ出力してください。前置き・説明文・コメントは一切不要です。
"""

VERIFY_PROMPT = """\
以下の投稿文に含まれる「事実主張」を検証してください。

---
投稿文:
{draft}
---

## 検証手順

1. 投稿文から「事実主張」をすべて列挙する
   - 事実主張 = 価格・変動率・日時・指標結果・発言の引用など、正誤が存在する情報
   - 「かも」「と思う」「っぽい」など意見・予測・感想は対象外
   - チャートパターンへの言及（「三尊を形成中」等）は、現在の相場状況と照らして確認する

2. WebSearchで各主張を独立した2つ以上のソースで裏取りする
   - 数値は複数ソースで一致することを確認する
   - 1つしか見つからない情報は「要確認」とする

3. 結果を以下のフォーマットで出力する:

## 検証結果

| 主張 | 判定 | 根拠 |
|---|---|---|
| （主張内容） | ✅ 確認済み | （ソース名・内容） |
| （主張内容） | ❌ 誤り | （正しい情報） |
| （主張内容） | ⚠️ 要確認 | （確認できなかった理由） |

## 総合判定
- 全項目✅: PASS
- ❌または⚠️が1件でもある: FAIL（理由を明記）

## スタイルチェック
- 断定的な価格予測が含まれていないか
- 「〜になる」「〜は確実」などの断定表現がないか
- 投資推奨（「買い推奨」「売れ」等）が含まれていないか
"""

FIX_PROMPT = """\
以下の投稿文を、検証ログの指摘に従って修正してください。

---
現在の投稿文:
{draft}

---
検証ログ:
{verify_log}
---

## 修正ルール

- ❌（誤り）と⚠️（要確認）の項目のみ修正する
- 修正方法:
  - 数値が間違っている → 正しい数値に直す（または数値を使わない表現に変える）
  - 確認できない情報 → その部分を削除するか、チャートパターン的な表現に置き換える
  - 断定的すぎる表現 → 「〜かも」「〜を試す可能性」などに柔らかくする

- ✅（確認済み）の部分は変えない
- 文体・人間らしさ・長さを維持する

修正後の投稿文のみ出力してください。説明・コメントは不要です。
"""


# ──────────────────────────────────────────
# Claude CLI 呼び出し
# ──────────────────────────────────────────

def call_claude(prompt: str, timeout: int = 300) -> str:
    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions", "-"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    if result.returncode != 0:
        print(f"ERROR: claude CLI failed\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)
    text = result.stdout.strip()
    m = re.search(r"```[^\n]*\n(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else text


def build_generate_prompt(date_str: str, slot: str) -> str:
    slot_label = SLOT_LABELS[slot]
    base = GENERATE_PROMPT.format(date=date_str, slot=slot, slot_label=slot_label)
    if INSIGHTS_PATH.exists():
        insights = INSIGHTS_PATH.read_text(encoding="utf-8")
        base += f"\n\n---\n\n## 過去分析インサイト（毎週更新）\n\n{insights}"
    return base


def is_verified(verify_log: str) -> bool:
    """検証ログにFAILまたは❌/⚠️があればFalse"""
    if "FAIL" in verify_log:
        return False
    lines = verify_log.split("\n")
    for line in lines:
        if re.search(r"^[\|\s]*[❌⚠️]", line):
            return False
    return True


# ──────────────────────────────────────────
# メインフロー
# ──────────────────────────────────────────

def generate_and_verify(date_str: str, slot: str) -> str:
    slot_label = SLOT_LABELS[slot]

    print(f"\n[STEP 1] 投稿生成中 ({slot_label})...")
    draft = call_claude(build_generate_prompt(date_str, slot))
    print(f"\n--- 初回生成 ({len(draft)}文字) ---\n{draft}\n{'-'*40}")

    for attempt in range(1, MAX_VERIFY_ATTEMPTS + 1):
        print(f"\n[STEP 2] 検証中（{attempt}/{MAX_VERIFY_ATTEMPTS}回目）...")
        verify_log = call_claude(VERIFY_PROMPT.format(draft=draft))
        print(f"\n--- 検証ログ ---\n{verify_log}\n{'-'*40}")

        if is_verified(verify_log):
            print(f"\n✅ 検証パス（{attempt}回目で完了）")
            return draft

        print(f"\n⚠️ 検証で問題を検出（attempt {attempt}）")

        if attempt < MAX_VERIFY_ATTEMPTS:
            print(f"\n[STEP 3] 修正中...")
            draft = call_claude(FIX_PROMPT.format(draft=draft, verify_log=verify_log))
            print(f"\n--- 修正後 ({len(draft)}文字) ---\n{draft}\n{'-'*40}")

    # 3回試して通らなかった
    print(f"\n❌ {MAX_VERIFY_ATTEMPTS}回の検証ループで問題が解消されませんでした", file=sys.stderr)
    print("投稿をブロックします。検証ログを確認してください:", file=sys.stderr)
    print(verify_log, file=sys.stderr)
    sys.exit(1)


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

    # 生成→検証→修正ループ（問題があれば自動でブロック）
    verified_text = generate_and_verify(date_str, slot)

    if not os.environ.get("TWITTER_API_KEY"):
        print("\nTWITTER_API_KEY未設定のため投稿をスキップ（ドライラン）")
        return

    print("\n[STEP 4] X に投稿中...")
    tweet_id = post_to_x(verified_text)
    print(f"\n✅ 投稿完了: https://x.com/hajime_cp/status/{tweet_id}")


if __name__ == "__main__":
    main()
