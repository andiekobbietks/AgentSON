"""
Time-series exporter for AgentSON.

Extracts glucose (or other numeric) observation entries into a flat
timestamp,value series suitable for time-series foundation models such as
GlucoFM, Chronos-2, GluFormer, MOMENT, TimesFM, etc.

Output formats:
- csv:  timestamp,value,unit  (one row per reading)
- jsonl: {"timestamp": ..., "value": ..., "unit": ...} per line

Readings are sorted by timestamp ascending by default.
"""

import csv
import json
from typing import Dict, List, Optional, Any
from pathlib import Path


def _entries(data) -> List[dict]:
    if isinstance(data, dict):
        return data.get("entries", []) or []
    if isinstance(data, list):
        return data
    return []


def _to_ms(ts) -> Optional[int]:
    """Coerce a timestamp to integer milliseconds if possible."""
    if ts is None:
        return None
    if isinstance(ts, bool):
        return None
    if isinstance(ts, int):
        return ts
    if isinstance(ts, float):
        return int(ts)
    if isinstance(ts, str):
        s = ts.strip()
        if not s:
            return None
        # epoch ms as string
        try:
            return int(s)
        except ValueError:
            pass
        # ISO 8601
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.astimezone()
            return int(dt.timestamp() * 1000)
        except ValueError:
            return None
    return None


def extract_series(data, sort: bool = True) -> List[dict]:
    """Extract observation entries with a numeric value into a sorted series."""
    rows: List[dict] = []
    for e in _entries(data):
        if not isinstance(e, dict):
            continue
        if e.get("type") != "observation":
            continue
        d = e.get("data") or {}
        val = d.get("value")
        if val is None or isinstance(val, bool):
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue
        ts = _to_ms(e.get("timestamp"))
        # fall back to timestamp_local in data if top-level missing
        if ts is None:
            ts = _to_ms(d.get("timestamp_local"))
        rows.append({
            "timestamp": ts,
            "value": val,
            "unit": d.get("unit"),
            "reading_type": d.get("reading_type"),
            "source": e.get("source"),
        })

    if sort:
        # None timestamps sort last, stably
        rows.sort(key=lambda r: (r["timestamp"] is None, r["timestamp"] if r["timestamp"] is not None else 0))
    return rows


def export_timeseries(data, fmt: str = "csv", output_path: Optional[str] = None, sort: bool = True) -> int:
    """Write the extracted series to CSV or JSONL. Returns row count."""
    rows = extract_series(data, sort=sort)
    fmt = (fmt or "csv").lower()
    if fmt not in ("csv", "jsonl"):
        raise ValueError(f"Unknown format: {fmt}")

    if output_path is None:
        import sys
        out = sys.stdout
        close = False
    else:
        out = open(output_path, "w", encoding="utf-8", newline="")
        close = True

    try:
        if fmt == "csv":
            w = csv.writer(out)
            w.writerow(["timestamp", "value", "unit", "reading_type", "source"])
            for r in rows:
                w.writerow([r["timestamp"], r["value"], r["unit"] or "", r["reading_type"] or "", r["source"] or ""])
        else:
            for r in rows:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
    finally:
        if close:
            out.close()

    return len(rows)