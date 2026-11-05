# Reader and Adapter Inventory

Readers extract source sessions and map them into AgentSON. A reader is not automatically an importer, exporter, reconstruction engine or resume adapter.

## Repository inventory (master snapshot, 05 November 2026)

The repository contains the following reader modules. This is a source-tree inventory, not a claim that every module is production-ready or that tests have passed in this documentation change.

| Source | Module | Dedicated test module present in repository |
|---|---|---|
| Aider | `readers/aider.py` | Yes: `tests/test_aider.py` |
| Antigravity | `readers/antigravity.py` | Yes: `tests/test_antigravity.py` |
| Chrome DevTools | `readers/chrome_devtools.py` | Yes: `tests/test_chrome_devtools.py` |
| Claude Code | `readers/claude_code.py` | Yes: `tests/test_claude_code.py` |
| Cline | `readers/cline.py` | Yes: `tests/test_cline.py` |
| GitHub Copilot Chat | `readers/copilot_chat.py` | Yes: `tests/test_copilot_chat.py` |
| Cursor | `readers/cursor.py` | Yes: `tests/test_cursor.py` |
| Gemini | `readers/gemini.py` | No dedicated `test_gemini.py` found in this snapshot |
| FreeStyle Libre | `readers/libre.py` | No dedicated `test_libre.py` found in this snapshot |
| MiniMax | `readers/minimax.py` | Yes: `tests/test_minimax.py` |
| OpenCode | `readers/opencode.py` | Yes: `tests/test_opencode.py` |
| VibeEdge | `readers/vibeedge.py` | No dedicated `test_vibeedge.py` found in this snapshot |

The source tree also contains importers for A2A, AGNTCY, ChatGPT and MCP under `importers/`. These are importer integrations and should not be counted as source readers without a clearly defined inventory rule.

## Cross-harness conformance

The executable baseline, conformance levels, producer/consumer test requirements and known gaps are maintained in the [Cross-Harness Conformance Test Plan](../architecture/conformance-test-plan.md). Do not infer interoperability from the presence of two reader modules or two independent reader test files.

## Capability labels

Use these labels per adapter and per operation:

- **Implemented and tested:** implementation exists and relevant tests have run and passed against identified fixtures.
- **Implemented, not yet verified:** implementation exists but current test evidence is missing or has not been run.
- **Experimental:** available for evaluation; behaviour or interface may change.
- **Designed:** contract or plan exists; implementation is not complete.
- **Planned:** accepted roadmap item, not implemented.
- **Unsupported:** deliberately not supported.

A file existing in the repository is not sufficient evidence for the label "working". Record the tested source version, fixture provenance, test command and known gaps.

## Adapter capability dimensions

Track these separately:

1. Capture/read source data.
2. Export a canonical v1.2 archive.
3. Import a canonical v1.2 archive.
4. Validate envelope and entries.
5. Preserve source ordering and correlation.
6. Preserve provenance and report semantic loss.
7. Inspect/render without executing imported content.
8. Reconstruct recorded context.
9. Resume from a compatible checkpoint.

Do not infer capabilities 3–9 from capability 1.

## Adding a reader

1. Inspect the source format and document its version/limitations.
2. Implement a source-specific reader behind a stable adapter boundary.
3. Preserve source identifiers, timestamps and ordering where available.
4. Map into the canonical v1.2 envelope and event vocabulary.
5. Record preserved, normalised, extension, unavailable, redacted and unsupported information.
6. Add sanitised fixtures derived from real exports where permission allows; label synthetic fixtures honestly.
7. Test malformed, incomplete, unknown and version-skewed source records.
8. Update this inventory with actual test evidence and limitations.
9. Submit changes through the repository's branch/PR workflow.

Raw real sessions must not be committed by default. See [Coding Standards](Coding-Standards).
