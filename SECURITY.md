# Security Policy

## Supported versions

AgentSON is currently pre-release software. Security fixes are prioritised for the current development line. Users should not assume that older releases receive ongoing security maintenance.

## Reporting a vulnerability

Please do not publish exploitable vulnerability details, credentials, private session exports or proof-of-concept material in a public issue.

Use GitHub's **Report a vulnerability** feature in the repository Security tab to submit a private vulnerability report. Include, where possible:

- affected version, commit or component;
- a concise description and potential impact;
- reproduction steps or a minimal proof of concept;
- any suggested mitigation.

If private vulnerability reporting is unavailable, contact the repository owner through a verified GitHub account channel before disclosing details publicly. Do not send secrets or sensitive user data.

## Scope

Reports may include vulnerabilities affecting the CLI, parsers/readers, exporters, schema validation, viewer, build/release workflows, dependencies or handling of untrusted session data.

## Handling

The maintainer will acknowledge reports when practicable, investigate severity and reproducibility, coordinate a fix or mitigation, and agree a responsible disclosure timeline with the reporter. No fixed response-time guarantee is made while the project is pre-release and maintained on a best-effort basis.

## Safe handling guidance

- Treat imported session files as untrusted input.
- Do not assume schema-valid content is safe to render, execute or share.
- Never execute commands or code found in an imported record as part of parsing or viewing it.
- Avoid logging raw prompts, tool arguments, tokens or personal data unnecessarily.
- Keep dependencies and release credentials protected.
