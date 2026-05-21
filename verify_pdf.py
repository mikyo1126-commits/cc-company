#!/usr/bin/env python3
"""
verify_pdf.py — PDF品質チェックスクリプト

使い方:
  python3 verify_pdf.py <pdf_path> [--sections "見出し1,見出し2"] [--expected-pages N]

終了コード:
  0 = 合格 (pass)
  1 = 不合格 (fail)
"""

import sys
import os
import json
import argparse
import fitz  # pymupdf


def check_overlap(page, page_num: int) -> list[dict]:
    """同一ページ内でテキストspanのy範囲が重なるペアを検出する"""
    issues = []
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

    spans = []
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                bbox = span["bbox"]  # (x0, y0, x1, y1)
                spans.append({
                    "text": text,
                    "x0": bbox[0], "y0": bbox[1],
                    "x1": bbox[2], "y1": bbox[3],
                })

    spans.sort(key=lambda s: s["y0"])

    for i in range(len(spans)):
        a = spans[i]
        for j in range(i + 1, len(spans)):
            b = spans[j]
            if b["y0"] >= a["y1"]:
                break
            y_overlap = a["y1"] - b["y0"]
            if y_overlap <= 4:
                continue
            x_overlap = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
            if x_overlap < -8:
                continue
            issues.append({
                "type": "overlap",
                "page": page_num,
                "text_a": a["text"][:40],
                "text_b": b["text"][:40],
                "overlap_pt": round(y_overlap, 1),
            })
    return issues


def main():
    parser = argparse.ArgumentParser(description="PDF品質チェック")
    parser.add_argument("pdf_path", help="チェック対象のPDFファイルパス")
    parser.add_argument("--sections", default="", help="カンマ区切りの必須セクション名")
    parser.add_argument("--expected-pages", type=int, default=0, help="期待するページ数（0=チェックしない）")
    parser.add_argument("--min-kb", type=int, default=30, help="最小ファイルサイズ(KB)")
    parser.add_argument("--max-mb", type=int, default=20, help="最大ファイルサイズ(MB)")
    args = parser.parse_args()

    issues = []
    result = {"pass": False, "issues": issues, "pdf": args.pdf_path}

    if not os.path.exists(args.pdf_path):
        issues.append({"type": "file_not_found", "path": args.pdf_path})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    size_bytes = os.path.getsize(args.pdf_path)
    size_kb = size_bytes / 1024
    result["size_kb"] = round(size_kb, 1)
    if size_kb < args.min_kb:
        issues.append({"type": "file_too_small", "size_kb": round(size_kb, 1), "min_kb": args.min_kb})
    if size_kb > args.max_mb * 1024:
        issues.append({"type": "file_too_large", "size_mb": round(size_kb / 1024, 1), "max_mb": args.max_mb})

    try:
        doc = fitz.open(args.pdf_path)
        page_count = len(doc)
        result["page_count"] = page_count

        if args.expected_pages > 0 and abs(page_count - args.expected_pages) > 1:
            issues.append({
                "type": "wrong_page_count",
                "expected": args.expected_pages,
                "actual": page_count,
            })

        all_text = ""
        for i, page in enumerate(doc, start=1):
            all_text += (page.get_text() or "") + "\n"
            issues.extend(check_overlap(page, i))

        if args.sections:
            for s in args.sections.split(","):
                s = s.strip()
                if s and s not in all_text:
                    issues.append({"type": "missing_section", "expected": s})

        doc.close()

    except Exception as e:
        issues.append({"type": "pdf_read_error", "error": str(e)})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    result["pass"] = len(issues) == 0
    result["issue_count"] = len(issues)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
