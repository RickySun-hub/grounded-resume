#!/usr/bin/env python3
"""Validate plan provenance, fixed facts, and final PDF text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pdfplumber

from resume_lib import CONTENT_POLICY_VERSION, DEFAULT_INDEX, number_tokens, read_json, write_json


STALE_OR_UNSAFE = []


def extract_pdf_text(path: Path) -> str:
    with pdfplumber.open(path) as document:
        return "\n".join(page.extract_text() or "" for page in document.pages)


def validate(plan: dict[str, Any], index: dict[str, Any], tex_text: str, pdf_text: str) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = ["Automated checks cannot establish semantic truth; compare every rewrite with its source."]
    from compose_resume import validate_plan_claims
    try:
        validate_plan_claims(plan, index)
    except (ValueError, KeyError) as exc:
        failures.append(str(exc))
    source_map = {bullet["id"]: bullet for item in index["items"] for bullet in item["bullets"]}
    if plan.get("evidence_index_sha256") != index.get("source_sha256"):
        failures.append("plan evidence hash does not match current master profile")
    if plan.get("layout", {}).get("spacing_mode") == "expanded":
        failures.append("expanded spacing is not an acceptable substitute for project evidence")
    seen_sources: set[str] = set()
    for entry in plan.get("entries", []):
        if entry.get("kind") == "project" and not 2 <= len(entry.get("bullets", [])) <= 4:
            failures.append(f"project {entry.get('item_id')} must have 2-4 bullets")
        if not entry.get("bullets"):
            failures.append(f"empty selected entry: {entry.get('item_id')}")
        for bullet in entry.get("bullets", []):
            source_id = bullet.get("source_id", "")
            if source_id not in source_map:
                failures.append(f"unknown source_id: {source_id}")
                continue
            if source_id in seen_sources:
                failures.append(f"duplicate source_id: {source_id}")
            seen_sources.add(source_id)
            new_numbers = set(number_tokens(bullet.get("final_text", ""))) - set(source_map[source_id]["numbers"])
            if new_numbers:
                failures.append(f"{source_id} introduced numbers: {sorted(new_numbers)}")
    if "@@" in tex_text:
        failures.append("unresolved template placeholder")
    for pattern in STALE_OR_UNSAFE:
        if re.search(pattern, tex_text, re.I) or re.search(pattern, pdf_text, re.I):
            failures.append(f"stale or unsafe wording matched: {pattern}")
    bullet_count = pdf_text.count("•")
    dash_list_lines = [line for line in pdf_text.splitlines() if re.match(r"^\s*[-–—]\s+", line)]
    if bullet_count < len(seen_sources):
        failures.append(f"solid round bullet count {bullet_count} is below selected bullet count {len(seen_sources)}")
    if dash_list_lines:
        failures.append(f"dash-style list markers found on {len(dash_list_lines)} PDF text lines")
    required_sections = ["Education", "Technical Skills", "Professional Experience", "Selected Projects"]
    positions = [pdf_text.find(section) for section in required_sections]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        failures.append("required sections are missing or out of order")
    jd_status = plan.get("jd", {}).get("status")
    if jd_status != "verified":
        warnings.append(f"JD status is {jd_status}; artifact is not application-ready")
    missing_terms = plan.get("jd", {}).get("analysis", {}).get("missing_terms", [])
    if missing_terms:
        warnings.append("unsupported JD terms were intentionally omitted: " + ", ".join(missing_terms))
    return {
        "jd_status": plan.get("jd", {}).get("status"),
        "content_policy_version": CONTENT_POLICY_VERSION,
        "project_bullet_counts": {e["item_id"]: len(e["bullets"]) for e in plan.get("entries",[]) if e["kind"]=="project"},
        "status": "PASS" if not failures else "FAIL",
        "application_ready": False,
        "selected_bullet_count": len(seen_sources),
        "solid_round_bullet_count": bullet_count,
        "bullet_style": "solid-round",
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--tex", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(read_json(args.plan), read_json(args.evidence_index), args.tex.read_text(encoding="utf-8"), extract_pdf_text(args.pdf))
    write_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
