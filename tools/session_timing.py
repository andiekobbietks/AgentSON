"""
Session Timing R&D — Active detection, burst analysis, hydration, prediction.

Empirical analysis of OpenCode session timing data from SQLite + .agentson files.
"""

import sqlite3
import json
import os
import glob
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class ActivityBurst:
    """A contiguous period of high-frequency activity."""
    start_ms: int
    end_ms: int
    part_count: int
    part_types: List[str] = field(default_factory=list)

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    @property
    def parts_per_second(self) -> float:
        return self.part_count / (self.duration_ms / 1000) if self.duration_ms > 0 else 0


@dataclass
class IdlePeriod:
    """A gap between activity bursts."""
    start_ms: int
    end_ms: int
    trigger: str  # what type of part preceded the idle

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass
class SessionTimingProfile:
    """Complete timing analysis for a single session."""
    session_id: str
    started_at: Optional[str]
    ended_at: Optional[str]
    wall_clock_ms: Optional[int]
    total_parts: int
    total_messages: int

    # Heartbeat
    step_count: int
    mean_step_duration_ms: float
    median_step_duration_ms: float
    inter_step_interval_ms: float

    # Bursts
    burst_count: int
    long_burst_count: int
    longest_burst_parts: int
    longest_burst_ms: float

    # Idle
    idle_count: int
    mean_idle_ms: float
    max_idle_ms: float

    # Activity ratio
    active_ms: int  # time spent in bursts
    idle_total_ms: int  # time spent idle
    activity_ratio: float  # active / (active + idle)

    # Hydration potential
    sparse_timestamp_count: int
    hydrateable_gaps: int  # gaps where interpolation is safe

    # Classification
    is_active: bool  # has activity in last 5 min
    session_class: str  # "micro", "short", "medium", "long", "epic"


