#!/usr/bin/env python3
"""
@hajime_cp X運用 日次ワークフロー エントリーポイント

使い方:
    python3 workflow/run_daily.py

このスクリプトは「決定論的な準備処理」だけを実行する。
分析・下書き生成・検証・予約登録の判断は Claude 自身が行う。

実行ステップ:
    [SCRIPT] Step 1: 競合・トレンド収集の検索計画を生成
    [CLAUDE] Step 2: WebSearch で各クエリを実行し raw_trends.json を保存
    [CLAUDE] Step 3: 分析結果からテーマを選定し drafts.md を生成
    [SCRIPT] Step 4: 検証チェックリストテンプレートを生成
    [CLAUDE] Step 5: WebSearch で事実主張を2ソース以上裏取り、verification_log.md を完成させる
    [CLAUDE] Step 6: scripts/x-schedule-post.md の手順に従い X予約投稿を登録
    [CLAUDE] Step 7: 完了報告を出力
"""

import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
JST      = timezone(timedelta(hours=9))


def run_step(label: str, cmd: list[str]) -> bool:
    print(f"\n{'='*60}")
    print(f"▶ {label}")
    print(f"  コマンド: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"\n❌ エラー: {label} が失敗しました（終了コード: {result.returncode}）")
        return False
    return True


def print_claude_step(step_num: int, label: str, details: list[str]):
    print(f"\n{'='*60}")
    print(f"⏸  Step {step_num}: {label}  ← Claude が実行")
    for d in details:
        print(f"   {d}")
    print(f"{'='*60}")


def main():
    date_str = datetime.now(JST).strftime("%Y-%m-%d")
    out_dir  = ROOT_DIR / "marketing" / "content-plan" / "drafts" / date_str

    print(f"""
╔══════════════════════════════════════════════════════╗
║  @hajime_cp X運用ワークフロー                        ║
║  実行日: {date_str}                              ║
╚══════════════════════════════════════════════════════╝
""")

    # ---- Step 1: 検索計画の生成（スクリプト）----
    ok = run_step(
        "Step 1: 競合・トレンド収集の検索計画を生成",
        [sys.executable, str(ROOT_DIR / "workflow" / "01_collect_trends.py"), "--date", date_str]
    )
    if not ok:
        sys.exit(1)

    # ---- Step 2〜3: Claude が実行 ----
    print_claude_step(2, "WebSearch で各クエリを実行し raw_trends.json を保存", [
        f"対象ファイル: {out_dir / 'search_plan.json'}",
        "各クエリを WebSearch で実行し、結果を同ディレクトリの raw_trends.json に保存してください",
        "「なぜ伸びているか」の分析メモを各結果に追記してください",
    ])

    print_claude_step(3, "テーマ選定 → drafts.md を生成（3〜5本）", [
        f"対象ファイル: {out_dir / 'raw_trends.json'}, {out_dir / 'existing_themes.json'}",
        "existing_themes.json と照合して既存テーマとの重複を避けること",
        "CLAUDE.md §2 の文体ルール（僕・句点なし・◽️・■）を厳守すること",
        f"出力先: {out_dir / 'drafts.md'}",
        "",
        "drafts.md のフォーマット（各投稿の区切り）:",
        "  ## 投稿1",
        "  （本文）",
        "  ---",
        "  ## 投稿2",
        "  （本文）",
        "  ---",
    ])

    # ---- Step 4: 検証テンプレート生成（スクリプト）----
    print(f"\n⏸  drafts.md の生成が完了したら Enter キーを押してください...")
    input()

    ok = run_step(
        "Step 4: 検証チェックリストテンプレートを生成",
        [sys.executable, str(ROOT_DIR / "workflow" / "03_verify_drafts.py"), "--date", date_str]
    )
    if not ok:
        sys.exit(1)

    # ---- Step 5〜7: Claude が実行 ----
    print_claude_step(5, "事実主張を2ソース以上で裏取り → verification_log.md を完成させる", [
        f"対象ファイル: {out_dir / 'verification_template.json'}",
        "CLAUDE.md §3 の検証プロトコル（1〜6）を完全に満たすまで繰り返すこと",
        "誤りがあれば drafts.md を修正し、Step 4 から再実行すること",
        f"完成版を保存先: {out_dir / 'verification_log.md'}",
    ])

    print_claude_step(6, "X予約投稿を登録（Claude in Chrome）", [
        f"手順書: {ROOT_DIR / 'scripts' / 'x-schedule-post.md'}",
        "手順書の内容に従い、X Web UI で予約投稿を登録してください",
        "登録前に必ず @hajime_cp でログイン中であることを確認すること",
        "予約投稿以外の操作（DM・フォロー等）は行わないこと",
    ])

    print_claude_step(7, "完了報告を出力", [
        "・生成した下書き一覧（本文＋予約時刻）",
        "・各下書きの検証ログ要約",
        "・予約時刻の選定根拠",
        "・判断に迷った点があればその内容と理由",
    ])

    print(f"""
╔══════════════════════════════════════════════════════╗
║  スクリプト処理が完了しました                        ║
║  上記の Claude 実行ステップを順番に進めてください    ║
╚══════════════════════════════════════════════════════╝
出力ディレクトリ: {out_dir}
""")


if __name__ == "__main__":
    main()
