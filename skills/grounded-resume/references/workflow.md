# Input and execution

Python 3.10+, `pdfplumber`, Tectonic and Poppler (`pdftoppm`) are needed for full PDF generation. PyYAML is used by the optional skill validator. Put the two external binaries on PATH; `--tectonic` can instead point to its executable. No credentials or model API keys are needed by the scripts.

The source is a UTF-8 JSON object. See [the bundled fictional profile](../examples/profile.json) for a complete example. Required keys: `contact` (name, location, phone, email, linkedin), `education` (institution, location, degree, dates, honors), `skills` (group-to-list mapping), and `items`. Each item has a unique stable `id`, `kind` (`role` or `project`), `name`, title/location/dates, and `bullets` with `source_text`. Optional fields: repository, visibility (`always`, `on-request`, `reference-only`), variants and technical_keywords. A `do_not_claim` list guides human/agent review; scripts do not enforce arbitrary semantic prohibitions. The built-in skill group labels are `Programming and data`, `Machine learning`, `Analytics and visualization`, and `Research computing`.

Keep the profile and original documents under an ignored `private/` directory. Review extraction before treating it as evidence. The index hashes the source and assigns bullet IDs; changing the source invalidates prior plans.

From the installed skill directory (the folder containing `SKILL.md`), create and activate a Python virtual environment, then run:

```sh
python -m pip install -r requirements.txt
python scripts/run_resume_pipeline.py --master examples/profile.json --jd examples/job.txt --company "Example Analytics" --role "Data Analyst" --jd-status local-regression --output-dir outputs/demo
```

For real use, supply your private profile and saved official JD. The default JD status is `unverified`; `verified` is a caller assertion and must follow actual source verification. The scripts do not fetch or authenticate the posting.

Edit only supported wording in the generated plan, then rebuild:

```sh
python scripts/run_resume_pipeline.py --master private/profile.json --plan outputs/role/PLAN_FILENAME.json --output-dir outputs/role
```

Use actual generated filenames. Paths printed by the pipeline identify each artifact. An index is created within the output directory. The default layout accepts 5–40% bottom whitespace so sparse candidates are not padded; the plan's layout limits can be adjusted when justified. Automatic fitting is bounded to 12 iterations. A failed fit remains failed. The layout check measures page size, pagination, margins and whitespace; it does not detect every collision.

After semantic review and viewing the exact PNG:

```sh
python scripts/finalize_resume_review.py --qa outputs/role/QA_FILENAME.json --reviewer "Reviewer name" --note "Describe actual checks"
python scripts/finalize_resume_review.py --qa outputs/role/QA_FILENAME.json --check
```

`application_ready` is a technical workflow flag requiring automated PASS, recorded visual review and caller-verified JD. It is not evidence of candidate approval, a guarantee of factual truth, ATS acceptance, or authorization to submit. `--check` verifies bundle integrity and recorded visual review; inspect `jd_status` separately. Any artifact or generator edit invalidates review. Keep bundles local because QA includes source paths.
