# Grounded Resume privacy policy

Effective date: October 20, 2026

This policy covers the Grounded Resume skill and plugin published by RUI SUN through the [Grounded Resume repository](https://github.com/RickySun-hub/grounded-resume). It does not cover the separate ProofRound website or the AI application you use to run the skill.

## Information used by the skill

The workflow uses the source profile, resume and job description you choose to provide. These can include names, contact information, education and employment history. It creates local PDF, LaTeX, preview, plan and QA files. QA and plan files may contain personal information, source text and local file paths.

The bundled Python scripts do not contain analytics, an account service or a resume-upload endpoint. They read and write files in the execution environment selected by you and your AI host. Running these scripts does not itself send your resume to the publisher or ProofRound. The plugin does not automatically install an MCP connection or submit applications.

## AI hosts and external services

Your AI host may process messages, files and tool output on its servers under its own policies and settings. A hosted execution environment is not the same as your personal computer. Review your host's privacy settings before supplying sensitive material.

Dependency installers and Tectonic may contact package services to download required software or TeX resources. GitHub handles repository visits, downloads and issues under its policies. These services have their own data practices.

An optional ProofRound link may appear once in the chat after delivery. The skill does not open that link or send resume data to ProofRound automatically. If you choose to visit or use that website, its own policies apply.

## Retention and deletion

Generated files remain in the execution environment until you or that environment removes them. Delete source files, output bundles, previews and backups you no longer need. Deleting local files does not necessarily delete copies retained by an AI host or other service; use that service's controls for those copies. The bundled scripts have no publisher-managed resume database to delete from.

## Support and privacy questions

Use [repository issues](https://github.com/RickySun-hub/grounded-resume/issues) for general questions. Issues are public: do not post resumes, contact details, credentials or private QA files. If you choose to post information there, it is processed and retained through GitHub and visible to repository maintainers and the public. Use GitHub's controls or support for removal requests involving GitHub-hosted information.

Updates to this policy will be published on this page with a revised effective date.
