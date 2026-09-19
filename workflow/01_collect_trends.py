#!/usr/bin/env python3
"""
Step 1: 競合・トレンド収集スクリプト
- competitor-accounts.json に定義されたアカウント・クエリでWebSearchを実行
- 結果を marketing/content-plan/drafts/YYYY-MM-DD/raw_trends.json に保存
- このスクリプト自体はデータ収集と保存のみ担当。「なぜ伸びているか」の分析はClaude自身が行う

Usage:
    python3 workflow/01_collect_trends.py
    python3 workflow/01_collect_trends.py --date 2026-09-16  # 特定日付で実行
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path


# --- 設定 ---
ROOT_DIR     = Path(__file__).parent.parent
ACCOUNTS_JSON = ROOT_DIR / "scripts" / "competitor-accounts.json"
DRAFTS_DIR   = ROOT_DIR / "marketing" / "content-plan" / "drafts"

JST = timezone(timedelta(hours=9))


def get_today_str(date_override: str | None = None) -> str:
    if date_override:
        return date_override
    return datetime.now(JST).strftime("%Y-%m-%d")


def build_search_queries(accounts_data: dict) -> list[dict]:
    """
    競合アカウント × トピッククエリ を検索クエリリストに変換する。
    Claude はこのリストを見て WebSearch を順番に実行する。
    """
    queries = []

    # 固定ウォッチリスト
    for acct in accounts_data["watch_accounts"]:
        queries.append({
            "type": "account",
            "handle": acct["handle"],
            "name": acct["name"],
            "lang": acct["lang"],
            "search_query": f"from:{acct['handle']}",
            "note": acct["note"],
        })

    # トピック別広域検索
    for topic in accounts_data["topic_queries"]:
        queries.append({
            "type": "topic",
            "category": topic["category"],
            "search_query": topic["query"],
            "note": "直近24h以内に伸びている投稿を広域探索",
        })

    return queries


def prepare_output_dir(date_str: str, slot: str | None = None) -> Path:
    if slot:
        out_dir = DRAFTS_DIR / date_str / slot
    else:
        out_dir = DRAFTS_DIR / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def save_search_plan(out_dir: Path, queries: list[dict], date_str: str) -> Path:
    """
    Claude が実行すべき検索クエリ一覧を JSON で保存する。
    実際の WebSearch 実行は Claude 自身が行うため、
    このスクリプトは「何を検索すべきか」の計画書を出力するだけ。
    """
    plan = {
        "generated_at": datetime.now(JST).isoformat(),
        "target_date": date_str,
        "instruction": (
            "以下の queries を順番に WebSearch で実行し、"
            "各結果を results フィールドに追記してから "
            "raw_trends.json として保存してください。"
            "「なぜ伸びているか」の分析は results 収集後に Claude 自身が行います。"
        ),
        "queries": queries,
        "results": [],   # Claude が WebSearch 実行後に埋める
    }

    out_path = out_dir / "search_plan.json"
    out_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def load_existing_themes() -> list[str]:
    """
    marketing/content-plan/ 配下の既存 .md ファイルからテーマ一覧を抽出。
    重複チェック用。タイトル行（###で始まる行）を収集する。
    """
    content_dir = ROOT_DIR / "marketing" / "content-plan"
    themes = []
    for md_file in content_dir.glob("*.md"):
        for line in md_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("### "):
                themes.append(line.lstrip("# ").strip())
    return themes


def main():
    parser = argparse.ArgumentParser(description="競合・トレンド収集の検索計画を生成する")
    parser.add_argument("--date", help="実行日付 YYYY-MM-DD（省略時は今日）")
    parser.add_argument("--slot", choices=["morning", "noon", "evening"],
                        help="投稿スロット（指定時はスロット別ディレクトリに保存）")
    args = parser.parse_args()

    date_str = get_today_str(args.date)
    print(f"[01_collect_trends] 実行日付: {date_str}" + (f" / slot: {args.slot}" if args.slot else ""))

    # アカウント定義読み込み
    if not ACCOUNTS_JSON.exists():
        print(f"ERROR: {ACCOUNTS_JSON} が見つかりません", file=sys.stderr)
        sys.exit(1)
    accounts_data = json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8"))

    # 検索クエリ一覧を構築
    queries = build_search_queries(accounts_data)
    print(f"  検索クエリ数: {len(queries)}（アカウント: {len(accounts_data['watch_accounts'])}件 + トピック: {len(accounts_data['topic_queries'])}件）")

    # 出力ディレクトリ準備
    out_dir = prepare_output_dir(date_str, args.slot)
    print(f"  出力先: {out_dir}")

    # 検索計画書を保存
    plan_path = save_search_plan(out_dir, queries, date_str)
    print(f"  検索計画書を保存: {plan_path.name}")

    # 既存テーマ一覧を保存（重複チェック用）
    existing_themes = load_existing_themes()
    themes_path = out_dir / "existing_themes.json"
    themes_path.write_text(
        json.dumps({"count": len(existing_themes), "themes": existing_themes}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  既存テーマ数: {len(existing_themes)}件 → {themes_path.name} に保存")

    print()
    print("=" * 60)
    print("【次のアクション（Claude が実行）】")
    print(f"  1. {plan_path} を読み込む")
    print(f"  2. queries の各エントリに対して WebSearch を実行")
    print(f"  3. 結果を raw_trends.json に保存")
    print(f"  4. 「なぜ伸びているか」を分析して下書き生成に進む")
    print("=" * 60)


if __name__ == "__main__":
    main()
