#!/usr/bin/env python3
"""
Step 3: 検証チェックリスト生成・検証ログ保存スクリプト
- drafts.md から各投稿を読み込み、事実主張を抽出するテンプレートを生成する
- Claude が WebSearch で裏取りした後に検証ログを保存する
- CLAUDE.md の検証プロトコル（1〜6）に完全準拠

Usage:
    python3 workflow/03_verify_drafts.py --date 2026-09-16
"""

import json
import re
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT_DIR   = Path(__file__).parent.parent
DRAFTS_DIR = ROOT_DIR / "marketing" / "content-plan" / "drafts"
JST        = timezone(timedelta(hours=9))


def get_today_str(date_override: str | None = None) -> str:
    if date_override:
        return date_override
    return datetime.now(JST).strftime("%Y-%m-%d")


def parse_drafts(drafts_path: Path) -> list[dict]:
    """
    drafts.md から各投稿ブロックを抽出する。
    フォーマット想定:
        ## 投稿1
        （本文）
        ---
        ## 投稿2
        ...
    """
    if not drafts_path.exists():
        return []

    text = drafts_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n## 投稿\d+", text)
    drafts = []
    for i, block in enumerate(blocks[1:], start=1):  # 最初の空ブロックをスキップ
        body = block.strip().rstrip("-").strip()
        drafts.append({"index": i, "body": body})
    return drafts


def extract_fact_claims(body: str) -> list[str]:
    """
    投稿本文から事実主張（検証対象）の候補行を抽出する。
    - 数値を含む行
    - 価格・変動率・日付・固有名詞引用を含む行
    Claude による最終判断の前段として、機械的に候補を絞り込む。
    """
    candidates = []
    patterns = [
        r"\d+[,，]\d+",                    # 価格（例: 145,000 / 1,500）
        r"\d+(\.\d+)?[%％]",               # 変動率（例: +2.5%）
        r"\d{4}年\d{1,2}月",               # 日付（例: 2026年9月）
        r"[+-]\$?¥?￥?\d+",               # 変動額
        r"ATH|史上最高|最安値|過去最大",   # 記録系表現
        r"発表|声明|述べた|コメント",       # 引用系表現
        r"FOMC|FRB|Fed|日銀|BOJ",          # 機関名
    ]
    combined = re.compile("|".join(patterns))

    for line in body.splitlines():
        line = line.strip()
        if line and combined.search(line):
            candidates.append(line)

    return candidates


def build_verification_template(drafts: list[dict]) -> dict:
    """
    各投稿の検証チェックリストテンプレートを生成する。
    Claude が WebSearch で各項目を裏取りした後にこの構造を埋める。
    """
    template = {
        "generated_at": datetime.now(JST).isoformat(),
        "protocol": "CLAUDE.md §3 検証プロトコル（1〜6）に準拠",
        "instruction": (
            "各 fact_claims の項目を独立した2つ以上のソースで裏取りし、"
            "verified フィールドと sources フィールドを埋めてください。"
            "すべての項目が verified=true になるまで下書きを修正し、"
            "完了後に verification_log.md として保存してください。"
        ),
        "posts": [],
    }

    for draft in drafts:
        claims = extract_fact_claims(draft["body"])
        template["posts"].append({
            "index": draft["index"],
            "body_preview": draft["body"][:80] + "..." if len(draft["body"]) > 80 else draft["body"],
            "fact_claims": [
                {
                    "claim": claim,
                    "verified": None,   # Claude が True/False を記入
                    "sources": [],       # ["URL or 出典名", "URL or 出典名"]
                    "notes": "",         # 誤りがあった場合の修正内容
                }
                for claim in claims
            ],
            "style_check": {
                "uses_boku": None,         # 一人称「僕」を使っているか
                "no_kuten": None,          # 文末に「。」がないか
                "uses_checkbox": None,     # 箇条書きが「◽️」になっているか
                "no_closing_phrase": None, # 「ではまた明日」等の定型句がないか
            },
            "overall_verified": None,     # 上記すべてが通過したら True
        })

    return template


def save_verification_log_md(out_dir: Path, log: dict, date_str: str) -> Path:
    """
    検証完了後の verification_log.md を生成する（Claude が結果を書き込んだ後に呼ぶ想定）。
    このスクリプトが生成するのは「テンプレート」のみ。
    """
    lines = [
        f"# 検証ログ {date_str}",
        f"生成日時: {log['generated_at']}",
        f"準拠プロトコル: {log['protocol']}",
        "",
    ]

    for post in log["posts"]:
        lines.append(f"## 投稿{post['index']}")
        lines.append("")
        lines.append("### 事実主張チェックリスト")
        for item in post["fact_claims"]:
            status = "✅" if item["verified"] else ("❌" if item["verified"] is False else "⬜")
            lines.append(f"- {status} `{item['claim']}`")
            if item["sources"]:
                for src in item["sources"]:
                    lines.append(f"  - 出典: {src}")
            if item["notes"]:
                lines.append(f"  - 備考: {item['notes']}")
        lines.append("")
        lines.append("### 文体チェック")
        sc = post["style_check"]
        lines.append(f"- 一人称「僕」: {'✅' if sc['uses_boku'] else '❌'}")
        lines.append(f"- 句点なし: {'✅' if sc['no_kuten'] else '❌'}")
        lines.append(f"- 箇条書き◽️: {'✅' if sc['uses_checkbox'] else '❌'}")
        lines.append(f"- 定型句なし: {'✅' if sc['no_closing_phrase'] else '❌'}")
        lines.append("")
        verdict = "✅ 検証完了" if post["overall_verified"] else "⬜ 未完了"
        lines.append(f"**総合判定: {verdict}**")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path = out_dir / "verification_log.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="検証チェックリストのテンプレートを生成する")
    parser.add_argument("--date", help="実行日付 YYYY-MM-DD（省略時は今日）")
    args = parser.parse_args()

    date_str = get_today_str(args.date)
    out_dir  = DRAFTS_DIR / date_str

    print(f"[03_verify_drafts] 実行日付: {date_str}")

    drafts_path = out_dir / "drafts.md"
    if not drafts_path.exists():
        print(f"ERROR: {drafts_path} が見つかりません。先に下書きを生成してください。", file=sys.stderr)
        sys.exit(1)

    drafts = parse_drafts(drafts_path)
    print(f"  下書き件数: {len(drafts)}本")

    # 検証テンプレート生成（JSON）
    template = build_verification_template(drafts)
    template_path = out_dir / "verification_template.json"
    template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  検証テンプレートを保存: {template_path.name}")

    # 空の verification_log.md を生成（Claude が埋める）
    log_path = save_verification_log_md(out_dir, template, date_str)
    print(f"  検証ログひな形を保存: {log_path.name}")

    print()
    print("=" * 60)
    print("【次のアクション（Claude が実行）】")
    print(f"  1. {template_path.name} の fact_claims を確認")
    print(f"  2. 各 claim を WebSearch で2ソース以上裏取り")
    print(f"  3. 誤りがあれば drafts.md を修正してから再度このスクリプトを実行")
    print(f"  4. すべて verified=true になったら手順書に従い予約投稿へ進む")
    print("=" * 60)


if __name__ == "__main__":
    main()
