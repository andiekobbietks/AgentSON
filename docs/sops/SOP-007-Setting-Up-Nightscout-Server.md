# SOP-007: Nightscout Local Prototype

**Status:** Historical, optional domain-specific prototype; not production deployment guidance.  
**Last reviewed:** 25 November 2026

## Purpose

Record the original local Nightscout integration path used in the early health-data prototype. Nightscout is not required by AgentSON Core and does not provide NHS FHIR connectivity by itself.

## Important limitations

- This procedure is for a local development environment only.
- Do not expose a Nightscout server or MongoDB instance directly to the public internet.
- Do not use default credentials or reuse an API secret.
- Do not commit .env files, API secrets, database connection strings or patient data.
- Any remote deployment requires a separate security, privacy, access-control, backup and retention design.
- This setup is not a clinical system and is not an NHS-approved integration.

## Local prototype outline

1. Review the current Nightscout installation documentation and compatibility requirements.
2. Use a dedicated local development environment and a supported MongoDB version.
3. Store configuration in an untracked .env file and ensure the file is excluded by .gitignore.
4. Bind the service to localhost for local testing; do not expose the development port to a shared network.
5. Use synthetic or appropriately de-identified test data.
6. Stop the service when testing is complete and remove test data securely.

Example local environment variables (placeholders only):

~~~dotenv
MONGO_CONNECTION=mongodb://localhost:27017/nightscout
API_SECRET=replace-with-a-unique-random-secret
~~~

Check the current upstream Nightscout documentation for supported deployment instructions. The historical Azure free-tier instructions in earlier versions of this SOP are withdrawn.

## Relationship to AgentSON

Nightscout is an optional data source in a legacy domain workflow. AgentSON readers and exporters must document the source version, data fields, conversion and known gaps. Do not infer that this integration supports NHS FHIR or automatic clinical-system sharing.

## Safety

Glucose thresholds and alerts must be configured with the person and their healthcare team. This prototype is not an emergency alert service and must not be used as the sole means of monitoring or responding to a medical event.
