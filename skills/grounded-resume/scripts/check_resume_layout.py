#!/usr/bin/env python3
"""Measure resume pagination, margins, and final-page bottom whitespace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pdfplumber


LETTER = (612.0, 792.0)


def inspect_layout(pdf_path: Path, min_blank: float = 0.05, max_blank: float = 0.08) -> dict[str, Any]:
    failures: list[str] = []
    with pdfplumber.open(pdf_path) as document:
        pages = len(document.pages)
        if pages != 1:
            failures.append(f"expected 1 page, found {pages}")
        if not document.pages:
            return {"status": "FAIL", "failures": ["PDF has no pages"], "pages": 0}
        page = document.pages[-1]
        if abs(float(page.width) - LETTER[0]) > 3 or abs(float(page.height) - LETTER[1]) > 3:
            failures.append(f"page is {page.width:.1f}x{page.height:.1f}pt, not US Letter")
        if not page.chars:
            failures.append("page has no extractable text")
            bottom_ratio = 1.0
            left_margin = right_margin = 0.0
        else:
            top_margin = min(float(char["top"]) for char in page.chars)
            if top_margin < 20:
                failures.append(f"unsafe top text margin: {top_margin:.1f}pt")
            text_bottom = max(float(char["bottom"]) for char in page.chars)
            bottom_ratio = (float(page.height) - text_bottom) / float(page.height)
            left_margin = min(float(char["x0"]) for char in page.chars)
            right_margin = float(page.width) - max(float(char["x1"]) for char in page.chars)
            if left_margin < 20 or right_margin < 20:
                failures.append(f"unsafe horizontal text margin: left={left_margin:.1f}pt right={right_margin:.1f}pt")
            if bottom_ratio < min_blank:
                failures.append(f"bottom whitespace {bottom_ratio:.1%} is below {min_blank:.1%}")
            if bottom_ratio > max_blank:
                failures.append(f"bottom whitespace {bottom_ratio:.1%} exceeds {max_blank:.1%}")
        return {
            "status": "FAIL" if failures else "PASS",
            "pages": pages,
            "page_width": float(page.width),
            "page_height": float(page.height),
            "bottom_blank_ratio": round(bottom_ratio, 5),
            "left_text_margin_pt": round(left_margin, 2),
            "right_text_margin_pt": round(right_margin, 2),
            "failures": failures,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--min-bottom-blank-ratio", type=float, default=0.05)
    parser.add_argument("--max-bottom-blank-ratio", type=float, default=0.08)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    if not args.pdf.is_file():
        print(f"FAIL: PDF not found: {args.pdf}")
        return 2
    result = inspect_layout(args.pdf, args.min_bottom_blank_ratio, args.max_bottom_blank_ratio)
    print(json.dumps(result, indent=2))
    if args.json_output:
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

