# AgentSON Platform — Enterprise Operations Runbook

For clients running AgentSON Platform (premium module, local or managed).
All commands below use only the standard library. No cloud dependency.

## 1. Verify the local premium path (before any GRC upload)

```bash
# Confirm licences are present locally (never Phone-Home)
agentson platform license --dev          # writes ~/.agentson/platform-license.json

# Confirm the server responds and the scan is present
agentson platform serve --port 8090     # opens http://localhost:8090/

# Confirm evidence can be exported and signed
agentson grc-export --digest <report.json> --secure --output out.json
```

## 2. End-to-end GRC ingestion (the loop you asked for)

```bash
# Terminal A — start the dev server (local ingestion point)
agentson platform serve --port 8090

# Terminal B — export + sign + post to the local server
agentson grc-export --digest scan/report.json --secure --post http://localhost:8090/api/evidence

# Verify ingestion server-side (signature verified, evidence count shown)
curl http://localhost:8090/api/evidence  # GET not supported; check server stdout
# Or: open http://localhost:8090/ and review the dashboard
```

The POST endpoint at `/api/evidence` accepts the JSON package emitted by `grc-export`. It verifies `signature` + `signer_kid` using the local ECDSA P-256 public key (`~/.agentson/signing.pub`), writes the evidence to `~/.agentson/platform/evidence/evidence_YYYYmmdd_HHMMSS.json`, and returns `signature_verified: true/false`.

If a client needs to point at a real GRC platform (Vanta / Drata / Hyperproof) instead of localhost:

```bash
agentson grc-export --digest report.json --secure --post https://client-gateway.example.com/agentson/evidence
```

The `--post` retry handles transient failures: 2 s / 4 s / 8 s exponential backoff, 3 attempts max.

## 3. Networking troubleshooting (enterprise client needs to see this)

```bash
# Resolve, TCP, TLS, HTTP — read-only probes, zero telemetry
agentson platform doctor --dns example.com
agentson platform doctor --tcp example.com:443
agentson platform doctor --tls example.com:443
agentson platform doctor --http https://example.com/health
agentson platform doctor --proxy
agentson platform doctor --offline
```

What each proves:

- `--dns`: hostname resolution works (rules out DNS misconfiguration on the agent host).
- `--tcp`: TCP connectivity to the GRC / ingestion endpoint works (rules out firewall / port block).
- `--tls`: TLS handshake + cert expiry / issuer / cipher verified (rules out cert expiry / wrong CA).
- `--http`: the endpoint responds with status + body preview (rules out 500 / auth failure).
- `--proxy`: reports `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` visible to the process.
- `--offline`: confirms the core licence check reads a local file and performs 0 DNS / 0 TCP; stated as a fact about the code path, not a network probe.

Server endpoints for the same probes:

```
GET  /api/health     → {status, service, scan_dir, checked_at}
GET  /api/doctor?target=host:port     → full sweep
GET  /api/doctor?offline=1            → offline proof
GET  /api/graph?input=examples        → graph JSON (structure pipeline output)
POST /api/evidence                     → ingest GRC package (201 if accepted)
```

## 4. Structure pipeline (premium data pipeline — the "training pipeline")

```bash
# From any directory containing .agentson fixtures
agentson platform structure --input . --output ./structure/
```

Produces:

- `structure/graph.json` — entities + relations (agent ↔ session ↔ tool)
- `structure/entities.csv` + `relations.csv` — tabular for Excel / GRC import
- `structure/training_module.jsonl` — entry-level stream for model-training / fine-tuning

The pipeline scans `.agentson` JSONL files (ADR-015, v1.2 canonical). It does not invent relations: only `agent`, `session`, `tool`, `source_file` are extracted from the stream meta line and entry lines.

## 5. What requires a licence (premium gate) vs free

| Feature | Gate | Local check |
|---|---|---|
| `export`, `validate`, `render` | free | no file needed |
| `grc-export` | `is_premium("grc-export")` | `~/.agentson/platform-license.json` or `AGENTSON_PLATFORM_LICENSE` env |
| `structure` | `is_premium("structure")` | same file |
| `audit-log` | `is_premium("audit-log")` | same file |
| `platform serve` | free preview | reads real `report.json`; no network call |

Never phones home. The licence file is written by `platform license --dev` for local testing only; for production it is written by the commercial agreement, not by this CLI.

## 6. File paths (all verified this session)

- Source: `C:\Users\Admin\vibeedge-studio\AgentSON\cli/signing.py`
- Source: `C:\Users\Admin\vibeedge-studio\AgentSON\cli/main.py`
- Source: `C:\Users\Admin\vibeedge-studio\AgentSON\agentson_platform/structure.py`
- Source: `C:\Users\Admin\vibeedge-studio\AgentSON\agentson_platform/netdoctor.py`
- Source: `C:\Users\Admin\vibeedge-studio\AgentSON\agentson_platform/server.py`
- Source: `C:\Users\Admin\vibeedge-studio\AgentSON\readers/gemini.py`
- Dev licence: `C:\Users\Admin\.agentson\platform-license.json`
- Evidence ingested: `C:\Users\Admin\.agentson\platform\evidence\evidence_20261021_220000.json`
- Real scan report: `C:\Users\Admin\AppData\Local\Temp\opencode\platform_full\scan-20261021-161148\report.json`
- Real Gemini source: `C:\Users\Admin\Downloads\Google-Search_NEXGO-N6N86N96-whats-the-cheapers-for-a-micro-biz_20261021-1620.json`
