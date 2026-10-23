"""
FreeStyle Libre 2 CSV reader for AgentSON.

This reader converts FreeStyle Libre 2 glucose data (CSV format)
into AgentSON v1.2 format for visualization and search.

Usage:
    from readers.libre import read_libre_csv, get_libre_summary

    data = read_libre_csv("libre_data.csv")
    summary = get_libre_summary(data)

CSV shape (produced upstream by
``glucometerutils --driver fslibre2``):

    Timestamp,Glucose (mmol/L),,,Type,Source
    2026-10-01 08:00:00,5.5,,,CGM,(Sensor)

The two middle columns are empty in the sensor-history export. ``Type`` is the
reading kind (CGM / Scan). ``Source`` is the provenance, e.g. ``(Sensor)``.

Mapping notes
-------------
* Each reading becomes an ``observation`` entry, the v1.2 primitive for a
  reading produced by a tool, user or sensor.
* ``timestamp`` is epoch milliseconds, because the v1.2 entry schema requires
  an integer. The Libre export carries local wall-clock time with no offset,
  so the value is interpreted in the *system* timezone and the basis is
  recorded explicitly as ``source-local`` rather than silently treated as UTC.
* The CSV ``Source`` is mapped onto the schema's ``source`` enum, which has no
  "manual" member; a manual scan is therefore recorded as ``user``.
* The CSV ``Type`` (CGM / Scan) is preserved in ``data.reading_type`` -- it is
  a different thing from ``source`` and was previously dropped.
"""

import csv
from datetime import datetime, timezone
from typing import Dict, List
from pathlib import Path


# Clinical thresholds (mmol/L; Diabetes UK / ATTD consensus).
# Hypoglycaemia < 3.9, target range 3.9-10.0, hyperglycaemia > 10.0.
# Status and the summary metrics below share these constants so a reading can
# no longer be "low" and in range at the same time.
LOW_THRESHOLD = 3.9
HIGH_THRESHOLD = 10.0

# CSV "Source" -> AgentSON observation `source` enum
# (agent | user | system | tool | sensor | extension | other).
SOURCE_MAP = {
    "sensor": "sensor",
    "scan": "user",
    "manual": "user",
    "user": "user",
    "system": "system",
    "tool": "tool",
    "extension": "extension",
    "agent": "agent",
}


def _epoch_ms(dt: datetime) -> int:
    """
    Convert a timestamp to epoch milliseconds.

    A naive datetime is interpreted in the system timezone
    (``datetime.astimezone`` presumes local time for naive values), so the
    result is unambiguous. The reader does not assert that the source file is
    UTC; the original wall-clock value is preserved separately.
    """
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return int(dt.timestamp() * 1000)


