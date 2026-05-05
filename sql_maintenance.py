#!/usr/bin/env python3
"""Maintenance utilities for the running log database.

Run directly to recalculate all derived fields in the Log and RaceTimes tables.
"""

import datetime
import logging

import sql
from config import DATABASE

logger = logging.getLogger(__name__)


def update_workout_calculated_data(conn, cur) -> None:
    """Recalculate and update all derived fields for every Log entry."""
    cur.execute('SELECT id FROM Log')
    for (row_id,) in cur.fetchall():
        cur.execute(
            'SELECT date, location, wo_type, objective, notes, dist, recovery, easy, '
            'threshold, interval, repetition, shoeID FROM Log WHERE Log.id = ?',
            (row_id,)
        )
        date, location, wo_type_id, objective, notes, distance, recovery, easy, threshold, interval, repetition, shoe_id = cur.fetchone()
        sql.change_workout(conn, cur, row_id, date, location, wo_type_id, objective, notes,
                           distance, recovery, easy, threshold, interval, repetition, shoe_id)


def update_racetimes_time(conn, cur) -> None:
    """Normalise the str_time field in all RaceTimes rows."""
    cur.execute('SELECT id, str_time FROM Racetimes')
    for row_id, str_time in cur.fetchall():
        cur.execute('UPDATE Racetimes SET str_time = ? WHERE id = ?',
                    (sql.scrub_timestr(str_time), row_id))
    conn.commit()


def update_racetimes_pace(conn, cur) -> None:
    """Normalise the pace field in all RaceTimes rows."""
    cur.execute('SELECT id, pace FROM Racetimes')
    for row_id, pace in cur.fetchall():
        cur.execute('UPDATE Racetimes SET pace = ? WHERE id = ?',
                    (sql.scrub_pace(pace), row_id))
    conn.commit()


def recalc_racetimes_pace(conn, cur) -> None:
    """Recalculate pace from sec_time and event distance for all RaceTimes rows."""
    cur.execute(
        'SELECT RaceTimes.id, RaceTimes.sec_time, Events.id, Events.dist FROM RaceTimes '
        'JOIN Races ON RaceTimes.raceID = Races.id '
        'JOIN Events ON Races.eventID = Events.id'
    )
    for row_id, sec_time, event_id, dist in cur.fetchall():
        pace = sql.timestr2pacestr(sql.str_time(sec_time / dist))
        logger.debug('racetime id=%s sec=%s event=%s dist=%s pace=%s',
                     row_id, sec_time, event_id, dist, pace)
        cur.execute('UPDATE Racetimes SET pace = ? WHERE id = ?', (pace, row_id))
    conn.commit()


def update_isodate(conn, cur) -> None:
    """Populate the isodate column in Log from the date column."""
    cur.execute('SELECT id, date FROM Log')
    for row_id, date in cur.fetchall():
        iso = datetime.datetime.strptime(date, '%Y-%m-%d').isocalendar()
        isodate_str = f'{iso[0]}-{str(iso[1]).zfill(2)}-{iso[2]}'
        logger.debug('update isodate id=%s -> %s', row_id, isodate_str)
        cur.execute('UPDATE Log SET isodate = ? WHERE id = ?', (isodate_str, row_id))
    conn.commit()


def update_secs(conn, cur) -> None:
    """Recalculate all _secs columns in Log from their corresponding time strings."""
    cur.execute('SELECT id, time, pace, recovery, easy, threshold, interval, repetition FROM Log')
    for row in cur.fetchall():
        row_id = row[0]
        time_secs, pace_secs, recovery_secs, easy_secs, threshold_secs, interval_secs, repetition_secs = (
            sql.secs(v) for v in row[1:]
        )
        cur.execute(
            'UPDATE Log SET time_secs=?, pace_secs=?, recovery_secs=?, easy_secs=?, '
            'threshold_secs=?, interval_secs=?, repetition_secs=? WHERE id=?',
            (time_secs, pace_secs, recovery_secs, easy_secs,
             threshold_secs, interval_secs, repetition_secs, row_id)
        )
    conn.commit()


def main() -> None:
    conn, cur = sql.load_database(DATABASE)
    recalc_racetimes_pace(conn, cur)
    update_workout_calculated_data(conn, cur)
    cur.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