class SessionTimingAnalyzer:
    """Analyzes session timing from SQLite + .agentson files."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.expanduser('~/.local/share/opencode/opencode.db')
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def detect_active_sessions(self, within_ms: int = 300000) -> List[Dict]:
        """Detect sessions with activity in the last N milliseconds."""
        conn = self._connect()
        cursor = conn.cursor()
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        cutoff = now_ms - within_ms

        cursor.execute('''
            SELECT id, title, time_created, time_updated,
                   (time_updated - time_created) as duration_ms
            FROM session
            WHERE time_updated > ?
            ORDER BY time_updated DESC
        ''', (cutoff,))
        sessions = []
        for row in cursor.fetchall():
            # Check if there are any in-progress tool calls
            cursor.execute('''
                SELECT COUNT(*) as cnt FROM part p
                JOIN message m ON p.message_id = m.id
                WHERE m.session_id = ?
                AND p.data LIKE '%"status":"pending"%'
            ''', (row['id'],))
            pending = cursor.fetchone()['cnt']

            sessions.append({
                'id': row['id'],
                'title': row['title'],
                'duration_min': row['duration_ms'] / 60000,
                'pending_tools': pending,
                'is_current': row['id'].startswith('ses_0c7c1fb3bffe'),
            })
        conn.close()
        return sessions

    def analyze_session(self, session_id: str) -> SessionTimingProfile:
        """Full timing analysis for a single session."""
        conn = self._connect()
        cursor = conn.cursor()

        # Session metadata
        cursor.execute('SELECT * FROM session WHERE id = ?', (session_id,))
        session = cursor.fetchone()
        if not session:
            conn.close()
            raise ValueError(f'Session {session_id} not found')

        # All parts ordered by time
        cursor.execute('''
            SELECT time_created, time_updated, data
            FROM part WHERE session_id = ?
            ORDER BY time_created
        ''', (session_id,))
        parts = cursor.fetchall()

        # Message count
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM message WHERE session_id = ?
        ''', (session_id,))
        msg_count = cursor.fetchone()['cnt']

        conn.close()

        # Parse part types and compute timing
        part_types = []
        part_times = []
        step_starts = []
        step_finishes = []
        tool_calls = []

        for p in parts:
            try:
                data = json.loads(p['data'])
                ptype = data.get('type', 'unknown')
                state = data.get('state', {})
                status = state.get('status', 'none')
            except:
                ptype = 'unknown'
                status = 'none'

            part_types.append(ptype)
            part_times.append(p['time_created'])

            if ptype == 'step-start':
                step_starts.append(p['time_created'])
            elif ptype == 'step-finish':
                step_finishes.append(p['time_created'])
            elif ptype == 'tool':
                tool_calls.append({
                    'time': p['time_created'],
                    'tool': data.get('tool', 'unknown'),
                    'status': status,
                    'duration': (p['time_updated'] or p['time_created']) - p['time_created']
                })

        # Compute inter-arrival gaps
        gaps = []
        for i in range(1, len(part_times)):
            gap = part_times[i] - part_times[i - 1]
            if gap > 0:
                gaps.append(gap)

        # Detect bursts (< 1s between parts)
        bursts = []
        current_burst = []
        for i, gap in enumerate(gaps):
            if gap < 1000:
                current_burst.append(i)
            else:
                if len(current_burst) >= 2:
                    bursts.append(current_burst)
                current_burst = []
        if len(current_burst) >= 2:
            bursts.append(current_burst)

        # Detect idle periods (> 60s between parts)
        idle_periods = []
        for i, gap in enumerate(gaps):
            if gap > 60000:
                idle_periods.append(IdlePeriod(
                    start_ms=part_times[i],
                    end_ms=part_times[i + 1],
                    trigger=part_types[i] if i < len(part_types) else 'unknown'
                ))

        # Step-level heartbeat
        step_durs = []
        for i in range(min(len(step_starts), len(step_finishes))):
            dur = step_finishes[i] - step_starts[i]
            if dur > 0:
                step_durs.append(dur)

        inter_step = []
        for i in range(1, len(step_starts)):
            interval = step_starts[i] - step_starts[i - 1]
            if interval > 0:
                inter_step.append(interval)

        # Compute active vs idle time
        active_ms = sum(b.duration_ms for b in [ActivityBurst(
            start_ms=part_times[min(burst)],
            end_ms=part_times[max(burst) + 1] if max(burst) + 1 < len(part_times) else part_times[max(burst)],
            part_count=len(burst)
        ) for burst in bursts]) if bursts else 0

        total_ms = (session['time_updated'] or 0) - (session['time_created'] or 0)
        idle_total_ms = sum(ip.duration_ms for ip in idle_periods)
        activity_ratio = active_ms / (active_ms + idle_total_ms) if (active_ms + idle_total_ms) > 0 else 0

        # Classify session
        duration_min = total_ms / 60000
        if duration_min < 1:
            session_class = 'micro'
        elif duration_min < 10:
            session_class = 'short'
        elif duration_min < 60:
            session_class = 'medium'
        elif duration_min < 480:
            session_class = 'long'
        else:
            session_class = 'epic'

        # Active check (activity in last 5 min)
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        is_active = (now_ms - (session['time_updated'] or 0)) < 300000

        # Hydration potential
        sparse_count = sum(1 for t in part_times if t is None)
        hydrateable = len([g for g in gaps if 1000 < g < 300000])  # 1s-5min gaps are safe to interpolate

        return SessionTimingProfile(
            session_id=session_id,
            started_at=datetime.utcfromtimestamp(session['time_created'] / 1000).isoformat() + 'Z' if session['time_created'] else None,
            ended_at=datetime.utcfromtimestamp(session['time_updated'] / 1000).isoformat() + 'Z' if session['time_updated'] else None,
            wall_clock_ms=total_ms,
            total_parts=len(parts),
            total_messages=msg_count,
            step_count=len(step_starts),
            mean_step_duration_ms=statistics.mean(step_durs) if step_durs else 0,
            median_step_duration_ms=statistics.median(step_durs) if step_durs else 0,
            inter_step_interval_ms=statistics.mean(inter_step) if inter_step else 0,
            burst_count=len(bursts),
            long_burst_count=len([b for b in bursts if len(b) >= 3]),
            longest_burst_parts=max((len(b) for b in bursts), default=0),
            longest_burst_ms=max((ActivityBurst(
                start_ms=part_times[min(b)],
                end_ms=part_times[max(b) + 1] if max(b) + 1 < len(part_times) else part_times[max(b)],
                part_count=len(b)
            ).duration_ms for b in bursts), default=0),
            idle_count=len(idle_periods),
            mean_idle_ms=statistics.mean([ip.duration_ms for ip in idle_periods]) if idle_periods else 0,
            max_idle_ms=max((ip.duration_ms for ip in idle_periods), default=0),
            active_ms=active_ms,
            idle_total_ms=idle_total_ms,
            activity_ratio=activity_ratio,
            sparse_timestamp_count=sparse_count,
            hydrateable_gaps=hydrateable,
            is_active=is_active,
            session_class=session_class,
        )

    def cross_session_stats(self) -> Dict:
        """Aggregate timing statistics across all sessions."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, time_created, time_updated,
                   (time_updated - time_created) as duration_ms
            FROM session WHERE time_updated > time_created
        ''')
        sessions = cursor.fetchall()

        durations = [s['duration_ms'] for s in sessions]

        # Message counts
        cursor.execute('''
            SELECT s.id, COUNT(m.id) as cnt
            FROM session s LEFT JOIN message m ON s.id = m.session_id
            GROUP BY s.id
        ''')
        msg_data = {r['id']: r['cnt'] for r in cursor.fetchall()}

        conn.close()

        # Classify
        classes = {'micro': 0, 'short': 0, 'medium': 0, 'long': 0, 'epic': 0}
        for d in durations:
            m = d / 60000
            if m < 1: classes['micro'] += 1
            elif m < 10: classes['short'] += 1
            elif m < 60: classes['medium'] += 1
            elif m < 480: classes['long'] += 1
            else: classes['epic'] += 1

        return {
            'total_sessions': len(sessions),
            'duration_stats': {
                'min_ms': min(durations),
                'max_ms': max(durations),
                'mean_ms': statistics.mean(durations),
                'median_ms': statistics.median(durations),
                'stdev_ms': statistics.stdev(durations) if len(durations) > 1 else 0,
            },
            'classes': classes,
            'message_correlation': self._correlation(
                [d / 60000 for d in durations],
                [msg_data.get(s['id'], 0) for s in sessions]
            ),
        }

    def _correlation(self, x: List[float], y: List[float]) -> float:
        """Pearson correlation coefficient."""
        n = len(x)
        if n < 3:
            return 0
        mx, my = statistics.mean(x), statistics.mean(y)
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / n
        sx = statistics.stdev(x)
        sy = statistics.stdev(y)
        return cov / (sx * sy) if sx * sy > 0 else 0

    def hydrate_session(self, session_id: str, method: str = 'linear') -> List[Dict]:
        """Fill in missing timestamps using interpolation."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, time_created, data FROM part
            WHERE session_id = ? ORDER BY time_created
        ''', (session_id,))
        parts = cursor.fetchall()
        conn.close()

        # Find parts with valid timestamps
        known = [(i, p['time_created']) for i, p in enumerate(parts) if p['time_created']]
        if len(known) < 2:
            return [{'index': i, 'original': p['time_created'], 'hydrated': None} for i, p in enumerate(parts)]

        # Interpolate missing
        results = []
        known_idx = 0
        for i, p in enumerate(parts):
            if p['time_created']:
                results.append({'index': i, 'original': p['time_created'], 'hydrated': None})
            else:
                # Find bracketing known points
                while known_idx < len(known) - 1 and known[known_idx + 1][0] < i:
                    known_idx += 1
                if known_idx < len(known) - 1:
                    i0, t0 = known[known_idx]
                    i1, t1 = known[known_idx + 1]
                    if method == 'linear':
                        frac = (i - i0) / (i1 - i0) if i1 != i0 else 0
                        hydrated = int(t0 + frac * (t1 - t0))
                    else:
                        hydrated = t0  # previous-value fill
                    results.append({'index': i, 'original': None, 'hydrated': hydrated})
                else:
                    results.append({'index': i, 'original': None, 'hydrated': None})

        return results

    def predict_duration(self, partial_session_id: str) -> Dict:
        """Predict total session duration from partial data."""
        # Get historical stats
        stats = self.cross_session_stats()
        median_dur = stats['duration_stats']['median_ms']

        # Get current session progress
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT time_created, time_updated FROM session WHERE id = ?
        ''', (partial_session_id,))
        session = cursor.fetchone()

        cursor.execute('''
            SELECT COUNT(*) as cnt FROM message WHERE session_id = ?
        ''', (partial_session_id,))
        msg_count = cursor.fetchone()['cnt']

        cursor.execute('''
            SELECT COUNT(*) as cnt FROM part WHERE session_id = ?
        ''', (partial_session_id,))
        part_count = cursor.fetchone()['cnt']
        conn.close()

        elapsed = (session['time_updated'] or 0) - (session['time_created'] or 0)

        # Simple prediction: if we have message count, use correlation
        corr = stats['message_correlation']
        if corr > 0.3 and msg_count > 0:
            # Estimate total messages from duration so far
            msgs_per_ms = msg_count / elapsed if elapsed > 0 else 0
            predicted_total_msgs = median_dur * msgs_per_ms if msgs_per_ms > 0 else msg_count
            predicted_dur = predicted_total_msgs / msgs_per_ms if msgs_per_ms > 0 else median_dur
        else:
            # Fallback: use median duration
            predicted_dur = median_dur

        return {
            'session_id': partial_session_id,
            'elapsed_ms': elapsed,
            'elapsed_min': elapsed / 60000,
            'current_msgs': msg_count,
            'current_parts': part_count,
            'predicted_total_ms': predicted_dur,
            'predicted_total_min': predicted_dur / 60000,
            'confidence': 'high' if corr > 0.5 else 'moderate' if corr > 0.3 else 'low',
            'based_on': stats['total_sessions'],
        }


def main():
    """Run the full R&D analysis."""
    analyzer = SessionTimingAnalyzer()

    print('=' * 70)
    print('SESSION TIMING R&D — EMPIRICAL ANALYSIS')
    print('=' * 70)

    # 1. Active sessions
    print('\n### 1. ACTIVE SESSION DETECTION ###')
    active = analyzer.detect_active_sessions(within_ms=300000)
    print('Sessions active in last 5 min: %d' % len(active))
    for s in active:
        marker = ' [CURRENT]' if s['is_current'] else ''
        print('  %s  %.1f min  pending_tools=%d%s' % (
            s['id'][:24], s['duration_min'], s['pending_tools'], marker
        ))

    # 2. Full analysis of current session
    print('\n### 2. CURRENT SESSION TIMING PROFILE ###')
    try:
        profile = analyzer.analyze_session('ses_0c7c1fb3bffeZRIIDKTX0Zppte')
        print('Session: %s (%s)' % (profile.session_id[:24], profile.session_class))
        print('Wall clock: %.1f min' % (profile.wall_clock_ms / 60000))
        print('Parts: %d | Messages: %d' % (profile.total_parts, profile.total_messages))
        print('Steps: %d (mean=%.1fs, median=%.1fs)' % (
            profile.step_count,
            profile.mean_step_duration_ms / 1000,
            profile.median_step_duration_ms / 1000
        ))
        print('Bursts: %d total, %d long (>=3 parts)' % (
            profile.burst_count, profile.long_burst_count
        ))
        print('Longest burst: %d parts, %.1fs' % (
            profile.longest_burst_parts, profile.longest_burst_ms / 1000
        ))
        print('Idle periods: %d (mean=%.1fs, max=%.1fs)' % (
            profile.idle_count,
            profile.mean_idle_ms / 1000,
            profile.max_idle_ms / 1000
        ))
        print('Activity ratio: %.1f%%' % (profile.activity_ratio * 100))
        print('Hydrateable gaps: %d' % profile.hydrateable_gaps)
        print('Active: %s' % profile.is_active)
    except Exception as e:
        print('Error: %s' % e)

    # 3. Cross-session statistics
    print('\n### 3. CROSS-SESSION STATISTICS ###')
    stats = analyzer.cross_session_stats()
    print('Total sessions: %d' % stats['total_sessions'])
    ds = stats['duration_stats']
    print('Duration: min=%.1fs, median=%.1fmin, mean=%.1fmin, max=%.1fmin' % (
        ds['min_ms'] / 1000,
        ds['median_ms'] / 60000,
        ds['mean_ms'] / 60000,
        ds['max_ms'] / 60000,
    ))
    print('Classification:', stats['classes'])
    print('Duration vs message correlation: %.3f' % stats['message_correlation'])

    # 4. Hydration demo
    print('\n### 4. HYDRATION DEMO ###')
    hydrated = analyzer.hydrate_session('ses_0c7c1fb3bffeZRIIDKTX0Zppte')
    filled = [h for h in hydrated if h['hydrated'] is not None]
    print('Total parts: %d' % len(hydrated))
    print('Hydrated gaps: %d' % len(filled))
    if filled:
        print('Sample hydrated timestamps (first 5):')
        for h in filled[:5]:
            print('  Part %d: %s -> %s' % (
                h['index'],
                'None',
                datetime.utcfromtimestamp(h['hydrated'] / 1000).strftime('%H:%M:%S.%f')[:-3]
            ))

    # 5. Duration prediction
    print('\n### 5. DURATION PREDICTION ###')
    prediction = analyzer.predict_duration('ses_0c7c1fb3bffeZRIIDKTX0Zppte')
    print('Elapsed: %.1f min' % prediction['elapsed_min'])
    print('Predicted total: %.1f min' % prediction['predicted_total_min'])
    print('Confidence: %s (based on %d sessions)' % (
        prediction['confidence'], prediction['based_on']
    ))


if __name__ == '__main__':
    main()
