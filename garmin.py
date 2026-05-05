#!/usr/bin/env python3
"""Garmin Connect integration for the running log.

Authenticates via GARMIN_EMAIL / GARMIN_PASSWORD environment variables and
caches OAuth tokens in ~/.garth so MFA is only needed once per machine.
"""

import logging
import os
from datetime import date, timedelta

logger = logging.getLogger(__name__)

_ACTIVITY_TYPE_MAP = {
    'running': 'Run',
    'trail_running': 'Run',
    'track_running': 'Run',
    'treadmill_running': 'Run',
    'cycling': 'Ride',
    'road_biking': 'Ride',
    'mountain_biking': 'Ride',
    'indoor_cycling': 'Ride',
    'virtual_ride': 'Ride',
}


def get_client():
    """Return an authenticated Garmin client, reusing cached tokens where possible."""
    from garminconnect import Garmin
    from config import GARMIN_EMAIL, GARMIN_PASSWORD

    if not GARMIN_EMAIL or not GARMIN_PASSWORD:
        raise ValueError(
            'Set GARMIN_EMAIL and GARMIN_PASSWORD environment variables to enable Garmin sync.'
        )

    client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
    tokenstore = os.path.expanduser('~/.garth')
    client.login(tokenstore=tokenstore)
    logger.info('Garmin client authenticated (tokenstore=%s)', tokenstore)
    return client


def fetch_recent_activities(client, days: int = 30) -> list[dict]:
    """Return Garmin activities from the last N days, newest first."""
    end = date.today()
    start = end - timedelta(days=days)
    activities = client.get_activities_by_date(
        start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    )
    logger.info('Fetched %d Garmin activities (%d days)', len(activities), days)
    return activities


def fetch_laps(client, activity_id: str) -> list[dict]:
    """Return the lapDTOs list for an activity, or [] on missing data."""
    splits = client.get_activity_splits(str(activity_id))
    return splits.get('lapDTOs', [])


def _pace_str(speed_ms: float) -> str:
    """Convert m/s to a mm:ss pace string (minutes per km)."""
    if not speed_ms or speed_ms <= 0:
        return '--:--'
    secs_per_km = 1000.0 / speed_ms
    mins = int(secs_per_km // 60)
    secs = int(secs_per_km % 60)
    return f'{mins}:{secs:02d}'


def _duration_str(seconds: float) -> str:
    """Convert seconds to mm:ss string."""
    if not seconds:
        return '0:00'
    total = int(seconds)
    mins = total // 60
    secs = total % 60
    return f'{mins}:{secs:02d}'


def format_lap_notes(laps: list[dict], total_dist_km: float, total_secs: float) -> str:
    """Build the Rep / Pace / AHR / RPE / Dist notes block."""
    lines = ['Rep / Pace / AHR / RPE / Dist']
    for i, lap in enumerate(laps, start=1):
        pace = _pace_str(lap.get('averageSpeed', 0))
        ahr = int(lap.get('averageHR') or 0) or ''
        dist_km = (lap.get('distance') or 0) / 1000.0
        lines.append(f'{i} / {pace} / {ahr} /   / {dist_km:.2f} km')
    lines.append(f'Total distance was {total_dist_km:.2f} km in {_duration_str(total_secs)} minutes')
    return '\n'.join(lines)


def find_unlogged(cur, activities: list[dict]) -> list[dict]:
    """Return activities that have no matching Log entry (same date, distance ±10%)."""
    cur.execute('SELECT date, dist FROM Log')
    logged = cur.fetchall()

    result = []
    for act in activities:
        raw_date = (act.get('startTimeLocal') or '')[:10]
        dist_m = act.get('distance') or 0
        dist_km = dist_m / 1000.0

        already_logged = any(
            log_date == raw_date and dist_km > 0 and abs(log_dist - dist_km) / dist_km <= 0.10
            for log_date, log_dist in logged
            if log_dist
        )
        if not already_logged:
            result.append(act)
    return result


def map_to_form(activity: dict, laps: list[dict]) -> dict:
    """Return a pre-filled AddWorkout form dict from a Garmin activity + its laps."""
    raw_date = (activity.get('startTimeLocal') or '')[:10]
    dist_m = activity.get('distance') or 0
    dist_km = dist_m / 1000.0
    total_secs = activity.get('duration') or 0

    type_key = (activity.get('activityType') or {}).get('typeKey', '')
    wo_type = _ACTIVITY_TYPE_MAP.get(type_key, 'Run')

    notes = format_lap_notes(laps, dist_km, total_secs) if laps else ''

    return dict(
        val_date=raw_date or date.today().strftime('%Y-%m-%d'),
        val_location=activity.get('activityName') or '',
        val_objective='',
        val_notes=notes,
        val_distance=f'{dist_km:.2f}',
        val_recovery='0:00:00',
        val_easy='0:00:00',
        val_threshold='0:00:00',
        val_interval='0:00:00',
        val_repetition='0:00:00',
        val_wo_type=wo_type,
    )
