# Reader conformance fixtures

These fixtures are **synthetic, source-shaped regression data**, not captured user sessions or vendor-certified fixtures. They contain no personal or production data. They exercise the actual repository reader entry points against representative native container formats:

- `claude_code_native_synthetic.jsonl`: Claude Code transcript JSONL records.
- `chrome_devtools_native_synthetic.md`: Chrome DevTools AI Assistance Markdown export.
- `libre_sensor_native_synthetic.csv`: FreeStyle Libre-style CSV rows with CGM and manual scan readings.

The MiniMax/Mavis and Antigravity tests create temporary SQLite databases with representative table layouts during the test. These are adapter integration fixtures, not copies of real vendor databases.

Synthetic fixtures prove that the current parser path works for the cases represented. They do not prove compatibility with every version of the source applications, nor lossless preservation of undocumented fields. Real, anonymised exports from supported versions should be added only with appropriate consent and privacy review.
