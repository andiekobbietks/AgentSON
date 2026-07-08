"""
Live Heartbeat Demo — real-time agent health display.

Writes heartbeat entries to a JSONL file and renders a live terminal dashboard.
Run this while performing browser actions to see the heartbeat in real-time.
"""

import json
import time
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict


HEARTBEAT_FILE = os.path.join(os.path.dirname(__file__), '..', 'exports', 'live_heartbeat.jsonl')
ENTRIES: List[Dict] = []


def write_entry(entry_type: str, detail: str = ""):
    """Write a heartbeat entry and display it."""
    now = datetime.now(timezone.utc)
    entry = {
        "timestamp": now.isoformat(),
        "timestamp_ms": int(now.timestamp() * 1000),
        "type": entry_type,
        "detail": detail,
    }
    ENTRIES.append(entry)

    # Append to JSONL file
    os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
    with open(HEARTBEAT_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

    # Display
    render_live(entry)


def render_live(entry: Dict):
    """Render a single entry to terminal."""
    ts = entry['timestamp'][11:19]
    etype = entry['type']
    detail = entry['detail']

    # Color codes
    colors = {
        "heartbeat": "\033[92m",   # green
        "action": "\033[93m",       # yellow
        "observation": "\033[96m",  # cyan
        "thought": "\033[95m",      # magenta
        "user-query": "\033[97m",   # white
        "answer": "\033[92m",       # green
        "error": "\033[91m",        # red
    }
    reset = "\033[0m"
    color = colors.get(etype, "\033[0m")

    # Heartbeat pulse character
    pulse_chars = ["-", "\\", "|", "/"]
    pulse_idx = len(ENTRIES) % 4
    pulse = pulse_chars[pulse_idx]

    print("  %s [%s] %s%-12s%s %s" % (pulse, ts, color, etype, reset, detail))


def render_summary():
    """Render summary stats."""
    if not ENTRIES:
        return

    now = datetime.now(timezone.utc)
    first = ENTRIES[0]
    last = ENTRIES[-1]
    span_s = (last['timestamp_ms'] - first['timestamp_ms']) / 1000

    # Count types
    type_counts = {}
    for e in ENTRIES:
        t = e['type']
        type_counts[t] = type_counts.get(t, 0) + 1

    # Compute inter-entry gaps
    gaps = []
    for i in range(1, len(ENTRIES)):
        gap = ENTRIES[i]['timestamp_ms'] - ENTRIES[i-1]['timestamp_ms']
        gaps.append(gap)

    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    max_gap = max(gaps) if gaps else 0

    # Heart rate (entries per minute)
    heart_rate = len(ENTRIES) / (span_s / 60) if span_s > 0 else 0

    # Idle check
    last_gap = (now.timestamp() * 1000) - last['timestamp_ms']
    if last_gap < 30000:
        status = "\033[92mALIVE\033[0m"
    elif last_gap < 300000:
        status = "\033[93mIDLE\033[0m"
    else:
        status = "\033[91mSTALE\033[0m"

    print()
    print("  " + "=" * 56)
    print("  HEARTBEAT SUMMARY")
    print("  " + "=" * 56)
    print("  Status:        %s" % status)
    print("  Heart rate:    %.1f beats/min" % heart_rate)
    print("  Total beats:   %d" % len(ENTRIES))
    print("  Span:          %.1fs" % span_s)
    print("  Avg gap:       %.1fs" % (avg_gap / 1000))
    print("  Max gap:       %.1fs" % (max_gap / 1000))
    print("  Beat types:    %s" % type_counts)
    print("  Last beat:     %s" % last['timestamp'][11:19])
    print("  " + "=" * 56)

    # Activity bar
    bar_width = 50
    if gaps:
        max_gap_s = max(gaps) / 1000
        print("  Activity:")
        for i, gap in enumerate(gaps[-20:]):
            gap_s = gap / 1000
            bar_len = int(gap_s / max(max_gap_s, 1) * 30) if max_gap_s > 0 else 0
            bar = "#" * bar_len
            ts = ENTRIES[i + len(ENTRIES) - len(gaps) + len(gaps) - 20]['timestamp'][11:19] if len(gaps) > 20 else ENTRIES[i + 1]['timestamp'][11:19]
            print("    %s %6.1fs %s" % (ts, gap_s, bar))


def main():
    """Main loop — writes heartbeat entries at intervals."""
    print()
    print("  \033[92m*** LIVE HEARTBEAT MONITOR ***\033[0m")
    print("  Watching agent activity in real-time...")
    print("  Press Ctrl+C to stop")
    print()

    # Write initial heartbeat
    write_entry("heartbeat", "Monitor started")

    # Simulate some initial activity
    write_entry("thought", "Analyzing browser state...")
    time.sleep(0.5)
    write_entry("action", "Connected to Edge CDP on port 9223")
    time.sleep(0.3)
    write_entry("observation", "Page loaded: example.com")
    time.sleep(0.2)
    write_entry("heartbeat", "Pulse OK")

    print()
    print("  \033[93m--- Waiting for actions (Ctrl+C to stop) ---\033[0m")
    print()

    # Keep writing heartbeats every 5 seconds to show the pulse
    try:
        beat_count = 0
        while True:
            time.sleep(5)
            beat_count += 1
            write_entry("heartbeat", "Pulse #%d" % beat_count)
    except KeyboardInterrupt:
        print()
        render_summary()
        print()
        print("  Heartbeat data saved to: %s" % os.path.abspath(HEARTBEAT_FILE))


if __name__ == '__main__':
    main()
