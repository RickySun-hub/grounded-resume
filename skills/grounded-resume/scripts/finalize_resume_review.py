#!/usr/bin/env python3
"""Record visual inspection of the exact validated PDF, or check reuse readiness."""
from __future__ import annotations
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from resume_lib import CONTENT_POLICY_VERSION, read_json, write_json

def check_bundle(qa: dict, require_review: bool = True) -> None:
    if qa.get('status') != 'PASS' or qa.get('content_policy_version') != CONTENT_POLICY_VERSION:
        raise ValueError('Bundle failed QA or uses an obsolete content policy; regenerate it')
    required = {'pdf', 'tex', 'plan', 'layout', 'preview_png'}
    if not required <= qa.get('artifact_sha256', {}).keys() or not qa.get('generator_sources') or not qa.get('source_files'):
        raise ValueError('Bundle is missing artifact or generator provenance; regenerate it')
    for key in required:
        path = Path(qa['artifacts'][key])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != qa['artifact_sha256'][key]:
            raise ValueError(f'Artifact changed or is missing: {key}')
    for filename, expected in (qa['generator_sources'] | qa['source_files']).items():
        path = Path(filename)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Generator, template or canonical source changed; regenerate the bundle')
    if require_review:
        review = qa.get('visual_review', {})
        if review.get('status') != 'PASS' or review.get('pdf_sha256') != qa['artifact_sha256']['pdf']:
            raise ValueError('Current PDF has not passed recorded visual inspection')

def finalize(qa_path: Path, reviewer: str, note: str) -> dict:
    qa = read_json(qa_path)
    check_bundle(qa, require_review=False)
    if not reviewer.strip() or not note.strip():
        raise ValueError('Record who inspected the PNG and what was checked')
    qa['visual_review'] = {'status': 'PASS', 'reviewer': reviewer, 'note': note,
        'reviewed_at': datetime.now(timezone.utc).isoformat(), 'pdf_sha256': qa['artifact_sha256']['pdf']}
    qa['application_ready'] = qa.get('jd_status', 'unverified') == 'verified'
    write_json(qa_path, qa)
    return qa

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qa', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--reviewer')
    parser.add_argument('--note')
    args = parser.parse_args()
    if args.check:
        check_bundle(read_json(args.qa));print('PASS: intact bundle, current generator, recorded visual inspection')
    else:
        if not args.reviewer or not args.note:parser.error('--reviewer and --note are required after visually inspecting the current PNG')
        qa = finalize(args.qa, args.reviewer, args.note);print(f"PASS: visual review recorded; application_ready={qa['application_ready']}")
if __name__ == '__main__':main()
