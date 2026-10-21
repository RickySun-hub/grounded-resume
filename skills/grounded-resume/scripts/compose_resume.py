#!/usr/bin/env python3
"""Compose an evidence-linked tailoring plan into the fixed LaTeX template."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from resume_lib import DEFAULT_INDEX, number_tokens, read_json


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def evidence_map(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {bullet["id"]: bullet for item in index["items"] for bullet in item["bullets"]}


def validate_plan_claims(plan: dict[str, Any], index: dict[str, Any]) -> None:
    sources = evidence_map(index)
    if plan.get("evidence_index_sha256") != index.get("source_sha256"):
        raise ValueError("Plan was built from a different master-profile evidence index")
    if plan["fixed"]["contact"] != index["contact"] or plan["fixed"]["education"] != index["education"]:
        raise ValueError("Fixed profile facts changed; update the reviewed source first")
    items = {item["id"]: item for item in index["items"]}
    supported_skills = {term for group in index["skills"].values() for term in group}
    if any(term not in supported_skills for group in plan["skill_groups"] for term in group["values"]):
        raise ValueError("Unsupported skill added to the plan")
    for entry in plan["entries"]:
        item = items[entry["item_id"]]
        for key in ("kind", "name", "title", "location", "dates", "repository"):
            if entry.get(key, "") != item.get(key, ""):
                raise ValueError(f"Entry metadata changed: {key}")
        allowed = {b["id"] for b in item["bullets"]}
        if any(b["source_id"] not in allowed for b in entry["bullets"]):
            raise ValueError("Evidence assigned to the wrong entry")
        for bullet in entry["bullets"]:
            source_id = bullet.get("source_id", "")
            if source_id not in sources:
                raise ValueError(f"Unknown evidence source_id: {source_id}")
            introduced = set(number_tokens(bullet["final_text"])) - set(sources[source_id]["numbers"])
            if introduced:
                raise ValueError(f"{source_id} introduces unsupported numeric tokens: {sorted(introduced)}")


def header_tex(contact: dict[str, str]) -> str:
    linkedin = contact["linkedin"].removeprefix("https://").removeprefix("http://")
    return (
        "\\begin{center}\n"
        f"  {{\\Huge \\scshape {latex_escape(contact['name'])}}} \\\\[3pt]\n"
        f"  \\small {latex_escape(contact['location'])} $|$ {latex_escape(contact['phone'])} $|$ "
        f"\\href{{mailto:{latex_escape(contact['email'])}}}{{{latex_escape(contact['email'])}}} $|$ "
        f"\\href{{https://{latex_escape(linkedin)}}}{{{latex_escape(linkedin)}}}\n"
        "\\end{center}"
    )


def education_tex(education: dict[str, str]) -> str:
    return (
        "\\resumeSubHeadingListStart\n"
        "  \\item\\begin{tabular*}{0.97\\textwidth}[t]{l@{\\extracolsep{\\fill}}r}\n"
        f"    \\textbf{{{latex_escape(education['institution'])}}} & {latex_escape(education.get('location', ''))} \\\\\n"
        f"    \\textit{{\\small {latex_escape(education['degree'])}}} & \\textit{{\\small {latex_escape(education['dates'])}}} \\\\\n"
        f"    \\small {latex_escape(education['honors'])} & \\\n"
        "  \\end{tabular*}\\vspace{-7pt}\n"
        "\\resumeSubHeadingListEnd"
    )


def skills_tex(groups: list[dict[str, Any]]) -> str:
    rows = []
    for group in groups:
        values = ", ".join(group["values"])
        rows.append(f"  \\textbf{{{latex_escape(group['label'])}}}{{: {latex_escape(values)}}} \\\\")
    return "\\begin{itemize}[leftmargin=0.15in,label={}]\n\\small{\\item{\n" + "\n".join(rows) + "\n}}\n\\end{itemize}"


def bullet_list_tex(bullets: list[dict[str, Any]]) -> str:
    lines = ["  \\resumeItemListStart"]
    lines.extend(f"    \\resumeItem{{{latex_escape(bullet['final_text'])}}}" for bullet in bullets)
    lines.append("  \\resumeItemListEnd")
    return "\n".join(lines)


def experience_tex(entries: list[dict[str, Any]]) -> str:
    lines = ["\\resumeSubHeadingListStart"]
    for entry in entries:
        lines.append(
            f"  \\resumeSubheading{{{latex_escape(entry['name'])}}}{{{latex_escape(entry.get('location', ''))}}}"
            f"{{{latex_escape(entry.get('title', ''))}}}{{{latex_escape(entry.get('dates', ''))}}}"
        )
        lines.append(bullet_list_tex(entry["bullets"]))
    lines.append("\\resumeSubHeadingListEnd")
    return "\n".join(lines)


def projects_tex(entries: list[dict[str, Any]]) -> str:
    lines = ["\\resumeSubHeadingListStart"]
    for entry in entries:
        heading = f"\\textbf{{{latex_escape(entry['name'])}}}"
        repository = entry.get("repository", "")
        if re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", repository):
            heading = r"\href{" + repository + "}{" + heading + "}"
        lines.append(f"  \\resumeProjectHeading{{{heading}}}{{{latex_escape(entry.get('dates', ''))}}}")
        lines.append(bullet_list_tex(entry["bullets"]))
    lines.append("\\resumeSubHeadingListEnd")
    return "\n".join(lines)


def apply_spacing_mode(template: str, mode: str) -> str:
    if mode != "expanded":
        return template
    replacements = {
        r"\titleformat{\section}{\vspace{-5pt}": r"\titleformat{\section}{\vspace{0pt}",
        r"[\titlerule\vspace{-6pt}]": r"[\titlerule\vspace{-1pt}]",
        r"\newcommand{\resumeItem}[1]{\item\small{#1\vspace{-2pt}}}":
            r"\newcommand{\resumeItem}[1]{\item\small{#1\vspace{2pt}}}",
        r"\newcommand{\resumeSubheading}[4]{\vspace{-1pt}\item":
            r"\newcommand{\resumeSubheading}[4]{\vspace{0pt}\item",
        r"\end{tabular*}\vspace{-7pt}}": r"\end{tabular*}\vspace{-2pt}}",
        r"\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}":
            r"\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{0pt}}",
    }
    for old, new in replacements.items():
        if old not in template:
            raise ValueError(f"Spacing-mode template token not found: {old}")
        template = template.replace(old, new)
    return template


def compose(plan: dict[str, Any], index: dict[str, Any], template: str) -> str:
    validate_plan_claims(plan, index)
    experiences = [entry for entry in plan["entries"] if entry["kind"] == "role" and entry["bullets"]]
    projects = [entry for entry in plan["entries"] if entry["kind"] == "project" and entry["bullets"]]
    if not experiences or not projects:
        raise ValueError("The fixed resume structure requires both experience and project entries")
    rendered = apply_spacing_mode(template, plan.get("layout", {}).get("spacing_mode", "normal"))
    rendered = rendered.replace("@@HEADER@@", header_tex(plan["fixed"]["contact"]))
    rendered = rendered.replace("@@EDUCATION@@", education_tex(plan["fixed"]["education"]))
    skills_gap = int(plan.get("layout", {}).get("skills_after_vspace_pt", 0))
    if not -8 <= skills_gap <= 0:
        raise ValueError("Skills spacing adjustment must be between -8 and 0 points")
    skills = skills_tex(plan["skill_groups"])
    if skills_gap:
        # A bare negative vspace before a section interacts with addvspace.
        # Set the heading's before-skip explicitly, then restore article defaults.
        before = max(4, 14 + skills_gap)
        rendered = rendered.replace(
            r"\section{Professional Experience}",
            r"\titlespacing*{\section}{0pt}{" + str(before) + r"pt}{2.3ex plus .2ex}" + "\n"
            + r"\section{Professional Experience}" + "\n"
            + r"\titlespacing*{\section}{0pt}{3.5ex plus 1ex minus .2ex}{2.3ex plus .2ex}",
        )
    rendered = rendered.replace("@@SKILLS@@", skills)
    rendered = rendered.replace("@@EXPERIENCE@@", experience_tex(experiences))
    rendered = rendered.replace("@@PROJECTS@@", projects_tex(projects))
    if re.search(r"@@[A-Z_]+@@", rendered):
        raise ValueError("Unresolved template placeholder")
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--template", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "resume-template.tex")
    parser.add_argument("--output-tex", type=Path, required=True)
    args = parser.parse_args()
    tex = compose(read_json(args.plan), read_json(args.evidence_index), args.template.read_text(encoding="utf-8"))
    args.output_tex.parent.mkdir(parents=True, exist_ok=True)
    args.output_tex.write_text(tex, encoding="utf-8")
    print(f"PASS: wrote {args.output_tex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
