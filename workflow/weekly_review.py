#!/usr/bin/env python3
"""
週次レビュー（毎週日曜 23:59 JST 起動）

月曜 0:00〜日曜 23:59（日本時間）の1週間の投稿の反応を集め、Opus 5.5 に
「どの投稿が伸びたか・なぜ伸びたか・なぜ伸びなかったか・今週どう改善するか」を分析させる。
- 全文レポート: workflow/reports/<週の開始日>.md
- 投稿を書くAIに渡す改善方針: workflow/insights.md
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import tweepy

sys.path.insert(0, str(Path(__file__).parent))
from auto_post import JST, call_claude  # noqa: E402
from update_insights import analyze_tweet, generate_md, get_client  # noqa: E402

ROOT_DIR = Path(__file__).parent.parent
REPORTS_DIR = ROOT_DIR / "workflow" / "reports"
INSIGHTS_PATH = ROOT_DIR / "workflow" / "insights.md"
POSTED_LOG = ROOT_DIR / "workflow" / "posted_log.jsonl"
ANALYST_MODEL = os.environ.get("ANALYST_MODEL", "claude-opus-5-5")

FIXED_RULES = """\
- ビットコイン・仮想通貨は扱わない（はじめさん本人が投稿しているため）
- 価格や価格の水準は数字で書かない
- 価格分析の投稿では、自分のエントリー時期（「ここから入りたい」等）を書かない
- 絵文字は1投稿2個まで。事実は2つ以上のソースで確認したものだけ
- 語尾は言い切る（「っぽい」「かも」「気がする」は使わない。見通しは「〜そうだ」）。ただし将来の値動きは断定しない
- 読者はFX未経験者も含む。1行目は24文字以内で、未経験者でも一読で分かり続きを読みたくなる一文（言いたいことは1つ。「いつ・何をした時」と「どうなるか」を具体的に）。専門用語・pips・計算が必要な数字（％計算など）は使わず、円の金額や普段の言葉で書く
- 投稿時刻は毎日 9:00 と 18:00（日本時間）
- 平日: 朝は初心者向け基礎、夜は失敗談が基本。ナスダック・ゴールド・ドル円（サブで日経平均）に大きな値動きがあった時だけ相場の投稿
- 土日: 土曜朝は今週のまとめ、土曜夜・日曜朝はファンダメンタルズ、日曜夜は来週の注目イベント"""

ANALYSIS_PROMPT = """\
あなたはFXトレーダー「はじめ」さん（@hajime_cp）のX運用アナリストです。
このアカウントは、はじめさん本人の投稿と、AIが書く自動投稿（毎日9時・18時）が混在しています。
先週（{start}〜{end} 日本時間）の投稿の反応を分析し、今週月曜からの自動投稿をどう改善するかをまとめてください。

## 自動投稿の固定ルール（変えられないので、これに反する提案はしない）
{fixed_rules}

## 先週の投稿（反応の良い順。エンゲージ率 = (いいね+RT+返信+引用+ブックマーク) / 表示回数）
{posts}

## 長期データ（直近の投稿全体の集計。テーマ別・時間帯別・曜日別）
{long_term}

## 前回の分析で決めた改善方針
{previous}

## 書くこと
データから言えることと推測をはっきり分け、件数が少ないものは言い過ぎない。数字は上のデータから引用する。

### 1. 先週の結果
自動投稿と本人投稿それぞれの件数・平均表示回数・平均エンゲージ率。前回の改善方針を試した効果が見えるなら、それも。

### 2. 反応が良かった投稿と、伸びた理由
上位3件程度。テーマ、1行目のつかみ、文章の構成、長さ、締め方、絵文字、投稿時間・曜日、その日の相場の話題性などから理由を考える。

### 3. 反応が悪かった投稿と、伸びなかった理由
下位3件程度。同じ観点で。

### 4. 見えてきたパターン
表示回数を伸ばす要素と、エンゲージ率を上げる要素は分けて考える。

