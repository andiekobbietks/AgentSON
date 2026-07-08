"""
Heart Monitor — Real-time agent health dashboard.

Computes heartbeat from .agentson / SQLite data, detects idle/crashed agents,
and generates a visual heartbeat timeline (ASCII for terminal, HTML for GUI).
"""

import sqlite3
import json
import os
import glob
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Heartbeat:
    """A single heartbeat reading."""
    timestamp_ms: int
    iso: str
    entry_type: str  # what caused this heartbeat
    agent: str
    is_step_boundary: bool  # step-start or step-finish


@dataclass
class AgentHealth:
    """Health status for a single agent/session."""
    session_id: str
    agent_name: str
    started_at: str
    last_heartbeat: str
    is_alive: bool  # heartbeat within threshold
    heart_rate: float  # beats per minute (steps/min)
    last_step_duration_ms: float
    avg_step_duration_ms: float
    total_steps: int
    idle_seconds: float
    health: str  # "healthy", "idle", "stale", "dead"


class HeartMonitor:
    """Computes and monitors agent heartbeats."""

    ALIVE_THRESHOLD_MS = 300000  # 5 min — heartbeat within this = alive
    IDLE_THRESHOLD_MS = 3600000  # 1 hour — heartbeat older = idle
    STALE_THRESHOLD_MS = 86400000  # 24 hours — stale

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.expanduser('~/.local/share/opencode/opencode.db')
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def compute_heartbeat(self, session_id: str) -> List[Heartbeat]:
        """Compute heartbeat series from session data."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT time_created, data FROM part
            WHERE session_id = ? ORDER BY time_created
        ''', (session_id,))
        parts = cursor.fetchall()

        # Also get messages for agent info
        cursor.execute('''
            SELECT data FROM message WHERE session_id = ?
            ORDER BY time_created DESC LIMIT 1
        ''', (session_id,))
        last_msg = cursor.fetchone()
        conn.close()

        # Determine agent name
        agent_name = 'unknown'
        if last_msg:
            try:
                msg_data = json.loads(last_msg['data'])
                agent_name = msg_data.get('role', 'unknown')
            except:
                pass

        heartbeats = []
        prev_step_type = None
        for p in parts:
            try:
                data = json.loads(p['data'])
                ptype = data.get('type', 'unknown')
            except:
                ptype = 'unknown'

            is_step = ptype in ('step-start', 'step-finish')
            hb = Heartbeat(
                timestamp_ms=p['time_created'],
                iso=datetime.utcfromtimestamp(p['time_created'] / 1000).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                entry_type=ptype,
                agent=agent_name,
                is_step_boundary=is_step,
            )
            heartbeats.append(hb)

        return heartbeats

    def get_health(self, session_id: str) -> AgentHealth:
        """Get current health status for a session."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM session WHERE id = ?', (session_id,))
        session = cursor.fetchone()
        if not session:
            conn.close()
            raise ValueError(f'Session {session_id} not found')

        # Get step timing
        cursor.execute('''SELECT time_created, data FROM part WHERE session_id = ? ORDER BY time_created''', (session_id,))
        parts = cursor.fetchall()
        conn.close()

        now_ms = int(datetime.utcnow().timestamp() * 1000)
        last_hb = int(session['last_heartbeat']) if session['last_heartbeat'] else 0
        idle_ms = now_ms - last_hb if last_hb > 0 else 0

        # Parse steps
        step_starts = []
        step_finishes = []
        for p in parts:
            try:
                data = json.loads(p['data'])
                if data.get('type') == 'step-start':
                    step_starts.append(p['time_created'])
                elif data.get('type') == 'step-finish':
                    step_finishes.append(p['time_created'])
            except:
                pass

        # Step durations
        step_durs = []
        for i in range(min(len(step_starts), len(step_finishes))):
            dur = step_finishes[i] - step_starts[i]
            if dur > 0:
                step_durs.append(dur)

        # Heart rate: steps per minute
        total_steps = len(step_starts)
        session_dur_min = (session['time_updated'] - session['time_created']) / 60000 if session['time_updated'] and session['time_created'] else 1
        heart_rate = total_steps / session_dur_min if session_dur_min > 0 else 0

        # Health classification
        if idle_ms < self.ALIVE_THRESHOLD_MS:
            health = 'healthy'
            is_alive = True
        elif idle_ms < self.IDLE_THRESHOLD_MS:
            health = 'idle'
            is_alive = True
        elif idle_ms < self.STALE_THRESHOLD_MS:
            health = 'stale'
            is_alive = False
        else:
            health = 'dead'
            is_alive = False

        return AgentHealth(
            session_id=session_id,
            agent_name=session['title'] or 'unknown',
            started_at=datetime.utcfromtimestamp(session['time_created'] / 1000).strftime('%Y-%m-%d %H:%M:%S') if session['time_created'] else 'unknown',
            last_heartbeat=datetime.utcfromtimestamp(last_hb / 1000).strftime('%Y-%m-%d %H:%M:%S') if last_hb else 'unknown',
            is_alive=is_alive,
            heart_rate=heart_rate,
            last_step_duration_ms=step_durs[-1] if step_durs else 0,
            avg_step_duration_ms=statistics.mean(step_durs) if step_durs else 0,
            total_steps=total_steps,
            idle_seconds=idle_ms / 1000,
            health=health,
        )

    def all_sessions_health(self) -> List[AgentHealth]:
        """Get health for all sessions."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM session ORDER BY last_heartbeat DESC')
        ids = [r['id'] for r in cursor.fetchall()]
        conn.close()

        healths = []
        for sid in ids:
            try:
                healths.append(self.get_health(sid))
            except:
                pass
        return healths

    def render_heartbeat_ascii(self, heartbeats: List[Heartbeat], width: int = 72) -> str:
        """Render heartbeat as ASCII timeline."""
        if not heartbeats:
            return "No heartbeat data"

        lines = []
        lines.append("HEARTBEAT TIMELINE")
        lines.append("=" * width)

        # Time range
        min_t = heartbeats[0].timestamp_ms
        max_t = heartbeats[-1].timestamp_ms
        span_ms = max_t - min_t
        if span_ms == 0:
            span_ms = 1

        # Build activity density per column
        density = [0] * width
        for hb in heartbeats:
            col = int((hb.timestamp_ms - min_t) / span_ms * (width - 1))
            col = min(col, width - 1)
            density[col] += 1

        max_density = max(density) if density else 1

        # Render density as bar chart
        bar_chars = " .:-=+*#%@"
        lines.append("")
        lines.append("Activity Density:")
        for i in range(0, width, 12):
            chunk = density[i:i+12]
            t = min_t + (i / width) * span_ms
            label = datetime.utcfromtimestamp(t / 1000).strftime('%H:%M')
            bars = ""
            for d in chunk:
                if d > 0:
                    level = int(d / max_density * (len(bar_chars) - 1))
                    bars += bar_chars[level]
                else:
                    bars += " "
            lines.append("%s |%s" % (label, bars))

        lines.clear()
        lines.append("HEARTBEAT MONITOR — %d beats over %.1f hours" % (
            len(heartbeats), span_ms / 3600000
        ))
        lines.append("=" * width)

        # Step boundaries are the "peaks"
        step_beats = [hb for hb in heartbeats if hb.is_step_boundary]
        if step_beats:
            # Show inter-step intervals as the "pulse"
            intervals = []
            for i in range(1, len(step_beats)):
                interval_s = (step_beats[i].timestamp_ms - step_beats[i-1].timestamp_ms) / 1000
                intervals.append(interval_s)

            if intervals:
                max_interval = max(intervals)
                lines.append("Step intervals (seconds):")
                for i, interval in enumerate(intervals[:width]):
                    bar_len = int(interval / max_interval * 40) if max_interval > 0 else 0
                    bar = "#" * bar_len
                    t = datetime.utcfromtimestamp(step_beats[i+1].timestamp_ms / 1000).strftime('%H:%M')
                    lines.append("%s %6.1fs %s" % (t, interval, bar))

        return "\n".join(lines)

    def render_heartbeat_html(self, heartbeats: List[Heartbeat], health: AgentHealth) -> str:
        """Render heartbeat as HTML dashboard."""
        if not heartbeats:
            return "<p>No heartbeat data</p>"

        # Compute step intervals for sparkline
        step_beats = [hb for hb in heartbeats if hb.is_step_boundary]
        intervals = []
        for i in range(1, len(step_beats)):
            intervals.append((step_beats[i].timestamp_ms - step_beats[i-1].timestamp_ms) / 1000)

        # Sparkline data (SVG)
        spark_width = 400
        spark_height = 60
        if intervals:
            max_int = max(intervals) if intervals else 1
            points = []
            for i, intv in enumerate(intervals):
                x = (i / max(len(intervals) - 1, 1)) * spark_width
                y = spark_height - (intv / max_int * spark_height)
                points.append("%.1f,%.1f" % (x, y))
            sparkline = '<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>' % (
                " ".join(points),
                "#22c55e" if health.health == "healthy" else "#eab308" if health.health == "idle" else "#ef4444"
            )
        else:
            sparkline = ""

        # Health color
        color_map = {"healthy": "#22c55e", "idle": "#eab308", "stale": "#f97316", "dead": "#ef4444"}
        color = color_map.get(health.health, "#6b7280")

        # Heartbeat "pulse" animation
        pulse_rate = max(0.5, 60 / max(health.heart_rate, 0.1)) if health.heart_rate > 0 else 999

        html = """<!DOCTYPE html>
