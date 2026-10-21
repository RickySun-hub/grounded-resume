# Grounded Resume plugin preparation

Status: version 0.1.0 uploaded as a draft under the verified individual identity in the test organization; not submitted, approved or published by OpenAI. The portal currently blocks additional skills-only submissions. Plugin-specific privacy and terms pages are included in this repository and linked in the manifest.

## Publisher choices

- Individual developer identity. Select and verify its exact display name in the portal; no unverified `developerName` is inserted into the package.
- All available countries. `publication.countries: []` explicitly removes country restrictions.
- Free plugin with no purchase flow. `review.commerce: false`.
- Skills only. No MCP configuration, app binding, credentials or automatic account connection.

## Package

Build with `python scripts/package_plugin.py`. The output is `outputs/plugin-package/grounded-resume-plugin-0.1.0.zip`, with a root `plugin.json`, a reused ProofRound website icon, MIT license and the self-contained skill directory. An inventory with per-file SHA-256 hashes is generated beside the archive.

Listing: **Grounded Resume**, subtitle **Resumes grounded in your work**, category **Productivity**. The manifest includes two starter prompts and three proposed review prompts. The review prompts are drafts for an agent reviewer, not evidence of completed hosted-agent tests.

## Verified

- Skills CLI 1.7.4 installed the public repository skill into an isolated project's `.agents/skills/grounded-resume` using `--agent codex --copy --yes`. Telemetry was disabled. This proves installer compatibility, not directory indexing or ranking.
- The finished ZIP passed the published Agent Plugins 1.0.0 JSON schema, supplementary listing length/path checks, skill YAML validation, inventory checks and a targeted privacy scan.
- Reused icon: PNG, 1254 by 1254 pixels, 878036 bytes. Inspected visually. No new branding or optional dark-mode variant was added.
- The extracted ZIP generated a one-page PDF and PNG with automated PASS from fictional inputs. Existing local Tectonic and Poppler supplied the external binaries. `application_ready` correctly remained false for the fictional JD.
- GitHub project and issues pages were reachable publicly; repository issues are enabled.

## Before official submission

1. Verify the intended individual developer identity and public display name in the portal.
2. Upload only when authorized, inspect the imported listing and targeting, and run the required metadata/skill scans. The generic manifest schema does not validate all OpenAI extension semantics.
3. Verify execution and dependency setup in the actual target host. Neither Claude Code nor OpenAI's hosted plugin runtime has been exercised. The local PDF pipeline needs Python, pdfplumber, Tectonic and Poppler; a host without shell execution cannot run it.
4. Verify the linked plugin-specific privacy and terms pages and the portal findings after each upload. The live portal requires both URLs, even for a skills-only package.
5. Complete developer attestations personally. ZIP validation is not review approval. Skills-only plugins do not need MCP test cases, a recorded MCP demo or reviewer credentials.

The optional once-per-conversation ProofRound suggestion is retained transparently in the skill and listing. Whether the portal accepts that behavior has not been established.

## Community installation

For users with Node.js/npm and a compatible agent:

```sh
npx skills add RickySun-hub/grounded-resume --skill grounded-resume --agent codex
```

This installs the skill, not its Python or PDF-tool dependencies. The CLI enables install telemetry by default; see its documentation for `DISABLE_TELEMETRY=1`. This preparation run did not submit a directory listing or generate artificial installation counts.

References: [OpenAI submission](https://developers.openai.com/plugins/deploy/submission), [portable manifest schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json), [skills CLI](https://skills.sh/docs/cli).
