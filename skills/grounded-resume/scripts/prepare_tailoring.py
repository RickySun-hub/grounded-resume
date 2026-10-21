#!/usr/bin/env python3
"""Analyze a JD and create an evidence-linked resume composition plan."""

from __future__ import annotations

import argparse
from pathlib import Path

from resume_lib import DEFAULT_INDEX, prepare_plan, read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd", type=Path, required=True)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--req-id", default="no-req-id")
    parser.add_argument("--variant", default="auto", choices=["auto", "data_science", "ml_engineer", "ai_engineer", "research_engineer", "applied_scientist", "data_engineering", "data_analyst", "business_analytics"])
    parser.add_argument("--jd-status", default="unverified", choices=["verified", "unverified", "local-regression", "role-family-base"])
    parser.add_argument("--location")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    jd = args.jd.read_text(encoding="utf-8")
    plan = prepare_plan(jd, read_json(args.evidence_index), args.company, args.role, args.req_id, args.variant, args.jd_status, args.location)
    write_json(args.output, plan)
    selected = sum(len(entry["bullets"]) for entry in plan["entries"])
    print(f"PASS: wrote {args.output}")
    print(f"variant={plan['target']['variant']} selected_bullets={selected} missing_terms={len(plan['jd']['analysis']['missing_terms'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