<html><head><title>Agent Heart Monitor</title>
<style>
body { background: #0a0a0a; color: #e5e5e5; font-family: 'Cascadia Code', monospace; margin: 20px; }
.heart-monitor { background: #111; border: 1px solid #333; border-radius: 8px; padding: 20px; max-width: 600px; }
.status { font-size: 24px; font-weight: bold; color: %s; }
.pulse { animation: pulse %ss infinite; }
@keyframes pulse { 0%% { opacity: 1; } 50%% { opacity: 0.3; } 100%% { opacity: 1; } }
.stat { display: inline-block; margin: 8px 16px 8px 0; }
.stat-label { color: #888; font-size: 11px; text-transform: uppercase; }
.stat-value { font-size: 18px; color: #fff; }
.sparkline { margin: 16px 0; }
</style></head><body>
<div class="heart-monitor">
  <div class="status pulse">%s</div>
  <div class="stat">
    <div class="stat-label">Heart Rate</div>
    <div class="stat-value">%.1f bpm</div>
  </div>
  <div class="stat">
    <div class="stat-label">Total Steps</div>
    <div class="stat-value">%d</div>
  </div>
  <div class="stat">
    <div class="stat-label">Avg Step</div>
    <div class="stat-value">%.1fs</div>
  </div>
  <div class="stat">
    <div class="stat-label">Idle</div>
    <div class="stat-value">%.0fs</div>
  </div>
  <div class="sparkline">
    <svg width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>
  </div>
  <div class="stat">
    <div class="stat-label">Started</div>
    <div class="stat-value">%s</div>
  </div>
  <div class="stat">
    <div class="stat-label">Last Beat</div>
    <div class="stat-value">%s</div>
  </div>
</div></body></html>""" % (
            color, pulse_rate,
            health.health.upper(),
            health.heart_rate,
            health.total_steps,
            health.avg_step_duration_ms / 1000,
            health.idle_seconds,
            spark_width, spark_height, spark_width, spark_height, sparkline,
            health.started_at,
            health.last_heartbeat,
        )
        return html


def main():
    monitor = HeartMonitor()

    print("=" * 60)
    print("AGENT HEART MONITOR")
    print("=" * 60)

    # Current session health
    current_id = 'ses_0c7c1fb3bffeZRIIDKTX0Zppte'
    print("\n### CURRENT SESSION ###")
    try:
        health = monitor.get_health(current_id)
        print("Status: %s" % health.health.upper())
        print("Alive: %s" % health.is_alive)
        print("Heart rate: %.1f bpm" % health.heart_rate)
        print("Total steps: %d" % health.total_steps)
        print("Avg step: %.1fs" % (health.avg_step_duration_ms / 1000))
        print("Last step: %.1fs" % (health.last_step_duration_ms / 1000))
        print("Idle: %.0fs (%.1f min)" % (health.idle_seconds, health.idle_seconds / 60))
        print("Started: %s" % health.started_at)
        print("Last heartbeat: %s" % health.last_heartbeat)

        # ASCII heartbeat
        heartbeats = monitor.compute_heartbeat(current_id)
        print("\n" + monitor.render_heartbeat_ascii(heartbeats))

        # HTML heartbeat
        html = monitor.render_heartbeat_html(heartbeats, health)
        html_path = os.path.join(os.path.dirname(__file__), '..', 'exports', 'heartbeat.html')
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        with open(html_path, 'w') as f:
            f.write(html)
        print("\nHTML dashboard: %s" % os.path.abspath(html_path))

    except Exception as e:
        print("Error: %s" % e)

    # All sessions health summary
    print("\n\n### ALL SESSIONS HEALTH ###")
    all_health = monitor.all_sessions_health()
    status_counts = {}
    for h in all_health:
        status_counts[h.health] = status_counts.get(h.health, 0) + 1

    print("Total sessions: %d" % len(all_health))
    for status, count in sorted(status_counts.items()):
        print("  %s: %d" % (status, count))

    # Top 5 most recent alive sessions
    alive = [h for h in all_health if h.is_alive]
    print("\nAlive sessions (top 5):")
    for h in alive[:5]:
        print("  %s  %s  %.1f bpm  idle=%.0fs" % (
            h.session_id[:20], h.health, h.heart_rate, h.idle_seconds
        ))


if __name__ == '__main__':
    main()
