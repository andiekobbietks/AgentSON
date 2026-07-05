"""
FreeStyle Libre 2 CSV reader for AgentSON.

This reader converts FreeStyle Libre 2 glucose data (CSV format)
into AgentSON format for visualization and search.

Usage:
    from readers.libre import read_libre_csv, get_libre_summary

    data = read_libre_csv("libre_data.csv")
    summary = get_libre_summary(data)
"""

import csv
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path


def read_libre_csv(csv_path: str) -> Dict:
    """
    Read FreeStyle Libre 2 CSV and convert to AgentSON format.

    Args:
        csv_path: Path to the CSV file

    Returns:
        AgentSON session data
    """
    entries = []
    timestamps = []
    glucose_values = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp_str = row.get("Timestamp", "")
            glucose_str = row.get("Glucose (mmol/L)", "")
            source = row.get("Source", "").strip("()")

            if not timestamp_str or not glucose_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('"', ''))
                glucose = float(glucose_str)
            except (ValueError, TypeError):
                continue

            timestamps.append(timestamp)
            glucose_values.append(glucose)

            # Create entry
            entry = {
                "role": "sensor",
                "type": "glucose_reading",
                "timestamp": timestamp.isoformat(),
                "text": f"Glucose: {glucose:.2f} mmol/L",
                "data": {
                    "value": glucose,
                    "unit": "mmol/L",
                    "source": source,
                    "timestamp": timestamp.isoformat()
                }
            }

            # Add status based on glucose level
            if glucose < 4.0:
                entry["status"] = "low"
                entry["text"] += " ⚠️ LOW"
            elif glucose > 10.0:
                entry["status"] = "high"
                entry["text"] += " ⚠️ HIGH"
            else:
                entry["status"] = "normal"

            entries.append(entry)

    # Calculate summary statistics
    if glucose_values:
        avg_glucose = sum(glucose_values) / len(glucose_values)
        min_glucose = min(glucose_values)
        max_glucose = max(glucose_values)

        # Time in range (3.9-10.0 mmol/L)
        in_range = sum(1 for g in glucose_values if 3.9 <= g <= 10.0)
        tir = (in_range / len(glucose_values)) * 100

        # Hypoglycemia (< 3.9)
        hypo = sum(1 for g in glucose_values if g < 3.9)
        hypo_pct = (hypo / len(glucose_values)) * 100

        # Hyperglycemia (> 10.0)
        hyper = sum(1 for g in glucose_values if g > 10.0)
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

    return {
        "version": "1.0.0",
        "id": f"libre-{Path(csv_path).stem}",
        "tool": {
            "id": "freestyle-libre-2",
            "name": "FreeStyle Libre 2",
            "version": "2.0.0"
        },
        "agent": {
            "id": "glucose-monitor",
            "name": "Glucose Monitor",
            "model": "sensor"
        },
        "variant": {
            "id": "libre-csv",
            "name": "FreeStyle Libre CSV Export",
            "version": "1.0.0"
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
            "readings_per_day": round(len(entries) / days, 1) if days > 0 else 0
        },
        "metadata": {
            "source_file": csv_path,
            "exported_at": datetime.now(timezone.utc).isoformat()
        }
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
    entries = data.get("entries", [])

    lines = []
    lines.append(f"FreeStyle Libre 2 Summary")
    lines.append(f"=" * 40)
    lines.append(f"Period: {data.get('started_at', 'N/A')} to {data.get('ended_at', 'N/A')}")
    lines.append(f"Days: {metrics.get('days', 0)}")
    lines.append(f"Total readings: {metrics.get('total_readings', 0)}")
    lines.append(f"Readings/day: {metrics.get('readings_per_day', 0)}")
    lines.append("")
    lines.append(f"Glucose Statistics:")
    lines.append(f"  Average: {metrics.get('avg_glucose', 0):.2f} mmol/L")
    lines.append(f"  Min: {metrics.get('min_glucose', 0):.2f} mmol/L")
    lines.append(f"  Max: {metrics.get('max_glucose', 0):.2f} mmol/L")
    lines.append("")
    lines.append(f"Time in Range (3.9-10.0): {metrics.get('time_in_range', 0):.1f}%")
    lines.append(f"Hypoglycemia (<3.9): {metrics.get('hypo_pct', 0):.1f}%")
    lines.append(f"Hyperglycemia (>10.0): {metrics.get('hyper_pct', 0):.1f}%")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m readers.libre <csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    data = read_libre_csv(csv_path)
    print(get_libre_summary(data))
