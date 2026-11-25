# SOP-002: Convert FreeStyle Libre CSV Data to an AgentSON Stream

**Status:** Legacy domain-specific procedure; verify the installed reader version before use.  
**Last reviewed:** 25 November 2026

## Purpose

Convert a supported FreeStyle Libre CSV export into a local AgentSON archive for inspection and reporting. This is a data-conversion procedure, not clinical interpretation.

## Prerequisites

- A CSV export that the installed Libre reader supports.
- AgentSON installed in the local Python environment.
- Permission to process the data and a secure local output directory.

## Procedure

From the repository checkout or installed environment:

~~~powershell
python -m cli.main export --tool libre --input "$HOME\Documents\libre_data.csv" --output "$HOME\Downloads"
~~~

Use the exact input path and output directory for your machine. The generated filename is reported by the CLI; do not assume a fixed byte size or timestamp.

Validate the generated archive:

~~~powershell
python -m cli.main validate "$HOME\Downloads\libre_libre_data.agentson"
~~~

If the CLI reports a different output filename, use that path.

## Format note

The canonical v1.2 interchange format is JSONL: one typed event per line, with stream-meta first. A .agentson file is not necessarily a single JSON object. The JSON session envelope is a separate materialised/document compatibility representation.

Inspect or render the archive using the CLI rather than assuming the old JSON-envelope structure:

~~~powershell
python -m cli.main render "$HOME\Downloads\libre_libre_data.agentson" --format md --output "$HOME\Downloads\libre_report.md"
~~~

## Privacy and safety

- Treat glucose readings as sensitive health data.
- Keep the archive and reports in an access-controlled local folder.
- Do not upload raw exports to public hosting or paste them into unapproved services.
- Check timestamps, units, missing values and conversion output before relying on it.
- AgentSON does not provide medical advice or validate clinical interpretation.

## Next steps

Use SOP-003 to render an HTML report locally, or SOP-006 for guidance on preparing a report for a healthcare appointment.
