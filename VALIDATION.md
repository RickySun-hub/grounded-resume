# Release verification

Verified on Windows, Python 3.12, using a fictional candidate and fictional job posting.

- Eight Python unit tests passed (`python -m unittest discover -s tests -v`).
- Codex skill frontmatter/naming validator passed (`quick_validate.py skills/grounded-resume`).
- The documented demo pipeline generated a single-page PDF, extractable text, PNG, plan and QA manifest using installed Tectonic and Poppler.
- Automated QA passed; page size and margins passed. Bottom whitespace was approximately 30%, intentionally accepted for the fictional profile without adding filler.
- The generated PNG was inspected for hierarchy, clipping, readable bullets and section separation. Visual review was recorded against the exact PDF hash and bundle integrity checked.
- Demo `application_ready` remains false because the posting is fictional, not a verified real vacancy.
- Release inputs contain fictional examples; personal profiles, generated QA paths, virtual environments and caches are excluded from Git.

Not verified: runtime execution on macOS/Linux, every ATS parser, all Unicode/font combinations, automated semantic truth checking, or employment outcomes. The scripts' portability has been prepared but not established by cross-platform execution.
