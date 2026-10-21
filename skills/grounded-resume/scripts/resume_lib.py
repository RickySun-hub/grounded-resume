#!/usr/bin/env python3
"""Shared parsing and scoring helpers for the Grounded Resume pipeline."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_MASTER = Path("private/profile.json")
DEFAULT_INDEX = Path("outputs/evidence-index.json")

CONTENT_POLICY_VERSION = "2.0"
PROJECT_MIN_BULLETS = 2
PROJECT_TARGET_BULLETS = 3
PROJECT_MAX_BULLETS = 4
MAX_TOTAL_BULLETS = 15

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "our", "that", "the", "their", "this", "to",
    "using", "we", "will", "with", "you", "your", "years", "experience", "role",
}

COMMON_JD_TERMS = [
    "Python", "SQL", "pandas", "NumPy", "SciPy", "scikit-learn", "PyTorch",
    "TensorFlow", "R", "MATLAB", "Git", "Jupyter", "machine learning",
    "deep learning", "generative modeling", "VAE", "LLM", "NLP", "computer vision",
    "agentic AI", "prompt engineering", "RAG", "vector databases", "RESTful APIs",
    "JSON", "software testing", "CI/CD",
    "LightGBM", "uplift modeling", "retention", "cohort analysis", "conversion",
    "regression", "classification", "cross-validation", "feature engineering",
    "model evaluation", "experiment design", "A/B testing", "statistics",
    "data pipelines", "ETL", "data quality", "HDF5", "Linux", "SLURM", "CUDA",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Spark", "Tableau", "Excel",
    "Streamlit", "dashboarding", "KPI reporting", "visualization", "stakeholders",
]

EVIDENCE_ALIASES = {
    "data quality": ["data quality", "validated", "validation", "qc", "audit", "clean data", "exception"],
    "data pipelines": ["pipeline", "workflow", "etl", "consolidate", "hdf5", "manifest"],
    "etl": ["etl", "pipeline", "consolidate", "migrate"],
    "model evaluation": ["evaluated", "benchmark", "validation", "cross validation", "metrics"],
    "visualization": ["visualization", "dashboard", "plot", "streamlit", "tableau", "matplotlib"],
    "dashboarding": ["dashboard", "streamlit", "reporting"],
    "software testing": ["test", "testing", "validated", "guards", "audit"],
    "experiment design": ["experiment", "ablation", "matched budget", "controlled"],
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("–", "-").replace("—", "-").replace("/", " ")
    return re.sub(r"[^a-z0-9+#]+", " ", text).strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", normalize(text)).strip("-")
    return slug[:72] or "item"


def number_tokens(text: str) -> list[str]:
    raw = re.findall(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?%?", text, re.I)
    return sorted({token.replace(",", "").lower() for token in raw})


def word_tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z][a-z0-9+#.]{1,}", normalize(text))
        if token not in STOPWORDS
    }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _next_nonempty(lines: list[str], start: int, end: int) -> str:
    for index in range(start, end):
        value = lines[index].strip()
        if value:
            return value
    return ""


def _value_after(lines: list[str], label: str, start: int, end: int) -> str:
    wanted = normalize(label)
    for index in range(start, end):
        current = lines[index].strip()
        if normalize(current.rstrip(":")) == wanted:
            return _next_nonempty(lines, index + 1, end)
        if normalize(current).startswith(wanted + " "):
            return current.split(":", 1)[-1].strip()
    return ""


def _split_terms(text: str) -> list[str]:
    return [value.strip().rstrip(".") for value in re.split(r",\s*", text) if value.strip()]


def _terms_in(text: str, candidates: Iterable[str]) -> list[str]:
    haystack = f" {normalize(text)} "
    found: list[str] = []
    for term in candidates:
        needle = normalize(term)
        if needle == "r":
            r_supported = any(pattern in haystack for pattern in (" python or r ", " r or python ", " using r ", " with r ", " r programming ", " r language "))
            if r_supported:
                found.append(term)
        elif needle and (f" {needle} " in haystack or (len(needle) >= 3 and f" {needle}s " in haystack)):
            found.append(term)
    return found


def _unique_normalized(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = normalize(value)
        if key and key not in seen:
            result.append(value)
            seen.add(key)
    return result


def build_evidence_index(master_path: Path = DEFAULT_MASTER) -> dict[str, Any]:
    """Build provenance from a user-reviewed structured source, never from the JD."""
    raw = master_path.read_bytes()
    profile = json.loads(raw)
    for key in ("contact", "education", "skills", "items"):
        if key not in profile:
            raise ValueError(f"Profile missing {key}")
    ids = set()
    for item in profile["items"]:
        if item["kind"] not in ("role", "project") or item["id"] in ids:
            raise ValueError("Items need unique IDs and kind role or project")
        ids.add(item["id"])
        for key, default in (("visibility", "always"), ("variants", []), ("technical_keywords", []),
                             ("do_not_claim", []), ("title", ""), ("location", ""), ("dates", ""), ("repository", "")):
            item.setdefault(key, default)
        for n, bullet in enumerate(item["bullets"], 1):
            if not bullet.get("source_text", "").strip():
                raise ValueError("Empty source bullet")
            bullet["id"] = f"{item['id']}-b{n:02d}"
            bullet["numbers"] = number_tokens(bullet["source_text"])
            bullet["keywords"] = _terms_in(bullet["source_text"], COMMON_JD_TERMS)
            bullet["category"] = bullet.get("category", "general")
            bullet["line_cost"] = max(1, math.ceil(len(bullet["source_text"]) / 105))
    profile["source_sha256"] = hashlib.sha256(raw).hexdigest()
    return profile


def infer_variant(role: str, jd: str) -> str:
    def classify(text: str) -> str | None:
        if any(term in text for term in ("research engineer", "research scientist")):
            return "research_engineer"
        if "applied scientist" in text:
            return "applied_scientist"
        if any(term in text for term in ("machine learning engineer", "ml engineer", "ai engineer")):
            return "ml_engineer"
        if "data engineer" in text:
            return "data_engineering"
        if "data scientist" in text:
            return "data_science"
        if any(term in text for term in ("data analyst", "business analyst", "product analyst", "analytics")):
            return "data_analyst"
        return None
    return classify(normalize(role)) or classify(normalize(jd[:2000])) or "data_science"


def _jd_buckets(jd: str) -> tuple[str, str, str]:
    required: list[str] = []
    preferred: list[str] = []
    other: list[str] = []
    bucket = other
    jd = re.sub(r"(?i)\b(Required Qualifications|Minimum Qualifications|Preferred Qualifications|Desired Qualifications|Responsibilities|Requirements)\b", r"\n\1\n", jd)
    for line in jd.splitlines():
        norm = normalize(line)
        if any(term in norm for term in ("preferred qualifications", "desired qualifications", "nice to have", "bonus")):
            bucket = preferred
        elif any(term in norm for term in ("minimum qualifications", "required qualifications", "requirements", "what you need", "must have")):
            bucket = required
        elif norm == "responsibilities":
            bucket = other
        if any(term in norm for term in ("required", "must have", "minimum of")):
            required.append(line)
        elif "preferred" in norm:
            preferred.append(line)
        else:
            bucket.append(line)
    return "\n".join(required), "\n".join(preferred), "\n".join(other)


def _supported_terms(index: dict[str, Any]) -> list[str]:
    values = [term for group in index["skills"].values() for term in group]
    items = [item for item in index["items"] if item["visibility"] != "reference-only"]
    corpus = " ".join(b["source_text"] for item in items for b in item["bullets"] if "pending" not in normalize(b["source_text"]))
    # Plans, cautions and do-not-claim lists are not positive skill evidence.
    for item in items:
        values.extend(term for term in item["technical_keywords"] if _terms_in(corpus, [term]))
    values.extend(term for term in COMMON_JD_TERMS if _terms_in(corpus, [term]))
    return list(dict.fromkeys(values))


def analyze_jd(jd: str, index: dict[str, Any]) -> dict[str, list[str]]:
    supported = _supported_terms(index)
    required_text, preferred_text, other_text = _jd_buckets(jd)
    required = _unique_normalized(_terms_in(required_text, supported))
    required_norm = {normalize(term) for term in required}
    preferred = _unique_normalized(term for term in _terms_in(preferred_text, supported) if normalize(term) not in required_norm)
    claimed_norm = required_norm | {normalize(term) for term in preferred}
    mentioned = _unique_normalized(term for term in _terms_in(jd, supported) if normalize(term) not in claimed_norm)
    supported_norm = {normalize(term) for term in supported}
    def is_supported(term: str) -> bool:
        term_norm = normalize(term)
        return term_norm in supported_norm or any(f" {term_norm} " in f" {actual} " for actual in supported_norm)

    unsupported = [term for term in COMMON_JD_TERMS if _terms_in(jd, [term]) and not is_supported(term)]
    return {
        "required_supported": required,
        "preferred_supported": preferred,
        "mentioned_supported": mentioned,
        "missing_terms": unsupported,
    }


def score_bullet(
    bullet: dict[str, Any], item: dict[str, Any], variant: str,
    jd_analysis: dict[str, list[str]], jd_tokens: set[str],
) -> tuple[float, list[str]]:
    text = bullet["source_text"]
    required = _terms_in(text, jd_analysis["required_supported"])
    preferred = _terms_in(text, jd_analysis["preferred_supported"])
    mentioned = _terms_in(text, jd_analysis["mentioned_supported"])
    text_norm = normalize(text)
    for term in jd_analysis["required_supported"]:
        if term not in required and any(alias in text_norm for alias in EVIDENCE_ALIASES.get(normalize(term), [])):
            required.append(term)
    for term in jd_analysis["preferred_supported"]:
        if term not in preferred and any(alias in text_norm for alias in EVIDENCE_ALIASES.get(normalize(term), [])):
            preferred.append(term)
    for term in jd_analysis["mentioned_supported"]:
        if term not in mentioned and any(alias in text_norm for alias in EVIDENCE_ALIASES.get(normalize(term), [])):
            mentioned.append(term)
    matched = list(dict.fromkeys(required + preferred + mentioned))
    lexical = min(8, len(word_tokens(text) & jd_tokens)) * 0.35
    score = 10 * len(required) + 6 * len(preferred) + 3 * len(mentioned) + lexical
    if variant in item["variants"]:
        score += 4
    elif item["visibility"] == "always":
        score += 1
    if bullet["numbers"]:
        score += 1.5
    if any(token in normalize(text) for token in ("validated", "evaluated", "benchmarked", "built", "engineered", "analyzed", "generated")):
        score += 1
    if variant in ("data_analyst", "business_analytics", "data_science"):
        if normalize(bullet.get("category", "")) == "verified engineering evidence":
            score -= 80  # Supporting implementation detail must not replace analytical findings.
        if any(term in text_norm for term in ("conversion", "repeat activity", "held out", "baseline", "wape", "decomposed", "observed return", "quartiles")):
            score += 8
    return round(score, 2), matched


def select_skill_groups(index: dict[str, Any], jd_analysis: dict[str, list[str]], variant: str) -> list[dict[str, Any]]:
    jd_terms = jd_analysis["required_supported"] + jd_analysis["preferred_supported"] + jd_analysis["mentioned_supported"]
    defaults = {
        "ml_engineer": ["Python", "PyTorch", "NumPy", "pandas", "Git", "Linux", "SLURM", "CUDA", "generative modeling", "VAE / conditional VAE / generative modeling", "model evaluation", "HDF5 / h5py datasets"],
        "research_engineer": ["Python", "PyTorch", "SciPy", "NumPy", "MATLAB", "Linux", "SLURM", "experiment design", "model evaluation", "reproducible benchmarking"],
        "applied_scientist": ["Python", "PyTorch", "SciPy", "NumPy", "generative modeling", "experiment design", "model evaluation", "cross-validation"],
        "data_engineering": ["Python", "SQL", "pandas", "DuckDB", "HDF5", "h5py", "Linux", "SLURM", "ETL", "data validation", "data provenance", "reproducibility"],
        "data_analyst": ["Python", "SQL", "pandas", "Excel", "Tableau", "KPI reporting", "anomaly / exception detection", "Streamlit", "scikit-learn"],
        "data_science": ["Python", "SQL", "pandas", "NumPy", "scikit-learn", "PyTorch", "regression", "classification", "cross-validation", "feature engineering", "model evaluation", "experiment design"],
    }
    if variant == "ai_engineer":
        variant = "ml_engineer"
    supported_groups = index["skills"]
    selected: list[str] = []
    for desired in jd_terms + defaults.get(variant, defaults["data_science"]):
        for values in supported_groups.values():
            for actual in values:
                desired_norm = normalize(desired)
                actual_norm = normalize(actual)
                contains_phrase = " " in desired_norm and f" {desired_norm} " in f" {actual_norm} "
                if desired_norm == actual_norm or contains_phrase:
                    if actual not in selected:
                        selected.append(actual)
    group_map = [
        ("Languages & Data", ["Programming and data"]),
        ("Machine Learning", ["Machine learning"]),
        ("Analytics & Computing", ["Analytics and visualization", "Research computing"]),
    ]
    result: list[dict[str, Any]] = []
    for label, source_labels in group_map:
        allowed = [term for source in source_labels for term in supported_groups.get(source, [])]
        values = [term for term in selected if term in allowed]
        if values:
            result.append({"label": label, "values": values[:10]})
    return result


def prepare_plan(
    jd: str, index: dict[str, Any], company: str, role: str, req_id: str,
    variant: str = "auto", jd_status: str = "unverified", location: str | None = None,
) -> dict[str, Any]:
    if variant == "auto":
        variant = infer_variant(role, jd)
    jd_analysis = analyze_jd(jd, index)
    jd_tokens = word_tokens(jd)
    # Generic stack terms alone can bury a newly completed, directly relevant
    # project. Weight the specialization in the exact role title, after removing
    # generic job-family/seniority words. Eligibility remains evidence-gated.
    generic_role_words = set('data analyst analytics scientist science engineer engineering senior junior jr sr associate graduate new grad entry level machine learning applied research global platform start'.split())
    role_focus = {t for t in word_tokens(role) - generic_role_words if not t.isdigit()}
    candidates: list[dict[str, Any]] = []
    item_lookup = {item["id"]: item for item in index["items"]}
    for item in index["items"]:
        if item["visibility"] == "reference-only":
            continue
        eligible = item["visibility"] == "always" or variant in item["variants"]
        if not eligible and item["visibility"] == "on-request":
            eligible = bool(word_tokens(" ".join(item["technical_keywords"])) & jd_tokens)
        if not eligible:
            continue
        for bullet in item["bullets"]:
            if "pending" in normalize(bullet["source_text"]):
                continue
            score, matched = score_bullet(bullet, item, variant, jd_analysis, jd_tokens)
            focus_matches = sorted(role_focus & word_tokens(item['name'])) if item['kind'] == 'project' else []
            score += min(30, 15 * len(focus_matches))
            candidates.append({
                "item_id": item["id"], "item_kind": item["kind"], "source_id": bullet["id"],
                "source_text": bullet["source_text"], "final_text": bullet["source_text"],
                "score": score, "matched_jd_terms": matched, "line_cost": bullet["line_cost"],
                "category": bullet.get("category", "general"), "selected": False,
                "matched_role_focus": focus_matches,
            })

    def item_score(item_id: str) -> float:
        scores = sorted((c["score"] for c in candidates if c["item_id"] == item_id), reverse=True)
        return sum(scores[:3])

    role_items = [item for item in index["items"] if item["kind"] == "role" and any(c["item_id"] == item["id"] for c in candidates)]
    project_items = [item for item in index["items"] if item["kind"] == "project" and any(c["item_id"] == item["id"] for c in candidates)]
    role_items.sort(key=lambda item: item_score(item["id"]), reverse=True)
    project_items.sort(key=lambda item: item_score(item["id"]), reverse=True)
    selected_roles = role_items[:3]
    excluded_item_ids: set[str] = set()
    project_items = [item for item in project_items if sum(c["item_id"] == item["id"] for c in candidates) >= PROJECT_MIN_BULLETS]
    selected_projects = project_items[:2]
    target_counts = {item["id"]: 3 for item in selected_roles}
    max_counts = {item["id"]: 4 for item in selected_roles}
    for project_pos, item in enumerate(selected_projects):
        target_counts[item["id"]] = PROJECT_TARGET_BULLETS
        max_counts[item["id"]] = PROJECT_MAX_BULLETS

    entries: list[dict[str, Any]] = []
    for item in selected_roles + selected_projects:
        ranked = sorted((c for c in candidates if c["item_id"] == item["id"]), key=lambda c: c["score"], reverse=True)
        chosen = sorted(ranked[: target_counts[item["id"]]], key=lambda c:c["source_id"])
        for candidate in chosen:
            candidate["selected"] = True
        entries.append({
            "item_id": item["id"], "kind": item["kind"], "name": item["name"],
            "title": item["title"], "location": item["location"], "dates": item["dates"],
            "repository": item.get("repository", ""),
            "bullets": chosen, "min_bullets": 2, "target_bullets": target_counts[item["id"]], "max_bullets": max_counts[item["id"]],
        })

    candidate_pool = sorted(
        (c for c in candidates if not c["selected"] and c["item_id"] not in excluded_item_ids),
        key=lambda c: c["score"],
        reverse=True,
    )
    contact = dict(index["contact"])
    if location:
        contact["location"] = location
    return {
        "schema_version": "1.0",
        "target": {"company": company, "role": role, "req_id": req_id, "variant": variant},
        "jd": {"status": jd_status, "sha256": hashlib.sha256(jd.encode("utf-8")).hexdigest(), "analysis": jd_analysis},
        "fixed": {"contact": contact, "education": index["education"]},
        "skill_groups": select_skill_groups(index, jd_analysis, variant),
        "entries": entries,
        "candidate_pool": candidate_pool,
        "content_policy_version": CONTENT_POLICY_VERSION,
        "layout": {"target_pages": 1, "min_bottom_blank_ratio": 0.05, "max_bottom_blank_ratio": 0.40, "preferred_bottom_blank_ratio": [0.05, 0.08]},
        "evidence_index_sha256": index["source_sha256"],
    }


def item_from_index(index: dict[str, Any], item_id: str) -> dict[str, Any]:
    return next(item for item in index["items"] if item["id"] == item_id)
