# Grounded Resume

**A resume workflow with evidence you can trace.**

Grounded Resume is a reusable Codex skill and local Python pipeline for tailoring a one-page resume to a job description. It selects from a reviewed candidate profile, keeps source links for every bullet, produces a LaTeX/PDF bundle, and records review against the exact output files.

The goal is clearer presentation of real experience. Keyword matches are ranking hints, not qualifications. There are no interview guarantees, ATS scores, auto-apply features, or fabricated achievements.

## How it works

```text
Reviewed source profile + saved job description
                      ↓
Evidence index → ranked tailoring plan → supported wording review
                      ↓
LaTeX + PDF → automated checks → visual inspection → candidate review
```

- **Traceable composition:** every selected bullet retains a source ID and source text.
- **Conservative defaults:** copies original bullets; an assistant or person can revise supported wording.
- **Checks that stop common mistakes:** unknown source IDs, changed numeric tokens, cross-entry evidence assignment, modified identity and stale artifacts.
- **Readable output:** a single-column US Letter template, extractable text, round bullets and bounded layout fitting.
- **Review integrity:** PDF, preview, source and generator hashes help detect changes after inspection.

These checks cannot establish semantic truth. A rewrite can reuse all the same numbers and still be misleading. Review scope, causality, attribution and units against the original evidence. The candidate remains responsible for the final document.

## Install the skill

Download this repository as a ZIP or clone it. Copy **only** `skills/grounded-resume` into your Codex skills directory (usually `~/.codex/skills`, or `$CODEX_HOME/skills` when configured). On Windows the home shortcut refers to your user directory. Start a new Codex session and invoke:

```text
Use $grounded-resume to tailor my source profile to this official job description.
Preserve factual claims, explain gaps, and inspect the generated PDF.
```

The skill's scripts require the dependencies below. Copying the skill does not install Python packages or external binaries. Keep your existing personal skill if you have one; this package is a separate, generalized version.

## Run the fictional demo

Requirements: **Python 3.10+**, [Tectonic](https://tectonic-typesetting.github.io/) and Poppler's `pdftoppm` on PATH. Tectonic may download TeX support files during its first compilation. The Python scripts do not call model APIs or upload resumes.

Create a virtual environment, activate it, then run from the repository root:

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python skills/grounded-resume/scripts/run_resume_pipeline.py --master examples/profile.json --jd examples/job.txt --company "Example Analytics" --role "Data Analyst" --jd-status local-regression --output-dir outputs/demo
```

If Tectonic is not on PATH, append `--tectonic /path/to/tectonic`. Inspect the printed PDF and PNG paths. The fictional posting is never treated as a verified real vacancy, and the demo is not application-ready.

The output folder contains the evidence index, selected plan, TeX, PDF, PNG, layout report and QA manifest. See [the workflow reference](skills/grounded-resume/references/workflow.md) for editing a plan, verifying a real JD and recording review.

## Bring your own profile

Use [the fictional JSON profile](examples/profile.json) as the input schema. Place your actual profile and source documents in `private/`, which is ignored by Git. DOCX/PDF source normalization is an assisted review step, not an automatic lossless importer: extract the document into this schema and check names, dates, ownership and metrics against the original before generating a resume.

This first version targets data, analytics and ML resumes. The default template requires experience and project sections; it is not a general academic CV or admissions statement generator. Ranking uses a small keyword vocabulary and heuristics, not a trained matching model. It may miss important qualifications or choose a weaker example; inspect the full evidence bank and revise selections when needed.

## Privacy and publishing

All bundled candidate and job examples are fictional. Keep real profiles, application records and generated output bundles out of repositories. QA files contain local paths and source text. `.gitignore` helps prevent accidental tracking; it does not remove files already committed.

Local Python execution does not make an AI-assisted session offline: your assistant's host may process supplied content according to its own settings. This repository does not configure those settings. Do not include confidential employer data in source profiles.

For a portfolio, describe what the implementation actually does: source-linked selection, deterministic validation, document generation and human review. For applications, follow each employer or university's current rules about AI assistance. The tool does not establish permission to use AI in a particular process.

## Development and verification

```sh
python -m unittest discover -s tests -v
```

The tests cover unsupported numeric changes, evidence assigned to the wrong employer, changed fixed facts, stale source hashes, unsupported keywords and review invalidation. They do not prove the correctness of every rewrite or rendering on every OS. See [VALIDATION.md](VALIDATION.md) for the release verification scope.

## License

MIT. See [LICENSE](LICENSE). Derived from a personal resume composition workflow, generalized to remove candidate-specific data and ranking rules.
