# SOP-003: Render an AgentSON Archive as a Local HTML Report

**Status:** Current procedure for v1.2 JSONL archives.  
**Last reviewed:** 25 November 2026

## Purpose

Render a canonical AgentSON archive into an HTML report that can be opened in a local browser.

## Important viewer distinction

The static browser viewer at docs/viewer/index.html is a legacy viewer for single-JSON session-envelope documents. It does not parse canonical v1.2 JSONL streams. Do not drop a canonical .agentson JSONL archive into that viewer.

## Procedure

Render the archive using the CLI:

~~~powershell
python -m cli.main render "$HOME\Downloads\libre_libre_data.agentson" --format html --output "$HOME\Downloads\libre_report.html"
~~~

Open the generated report locally:

~~~powershell
Start-Process "$HOME\Downloads\libre_report.html"
~~~

Review the report for missing values, timestamp/time-zone assumptions, units and unexpected conversion output before sharing.

## Sharing and hosting

- Prefer keeping health-data reports local.
- Do not publish a report to a public Vercel, GitHub Pages or other public hosting project.
- If a report must be shared, use an approved, access-controlled and encrypted channel and share only the minimum necessary data.
- Do not assume that a private URL alone provides access control.

## Troubleshooting

| Issue | Action |
|---|---|
| JSONL archive fails in the legacy viewer | Expected; use the CLI render command above. |
| Render command rejects the archive | Run validate first and inspect the reported schema/version error. |
| Report has missing or unusual values | Compare against the source CSV; do not infer missing clinical values. |
| Browser cannot open the report | Check that the output file exists and open it from the local file system. |

## Limitations

The report is a technical rendering of supplied data, not a diagnosis, treatment recommendation or clinical record. Check its accuracy with an appropriate healthcare professional.