### 5. 今週の自動投稿への指示
最後に、投稿を書くAIにそのまま渡す指示を <for_writer> と </for_writer> で囲んで書く。
中身は「今週の改善方針」として、固定ルールの範囲内で具体的に実行できる指示を5〜8個と、今週試してみること1〜2個（効果は来週の分析で確かめる）。
投稿の文面をそのまま真似させる書き方はしない（毎回同じような投稿になるため）。
"""


def analysis_week(now: datetime) -> tuple[datetime, datetime]:
    """日曜の深夜〜月曜に起動しても、同じ「月曜0時〜翌月曜0時」の週になるようにする"""
    shifted = now + timedelta(hours=12)
    week_end = (shifted - timedelta(days=shifted.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return week_end - timedelta(days=7), week_end


def load_auto_post_ids() -> set[str]:
    if not POSTED_LOG.exists():
        return set()
    ids = set()
    for line in POSTED_LOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(str(json.loads(line)["id"]))
    return ids


def fetch_week_metrics(client, user_id, start: datetime, end: datetime) -> dict[str, dict]:
    """プロフィールクリック等の非公開指標（自分の投稿・30日以内のみ取得可）。取れなければ空"""
    try:
        resp = client.get_users_tweets(
            id=user_id, max_results=100, start_time=start, end_time=end,
            tweet_fields=["non_public_metrics"], exclude=["retweets", "replies"], user_auth=True,
        )
        return {str(t.id): (t.non_public_metrics or {}) for t in (resp.data or [])}
    except tweepy.TweepyException as e:
        print(f"::warning::非公開指標は取得できなかったので、公開指標だけで分析します: {e}")
        return {}


def post_row(t, auto_ids: set[str], private: dict) -> dict:
    m = t.public_metrics
    impressions = m.get("impression_count", 0)
    engagements = (m["like_count"] + m["retweet_count"] + m["reply_count"]
                   + m.get("quote_count", 0) + m.get("bookmark_count", 0))
    created = t.created_at.astimezone(JST)
    return {
        "kind": "自動" if str(t.id) in auto_ids else "本人",
        "at": created.strftime("%m/%d(%a) %H:%M"),
        "impressions": impressions,
        "likes": m["like_count"],
        "retweets": m["retweet_count"],
        "replies": m["reply_count"],
        "quotes": m.get("quote_count", 0),
        "bookmarks": m.get("bookmark_count", 0),
        "profile_clicks": private.get("user_profile_clicks"),
        "engagement_rate": engagements / impressions if impressions else 0.0,
        "text": t.text,
    }


def format_posts(rows: list[dict]) -> str:
    out = []
    for i, r in enumerate(rows, 1):
        clicks = "" if r["profile_clicks"] is None else f" / プロフィールクリック {r['profile_clicks']}"
        out.append(
            f"#{i} [{r['kind']}] {r['at']} / 表示 {r['impressions']} / いいね {r['likes']} / RT {r['retweets']} / "
            f"返信 {r['replies']} / 引用 {r['quotes']} / ブックマーク {r['bookmarks']}{clicks} / "
            f"エンゲージ率 {r['engagement_rate']*100:.1f}%\n{r['text']}\n"
        )
    return "\n".join(out) if out else "（先週の投稿なし）"


def pick_sections(md: str, titles: tuple[str, ...]) -> str:
    parts = re.split(r"(?m)^## ", md)
    return "\n".join("## " + p.strip() + "\n" for p in parts if p.startswith(titles))


def run_analysis(prompt: str) -> str:
    try:
        return call_claude(prompt, timeout=900, model=ANALYST_MODEL)
    except Exception:
        print(f"::warning::{ANALYST_MODEL} を使えなかったため、既定のモデルで分析しました")
        return call_claude(prompt, timeout=900)


def main():
    start, end = analysis_week(datetime.now(JST))
    week_label = f"{start:%Y-%m-%d}〜{end - timedelta(days=1):%m-%d}"
    report_path = REPORTS_DIR / f"{start:%Y-%m-%d}.md"
    if report_path.exists():
        print(f"{week_label} の週次レビューは作成済みなので終了")
        return

    client = get_client()
    user_id = client.get_me(user_auth=True).data.id
    resp = client.get_users_tweets(
        id=user_id, max_results=100,
        tweet_fields=["public_metrics", "created_at", "text"],
        exclude=["retweets", "replies"], user_auth=True,
    )
    tweets = resp.data or []
    week_tweets = [t for t in tweets if start <= t.created_at.astimezone(JST) < end]
    private = fetch_week_metrics(client, user_id, start, end)
    auto_ids = load_auto_post_ids()

    rows = [post_row(t, auto_ids, private.get(str(t.id), {})) for t in week_tweets]
    rows.sort(key=lambda r: (r["engagement_rate"], r["impressions"]), reverse=True)

    long_term_all = generate_md(
        sorted([analyze_tweet(t) for t in tweets], key=lambda x: x["score"], reverse=True), len(tweets)
    ) if tweets else ""
    long_term = pick_sections(long_term_all, ("A.", "D.", "E."))
    previous = INSIGHTS_PATH.read_text(encoding="utf-8") if INSIGHTS_PATH.exists() else "（なし）"

    prompt = ANALYSIS_PROMPT.format(
        start=f"{start:%m/%d}", end=f"{end - timedelta(days=1):%m/%d}",
        fixed_rules=FIXED_RULES, posts=format_posts(rows),
        long_term=long_term or "（なし）", previous=previous,
    )
    analysis = run_analysis(prompt)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text(f"# 週次レビュー {week_label}\n\n{analysis}\n\n---\n\n## 先週の投稿データ\n\n{format_posts(rows)}\n", encoding="utf-8")
    print(f"レポートを保存: workflow/reports/{report_path.name}（投稿 {len(rows)} 件、うち自動 {sum(r['kind'] == '自動' for r in rows)} 件）")

    m = re.search(r"<for_writer>(.*?)</for_writer>", analysis, re.DOTALL)
    if m:
        INSIGHTS_PATH.write_text(
            f"# 週次レビューからの改善方針（{week_label} の分析）\n\n{m.group(1).strip()}\n\n---\n\n## 長期データ（参考）\n\n{long_term}",
            encoding="utf-8",
        )
        print("insights.md を更新")
    else:
        print("::warning::分析結果に <for_writer> がなかったため、insights.md は更新しない")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"# 週次レビュー {week_label}\n\n{analysis}\n")


if __name__ == "__main__":
    main()
