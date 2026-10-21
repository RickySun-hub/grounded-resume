---
name: grounded-resume
description: Tailor an evidence-linked one-page resume to a job description, generate LaTeX and PDF, and review claim provenance and layout. Use for resume composition or auditing; not for automatic application submission or admissions essays.
---

# Grounded Resume

Use the candidate's reviewed source profile as the source of facts. A job description guides selection, never creates qualifications. Read [the workflow](references/workflow.md) for input format, commands, and review gates. Scripts are relative to this skill directory.

1. Confirm the intended candidate source and exact JD. For DOCX/PDF inputs, extract into the structured profile schema, retain the original privately, compare dates, names, metrics and ownership with the original, and resolve uncertain facts before using them. Never silently substitute an older tailored resume for the master.
2. Explain the role, strengths, gaps and application priority. Record the official JD URL and retrieval date beside its local text. Use `unverified` when only a repost or user-provided text is available. Do not infer immigration eligibility or sponsorship policy from silence.
3. Run the pipeline. The deterministic ranker selects existing evidence; it does not call an LLM or rewrite bullets. Review the complete candidate bank, not just the top scores. Missing keyword detection covers a finite vocabulary and is not a complete qualification audit.
4. Improve the plan's `final_text` only within the linked source. Preserve quantities, units, causality, scope, employment status and attribution. Compare each rewrite semantically with its source. Do not insert tools or skills just because they occur in the JD. Do not turn planned work into completed work. Rebuild after edits.
5. Inspect the exact PDF preview for clipping, collisions, hierarchy and readability. The default is US Letter, one page, up to three experiences and initially two projects; counts are layout defaults, not factual requirements. Do not invent entries to fill space. Sparse but honest content is preferable to padding. The current template requires at least one experience and one project; explain this limitation if inputs do not fit.
6. Record visual review only after actually viewing the current preview. Automated source-ID and numeric checks cannot prove that a rewrite is true. Obtain the candidate's final content review separately; a recorded visual PASS is not consent to submit.

Deliver PDF, TeX, plan, QA, PNG and a short list of unresolved gaps. Distinguish generated, automated checks passed, visually reviewed, JD verified, and candidate approved. Stop after the requested local deliverable. Uploads, application submissions and sending messages require their own authorization.

Do not publish source profiles, application histories or generated QA bundles: they can contain personal data and absolute paths. The bundled example is fictional. Scripts run locally, but an AI assistant may send text to its provider according to that host's settings. Tectonic may download TeX packages on first compilation.