def read_libre_csv(csv_path: str) -> Dict:
    """
    Read FreeStyle Libre 2 CSV and convert to AgentSON v1.2 format.

    Args:
        csv_path: Path to the CSV file

    Returns:
        AgentSON session data
    """
    entries: List[Dict] = []
    timestamps: List[datetime] = []
    glucose_values: List[float] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp_str = row.get("Timestamp", "")
            glucose_str = row.get("Glucose (mmol/L)", "")
            source_raw = row.get("Source", "").strip("()").strip()
            reading_type = (row.get("Type", "") or "").strip()

            if not timestamp_str or not glucose_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('"', ''))
                glucose = float(glucose_str)
            except (ValueError, TypeError):
                continue

            # Unknown sources fall back to the enum's catch-all rather than
            # emitting a value the schema rejects.
            source = SOURCE_MAP.get(source_raw.lower(), "other")

            timestamps.append(timestamp)
            glucose_values.append(glucose)

            # Create entry -- `observation`, with an integer-ms timestamp and
            # a schema-valid `source`.
            entry = {
                "type": "observation",
                "timestamp": _epoch_ms(timestamp),
                "text": f"Glucose: {glucose:.2f} mmol/L",
                "source": source,
                "agent": "glucose-monitor",
                "provenance": {
                    "confidence": "confirmed",
                    "source": "export",
                },
                "data": {
                    "value": glucose,
                    "unit": "mmol/L",
                    "reading_type": reading_type,
                    "source_raw": source_raw,
                    "timestamp_local": timestamp.isoformat(),
                    "timestamp_basis": "source-local",
                },
            }

            # Add status based on glucose level, using the same thresholds as
            # the summary metrics.
            if glucose < LOW_THRESHOLD:
                entry["status"] = "low"
                entry["text"] += " LOW"
            elif glucose > HIGH_THRESHOLD:
                entry["status"] = "high"
                entry["text"] += " HIGH"
            else:
                entry["status"] = "normal"

            entries.append(entry)

    # Calculate summary statistics
    if glucose_values:
        avg_glucose = sum(glucose_values) / len(glucose_values)
        min_glucose = min(glucose_values)
        max_glucose = max(glucose_values)

        # Time in range (3.9-10.0 mmol/L)
        in_range = sum(1 for g in glucose_values if LOW_THRESHOLD <= g <= HIGH_THRESHOLD)
        tir = (in_range / len(glucose_values)) * 100

        # Hypoglycemia (< 3.9)
        hypo = sum(1 for g in glucose_values if g < LOW_THRESHOLD)
        hypo_pct = (hypo / len(glucose_values)) * 100

        # Hyperglycemia (> 10.0)
        hyper = sum(1 for g in glucose_values if g > HIGH_THRESHOLD)
        hyper_pct = (hyper / len(glucose_values)) * 100
    else:
        avg_glucose = min_glucose = max_glucose = 0
        tir = hypo_pct = hyper_pct = 0

    # Date range
    if timestamps:
        start_time = min(timestamps)
        end_time = max(timestamps)
        days = (end_time - start_time).days + 1
    else:
        start_time = end_time = datetime.now()
        days = 0

    session_id = f"libre-{Path(csv_path).stem}"

    return {
        "$schema": "https://agentson.dev/schema/v1.2.json",
        "version": "1.2",
        "id": session_id,
        "tool": {
            # `name` is enum-constrained in v1.2 and has no Libre member, so
            # the identity is carried by `id`/`label` and the enum catch-all.
            "name": "other",
            "id": "freestyle-libre-2",
            "label": "FreeStyle Libre 2",
            "version": "2.0.0",
            "session_id": session_id,
        },
        "agent": {
            "id": "glucose-monitor",
            "name": "Glucose Monitor",
            "model": "sensor",
        },
        "variant": {
            "id": "libre-csv",
            "name": "FreeStyle Libre CSV Export",
            "version": "1.0.0",
        },
        "started_at": start_time.isoformat() if timestamps else None,
        "ended_at": end_time.isoformat() if timestamps else None,
        "entries": entries,
        "metrics": {
            "total_readings": len(entries),
            "avg_glucose": round(avg_glucose, 2),
            "min_glucose": round(min_glucose, 2),
            "max_glucose": round(max_glucose, 2),
            "time_in_range": round(tir, 1),
            "hypo_pct": round(hypo_pct, 1),
            "hyper_pct": round(hyper_pct, 1),
            "days": days,
            "readings_per_day": round(len(entries) / days, 1) if days > 0 else 0,
        },
        "metadata": {
            "source_file": csv_path,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def get_libre_summary(data: Dict) -> str:
    """
    Generate a human-readable summary of Libre data.

    Args:
        data: AgentSON session data from Libre reader

    Returns:
        Summary string
    """
    metrics = data.get("metrics", {})

    lines = []
    lines.append("FreeStyle Libre 2 Summary")
    lines.append("=" * 40)
    lines.append(f"Period: {data.get('started_at', 'N/A')} to {data.get('ended_at', 'N/A')}")
    lines.append(f"Days: {metrics.get('days', 0)}")
    lines.append(f"Total readings: {metrics.get('total_readings', 0)}")
    lines.append(f"Readings/day: {metrics.get('readings_per_day', 0)}")
    lines.append("")
    lines.append("Glucose Statistics:")
    lines.append(f"  Average: {metrics.get('avg_glucose', 0):.2f} mmol/L")
    lines.append(f"  Min: {metrics.get('min_glucose', 0):.2f} mmol/L")
    lines.append(f"  Max: {metrics.get('max_glucose', 0):.2f} mmol/L")
    lines.append("")
    lines.append(f"Time in Range ({LOW_THRESHOLD}-{HIGH_THRESHOLD}): {metrics.get('time_in_range', 0):.1f}%")
    lines.append(f"Hypoglycemia (<{LOW_THRESHOLD}): {metrics.get('hypo_pct', 0):.1f}%")
    lines.append(f"Hyperglycemia (>{HIGH_THRESHOLD}): {metrics.get('hyper_pct', 0):.1f}%")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m readers.libre <csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    data = read_libre_csv(csv_path)
    print(get_libre_summary(data))