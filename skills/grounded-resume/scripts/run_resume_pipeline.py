#!/usr/bin/env python3
"""Stable end-to-end resume pipeline with evidence and layout gates."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from check_resume_layout import inspect_layout
from compose_resume import compose
from resume_lib import (
    DEFAULT_INDEX, DEFAULT_MASTER, CONTENT_POLICY_VERSION, MAX_TOTAL_BULLETS, build_evidence_index, item_from_index,
    prepare_plan, read_json, slugify, write_json,
)
from validate_tailoring import extract_pdf_text, validate


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SKILL_ROOT / "assets" / "resume-template.tex"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd", type=Path)
    parser.add_argument("--plan", type=Path, help="Reuse and update an already reviewed plan")
    parser.add_argument("--company")
    parser.add_argument("--role")
    parser.add_argument("--req-id", default="no-req-id")
    parser.add_argument("--variant", default="auto")
    parser.add_argument("--jd-status", default="unverified", choices=["verified", "unverified", "local-regression", "role-family-base"])
    parser.add_argument("--location")
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER)
    parser.add_argument("--evidence-index", type=Path, default=None)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-basename", help="Optional Windows-safe artifact stem without an extension")
    parser.add_argument("--tectonic")
    parser.add_argument("--max-layout-iterations", type=int, default=12)
    parser.add_argument("--no-auto-fit", action="store_true")
    return parser.parse_args()


def compile_tex(tex_path: Path, tectonic: str) -> Path:
    command = [tectonic, "--outdir", str(tex_path.parent), str(tex_path)]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"Tectonic failed with exit code {result.returncode}")
    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.is_file():
        raise RuntimeError(f"Tectonic did not create {pdf_path}")
    return pdf_path


def selected_bullets(plan: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [(entry, bullet) for entry in plan["entries"] for bullet in entry["bullets"]]


def remove_lowest_utility(plan: dict[str, Any]) -> str | None:
    removable = [(entry, bullet) for entry, bullet in selected_bullets(plan)
                 if len(entry["bullets"]) > max(2, entry.get("min_bullets", 2))]
    if removable:
        entry, bullet = min(removable, key=lambda pair: (pair[1].get("score", 0), -pair[1].get("line_cost", 1)))
        entry["bullets"].remove(bullet)
        bullet.update(selected=False, layout_rejected=True)
        plan["candidate_pool"].append(bullet)
        return bullet["source_id"]
    projects = [e for e in plan["entries"] if e["kind"] == "project"]
    if len(projects) > 1:
        entry = min(projects, key=lambda e: sum(b.get("score", 0) for b in e["bullets"]))
        plan["entries"].remove(entry)
        for bullet in entry["bullets"]:
            bullet.update(selected=False, layout_rejected=True)
            plan["candidate_pool"].append(bullet)
        return "project:" + entry["item_id"]
    return None


def add_highest_utility(plan: dict[str, Any], index: dict[str, Any]) -> str | None:
    count = len(selected_bullets(plan))
    if count >= MAX_TOTAL_BULLETS:
        return None
    entries = {e["item_id"]: e for e in plan["entries"]}
    pool = [b for b in plan["candidate_pool"] if not b.get("layout_rejected")]
    actions = []
    for item_id in dict.fromkeys(b["item_id"] for b in pool):
        bullets = sorted((b for b in pool if b["item_id"] == item_id), key=lambda b:b.get("score",0), reverse=True)
        if item_id in entries:
            entry = entries[item_id]
            if len(entry["bullets"]) >= min(4, entry.get("max_bullets", 4)):
                continue
            # Complete the narrative before adding a different project or fourth bullet.
            priority = 3 if len(entry["bullets"]) < entry.get("target_bullets", 3) else 1
            chosen = bullets[:1]
        else:
            item = item_from_index(index, item_id)
            if item["kind"] != "project" or item["visibility"] == "reference-only" or sum(e["kind"]=="project" for e in entries.values()) >= 3:
                continue
            if len(bullets) < 2:
                continue
            chosen = bullets[:min(3, MAX_TOTAL_BULLETS-count)]
            if len(chosen) < 2:
                continue
            priority = 2
        if count + len(chosen) <= MAX_TOTAL_BULLETS:
            actions.append((priority, sum(b.get("score",0) for b in chosen)/len(chosen), item_id, chosen))
    if not actions:
        return None
    _, _, item_id, chosen = max(actions, key=lambda a:a[:2])
    if item_id not in entries:
        item = item_from_index(index, item_id)
        entry = {key:item.get(key, "") for key in ("kind", "name", "title", "location", "dates", "repository")}
        entry.update(item_id=item_id, bullets=[], min_bullets=2, target_bullets=3, max_bullets=4)
        plan["entries"].append(entry)
    else:
        entry = entries[item_id]
    for bullet in sorted(chosen, key=lambda b:b["source_id"]):
        plan["candidate_pool"].remove(bullet)
        bullet["selected"] = True
        entry["bullets"].append(bullet)
    return ",".join(b["source_id"] for b in chosen)


def render_png(pdf_path: Path) -> Path | None:
    renderer = shutil.which("pdftoppm")
    if not renderer:
        return None
    prefix = pdf_path.with_suffix("")
    if renderer.lower().endswith((".cmd", ".bat")):
        command = [os.environ.get("COMSPEC", "cmd.exe"), "/c", renderer, "-png", "-f", "1", "-singlefile", "-r", "150", str(pdf_path), str(prefix)]
    else:
        command = [renderer, "-png", "-f", "1", "-singlefile", "-r", "150", str(pdf_path), str(prefix)]
    result = subprocess.run(command, text=True, capture_output=True)
    png_path = prefix.with_suffix(".png")
    return png_path if result.returncode == 0 and png_path.is_file() else None


def main() -> int:
    args = parse_args()
    if args.plan is None and (args.jd is None or not args.company or not args.role):
        raise SystemExit("--jd, --company, and --role are required unless --plan is supplied")
    if args.plan is not None and not args.plan.is_file():
        raise SystemExit(f"Plan not found: {args.plan}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    args.evidence_index = args.evidence_index or args.output_dir / "evidence-index.json"
    evidence_index = build_evidence_index(args.master)
    write_json(args.evidence_index, evidence_index)
    if args.plan:
        plan = read_json(args.plan)
    else:
        jd_text = args.jd.read_text(encoding="utf-8")
        plan = prepare_plan(jd_text, evidence_index, args.company, args.role, args.req_id, args.variant, args.jd_status, args.location)

    plan["content_policy_version"] = CONTENT_POLICY_VERSION
    target = plan["target"]
    if args.output_basename:
        if re.search(r'[<>:"/\\|?*]', args.output_basename) or args.output_basename.endswith((".", " ")):
            raise SystemExit("--output-basename contains Windows-unsafe characters")
        resume_stem = args.output_basename
    else:
        resume_stem = slugify("_".join([target["company"], target["role"], target.get("req_id") or "no-req-id"])) + "_resume"
    plan_path = args.plan or args.output_dir / f"{resume_stem}_tailoring_plan.json"
    tex_path = args.output_dir / f"{resume_stem}.tex"
    qa_path = args.output_dir / f"{resume_stem}_qa.json"
    layout_path = args.output_dir / f"{resume_stem}_layout.json"
    template = args.template.read_text(encoding="utf-8")
    tectonic = args.tectonic or shutil.which("tectonic")
    if not tectonic or not Path(tectonic).is_file():
        raise SystemExit(f"Tectonic not found: {tectonic}")

    adjustments: list[dict[str, Any]] = plan.setdefault("layout_adjustments", [])
    pdf_path: Path | None = None
    layout: dict[str, Any] = {}
    for iteration in range(args.max_layout_iterations + 1):
        write_json(plan_path, plan)
        tex_path.write_text(compose(plan, evidence_index, template), encoding="utf-8")
        pdf_path = compile_tex(tex_path, tectonic)
        layout = inspect_layout(
            pdf_path,
            plan["layout"]["min_bottom_blank_ratio"],
            plan["layout"]["max_bottom_blank_ratio"],
        )
        if layout["status"] == "PASS" or args.no_auto_fit:
            break
        if iteration == args.max_layout_iterations:
            break
        crowded = layout["pages"] > 1 or layout["bottom_blank_ratio"] < plan["layout"]["min_bottom_blank_ratio"]
        changed = remove_lowest_utility(plan) if crowded else add_highest_utility(plan, evidence_index)
        if not changed:
            break
        action = "remove" if crowded else ("spacing" if changed.startswith("spacing:") else "add")
        adjustments.append({"iteration": iteration + 1, "action": action, "source_id": changed, "observed_bottom_blank_ratio": layout["bottom_blank_ratio"]})

    assert pdf_path is not None
    write_json(plan_path, plan)
    write_json(layout_path, layout)
    qa = validate(plan, evidence_index, tex_path.read_text(encoding="utf-8"), extract_pdf_text(pdf_path))
    qa["layout"] = layout
    qa["generator_fingerprint"] = hashlib.sha256(b"".join(
        p.read_bytes() for p in [Path(__file__), SKILL_ROOT/"scripts/resume_lib.py", SKILL_ROOT/"scripts/compose_resume.py", SKILL_ROOT/"scripts/validate_tailoring.py", SKILL_ROOT/"scripts/check_resume_layout.py", args.template]
    )).hexdigest()
    qa["pdf_sha256"] = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    qa["visual_review"] = {"status": "PENDING", "pdf_sha256": qa["pdf_sha256"]}
    qa["application_ready"] = False  # Requires inspection of these exact final PDF bytes.
    if layout["status"] != "PASS":
        qa["status"] = "FAIL"
        qa["application_ready"] = False
        qa["failures"].extend(layout["failures"])
    png_path = render_png(pdf_path)
    if png_path is None:
        qa["status"] = "FAIL"
        qa["application_ready"] = False
        qa["failures"].append("PNG preview was not rendered")
    source_files = [args.master]
    qa["source_files"] = {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    qa["template_path"] = str(args.template.resolve())
    qa["generator_sources"] = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), SKILL_ROOT/"scripts/resume_lib.py", SKILL_ROOT/"scripts/compose_resume.py", SKILL_ROOT/"scripts/validate_tailoring.py", SKILL_ROOT/"scripts/check_resume_layout.py", SKILL_ROOT/"scripts/finalize_resume_review.py", args.template]}
    qa["artifacts"] = {"pdf": str(pdf_path.resolve()), "tex": str(tex_path.resolve()), "plan": str(plan_path.resolve()), "layout": str(layout_path.resolve()), "preview_png": str(png_path.resolve()) if png_path else None}
    qa["artifact_sha256"] = {key:hashlib.sha256(Path(path).read_bytes()).hexdigest() for key,path in qa["artifacts"].items() if path and Path(path).is_file()}
    write_json(qa_path, qa)
    print(f"status={qa['status']} application_ready={qa['application_ready']}")
    print(f"pdf={pdf_path}")
    print(f"plan={plan_path}")
    print(f"qa={qa_path}")
    print(f"preview={png_path}")
    print(f"bottom_blank_ratio={layout.get('bottom_blank_ratio')} adjustments={len(adjustments)}")
    return 0 if qa["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
