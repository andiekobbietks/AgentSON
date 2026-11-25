# SOP-006: Prepare an AgentSON Data Report for a Healthcare Appointment

**Status:** Legacy domain-specific guidance; not clinical or regulatory advice.  
**Last reviewed:** 25 November 2026

## Purpose

Render a local report from a supported health-data archive for review and discussion with an appropriate healthcare professional.

## Prerequisites

- A supported source export and a validated AgentSON archive.
- A local, access-controlled output directory.
- Confirmation that the intended recipient and sharing method are appropriate.

## Generate a local HTML report

~~~powershell
python -m cli.main validate "$HOME\Downloads\libre_libre_data.agentson"
python -m cli.main render "$HOME\Downloads\libre_libre_data.agentson" --format html --output "$HOME\Downloads\glucose_report.html"
Start-Process "$HOME\Downloads\glucose_report.html"
~~~

Check the report against the original source data. Verify date ranges, time zones, units, missing values and calculations before relying on it.

## Sharing

- Share only the minimum necessary information.
- Prefer a provider-approved, access-controlled and encrypted channel.
- Do not upload health reports to public hosting or send them to an unverified recipient.
- Email may not be an appropriate channel for sensitive health information; check the provider's instructions.
- Keep a copy of exactly what was shared and when, if required by your own record-keeping process.

## Clinical and interoperability limitations

The report is a technical rendering, not a diagnosis or treatment recommendation. Discuss interpretation with a qualified healthcare professional.

NHS FHIR integration is not implemented by this procedure. Nightscout setup does not, by itself, provide NHS FHIR connectivity or establish approval to transmit data to a clinical system. Any future integration requires a separate security, privacy, clinical-safety and organisational review.
