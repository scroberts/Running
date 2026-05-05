#!/usr/bin/env python3

from flask import Flask, render_template, request, g, redirect, url_for
from urllib.parse import urlencode
import sqlite3
import re
import datetime
import logging

logger = logging.getLogger(__name__)

import sql
import garmin
from config import DATABASE

app = Flask(__name__)

TIME_PATTERN = r'^\d+:[0-5]\d:[0-5]\d$'


def _validate_workout(date: str, distance: str, recovery: str, easy: str,
                      threshold: str, interval: str, repetition: str) -> list[str]:
    """Return validation error messages for workout form fields."""
    errors = []
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        errors.append('Date must be in YYYY-MM-DD format.')
    try:
        if float(distance) <= 0:
            errors.append('Distance must be a positive number.')
    except (ValueError, TypeError):
        errors.append('Distance must be a number.')
    for label, val in [('Recovery', recovery), ('Easy', easy), ('Threshold', threshold),
                       ('Interval', interval), ('Repetition', repetition)]:
        if not re.match(TIME_PATTERN, val):
            errors.append(f'{label} time must be in H:MM:SS format (e.g. 0:45:00).')
    return errors


def _validate_health(date: str, weight: str, waist: str, waist_bb: str,
                     hips: str, chest: str, hr: str) -> list[str]:
    """Return validation error messages for health form fields."""
    errors = []
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        errors.append('Date must be in YYYY-MM-DD format.')
    for label, val in [('Weight', weight), ('Waist', waist), ('Waist BB', waist_bb),
                       ('Hips', hips), ('Chest', chest)]:
        try:
            if float(val) < 0:
                errors.append(f'{label} must be a non-negative number.')
        except (ValueError, TypeError):
            errors.append(f'{label} must be a number.')
    try:
        if int(float(hr)) <= 0:
            errors.append('Heart rate must be a positive number.')
    except (ValueError, TypeError):
        errors.append('Heart rate must be a number.')
    return errors


def _validate_shoe(short_name: str, long_name: str) -> list[str]:
    """Return validation error messages for shoe form fields."""
    errors = []
    if not short_name.strip():
        errors.append('Short name is required.')
    if not long_name.strip():
        errors.append('Long name is required.')
    return errors


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/', methods=["GET", "POST"])
def homepage():
    return render_template("homepage.html")


@app.route('/Workout52Weeks', methods=["GET", "POST"])
def workout_52weeks():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_log_52weeks(conn, cur)
    return render_template("ListInfo.html", title='Workout Statistics',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/WorkoutWeekStats', methods=["GET", "POST"])
def workout_week_stats():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_log_week_stats(conn, cur)
    return render_template("ListInfo.html", title='Workout Statistics',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/Workout12Months', methods=["GET", "POST"])
def workout_12months():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_log_12months(conn, cur)
    return render_template("ListInfo.html", title='Workout Statistics',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/WorkoutMonthStats', methods=["GET", "POST"])
def workout_month_stats():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_log_month_stats(conn, cur)
    return render_template("ListInfo.html", title='Workout Statistics',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/ListWorkouts', methods=["GET"])
def list_workouts():
    conn = get_db()
    cur = conn.cursor()
    query = request.args.get('q', '').strip()
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    thead, tbody, summary, total, total_pages = sql.search_workouts(cur, query=query, page=page)
    return render_template("ListWorkouts.html", thead=thead, tbody=tbody, summary=summary,
                           query=query, page=page, total_pages=total_pages)


@app.route('/ChangeWorkout/<id>', methods=["GET", "POST"])
def change_workout(id):
    conn = get_db()
    cur = conn.cursor()
    logger.debug('ChangeWorkout id=%s', id)
    wo = sql.get_workout(cur, id)

    val_date = wo[0]
    val_location = wo[1]
    val_wo_type = wo[2]
    val_objective = wo[3]
    val_notes = wo[4]
    val_distance = str(wo[5])
    val_recovery = wo[6]
    val_easy = wo[7]
    val_threshold = wo[8]
    val_interval = wo[9]
    val_repetition = wo[10]
    val_shoe = wo[11]

    cur.execute('SELECT shortName FROM shoes WHERE retired = 0 ORDER BY shortName')
    shoe_list = [val_shoe] + [row[0] for row in cur]

    cur.execute('SELECT type FROM wo_type')
    wo_type_list = [val_wo_type] + [row[0] for row in cur]

    errors = []
    if request.method == "POST":
        date = request.form['date']
        location = request.form['location']
        wo_type = request.form['wo_type']
        objective = request.form['objective']
        notes = request.form['notes']
        distance = request.form['distance']
        recovery = request.form['recovery']
        easy = request.form['easy']
        threshold = request.form['threshold']
        interval = request.form['interval']
        repetition = request.form['repetition']
        shoes = request.form['shoes']

        errors = _validate_workout(date, distance, recovery, easy, threshold, interval, repetition)
        if not errors:
            cur.execute('SELECT id FROM shoes WHERE shortName = ?', (shoes,))
            shoe_id = cur.fetchone()[0]

            cur.execute('SELECT id FROM wo_type WHERE type = ?', (wo_type,))
            wo_type_id = cur.fetchone()[0]

            sql.change_workout(conn, cur, id, date, location, wo_type_id, objective, notes,
                               distance, recovery, easy, threshold, interval, repetition, shoe_id)

            return redirect(url_for('list_workouts'))

        val_date, val_location, val_wo_type = date, location, wo_type
        val_objective, val_notes, val_distance = objective, notes, distance
        val_recovery, val_easy, val_threshold = recovery, easy, threshold
        val_interval, val_repetition, val_shoe = interval, repetition, shoes

    return render_template("ChangeWorkout.html",
                           val_date=val_date, val_location=val_location,
                           val_wo_type=val_wo_type, wo_type_list=wo_type_list,
                           val_objective=val_objective, val_notes=val_notes,
                           val_distance=val_distance, val_recovery=val_recovery,
                           val_easy=val_easy, val_threshold=val_threshold,
                           val_interval=val_interval, val_repetition=val_repetition,
                           val_shoe=val_shoe, shoe_list=shoe_list, errors=errors)


@app.route('/ListAthletes', methods=["GET"])
def list_athletes():
    conn = get_db()
    cur = conn.cursor()
    letter = request.args.get('letter')
    intro, thead, tbody, summary = sql.get_athletes(conn, cur, letter=letter)
    return render_template("ListInfo.html", title='Listing of Athletes',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/ListHealth', methods=["GET"])
def list_health():
    conn = get_db()
    cur = conn.cursor()
    query = request.args.get('q', '').strip()
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    thead, tbody, summary, total, total_pages = sql.search_health(cur, query=query, page=page)
    return render_template("ListHealth.html", thead=thead, tbody=tbody, summary=summary,
                           query=query, page=page, total_pages=total_pages)


@app.route('/ChangeHealth/<id>', methods=["GET", "POST"])
def change_health(id):
    conn = get_db()
    cur = conn.cursor()
    health = sql.get_health(cur, id)

    val_date = health[1]
    val_weight = health[2]
    val_waist = health[3]
    val_waist_bb = health[4]
    val_hips = health[5]
    val_chest = health[6]
    val_hr = health[7]
    val_notes = health[8]

    errors = []
    if request.method == "POST":
        date = request.form['date']
        weight = request.form['weight']
        waist = request.form['waist']
        waist_bb = request.form['waist_bb']
        hips = request.form['hips']
        chest = request.form['chest']
        hr = request.form['HR']
        notes = request.form['notes']

        errors = _validate_health(date, weight, waist, waist_bb, hips, chest, hr)
        if not errors:
            sql.change_health(conn, cur, id, date, weight, waist, waist_bb, hips, chest, notes, hr)
            return redirect(url_for('list_health'))

        val_date, val_weight, val_waist = date, weight, waist
        val_waist_bb, val_hips, val_chest, val_hr, val_notes = waist_bb, hips, chest, hr, notes

    return render_template("AddHealth.html",
                           val_date=val_date, val_weight=val_weight,
                           val_waist=val_waist, val_waist_bb=val_waist_bb,
                           val_chest=val_chest, val_hips=val_hips,
                           val_notes=val_notes, val_HR=val_hr, errors=errors)


@app.route('/AddHealth', methods=["GET", "POST"])
def add_health():
    conn = get_db()
    cur = conn.cursor()

    defaults = dict(val_date=datetime.date.today().strftime('%Y-%m-%d'),
                    val_weight='0.0', val_waist='0.0', val_waist_bb='0.0',
                    val_chest='0.0', val_hips='0.0', val_notes='notes...', val_HR=60)
    errors = []

    if request.method == "POST":
        date = request.form['date']
        weight = request.form['weight']
        waist = request.form['waist']
        waist_bb = request.form['waist_bb']
        chest = request.form['chest']
        hips = request.form['hips']
        hr = request.form['HR']
        notes = request.form['notes']

        errors = _validate_health(date, weight, waist, waist_bb, hips, chest, hr)
        if not errors:
            sql.add_health(conn, cur, date, weight, waist, waist_bb, hips, chest, notes, hr)
            return redirect(url_for('list_health'))

        defaults = dict(val_date=date, val_weight=weight, val_waist=waist,
                        val_waist_bb=waist_bb, val_chest=chest, val_hips=hips,
                        val_notes=notes, val_HR=hr)

    return render_template("AddHealth.html", errors=errors, **defaults)


@app.route('/PlotWeight', methods=["GET", "POST"])
def plot_weight():
    conn = get_db()
    cur = conn.cursor()
    sql.get_weight_report(cur)
    return render_template("PlotWeight.html")


@app.route('/AddWorkout', methods=["GET", "POST"])
def add_workout():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT shortName FROM shoes WHERE retired = 0 ORDER BY shortName')
    shoe_list = [row[0] for row in cur]

    cur.execute('SELECT type FROM wo_type')
    wo_type_list = [row[0] for row in cur]

    defaults = dict(val_date=datetime.date.today().strftime('%Y-%m-%d'),
                    val_location='Location...', val_objective='Objective', val_notes='Notes...',
                    val_distance='10.0', val_recovery='0:00:00', val_easy='0:00:00',
                    val_threshold='0:00:00', val_interval='0:00:00', val_repetition='0:00:00')
    errors = []

    if request.method == "POST":
        logger.debug('AddWorkout POST request')
        date = request.form['date']
        location = request.form['location']
        wo_type = request.form['wo_type']
        objective = request.form['objective']
        notes = request.form['notes']
        distance = request.form['distance']
        recovery = request.form['recovery']
        easy = request.form['easy']
        threshold = request.form['threshold']
        interval = request.form['interval']
        repetition = request.form['repetition']
        shoes = request.form['shoes']

        errors = _validate_workout(date, distance, recovery, easy, threshold, interval, repetition)
        if not errors:
            logger.debug('shoes=%s', shoes)
            cur.execute('SELECT id FROM shoes WHERE shortName = ?', (shoes,))
            shoe_id = cur.fetchone()[0]

            logger.debug('wo_type=%s', wo_type)
            cur.execute('SELECT id FROM wo_type WHERE type = ?', (wo_type,))
            wo_type_id = cur.fetchone()[0]

            sql.add_workout(conn, cur, date, location, wo_type_id, objective, notes,
                            distance, recovery, easy, threshold, interval, repetition, shoe_id)

            return redirect(url_for('list_workouts'))

        defaults = dict(val_date=date, val_location=location, val_objective=objective,
                        val_notes=notes, val_distance=distance, val_recovery=recovery,
                        val_easy=easy, val_threshold=threshold, val_interval=interval,
                        val_repetition=repetition)

    return render_template("AddWorkout.html", wo_type_list=wo_type_list,
                           shoe_list=shoe_list, errors=errors, **defaults)


@app.route('/ListShoes', methods=["GET", "POST"])
def list_shoes():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_shoes(cur)
    return render_template("ListInfo.html", title='Listing of Shoes',
                           intro='', thead=thead, tbody=tbody, summary=summary)


@app.route('/ManageShoes', methods=["GET"])
def manage_shoes():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_all_shoes(cur)
    return render_template("ListInfo.html", title='Manage Shoes',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/RetireShoe/<id>', methods=["GET"])
def retire_shoe(id):
    conn = get_db()
    cur = conn.cursor()
    sql.retire_shoe(conn, cur, id)
    intro, thead, tbody, summary = sql.get_all_shoes(cur)
    return render_template("ListInfo.html", title='Manage Shoes',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/AddShoes', methods=["GET", "POST"])
def add_shoes():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_shoes(cur)
    val_short_name, val_long_name, errors = '', '', []

    if request.method == "POST":
        val_short_name = request.form['shortName']
        val_long_name = request.form['longName']
        errors = _validate_shoe(val_short_name, val_long_name)
        if not errors:
            sql.add_shoes(conn, cur, val_short_name, val_long_name)
            intro, thead, tbody, summary = sql.get_shoes(cur)
            val_short_name, val_long_name = '', ''

    return render_template("ShoeInput.html", intro=intro, thead=thead, tbody=tbody,
                           val_shortName=val_short_name, val_longName=val_long_name,
                           errors=errors)


@app.route('/Compare', methods=["GET", "POST"])
def compare():
    conn = get_db()
    cur = conn.cursor()
    races = sql.get_races(cur)

    if request.method == "POST":
        race1 = request.form['race1']
        race2 = request.form['race2']
        min_time = request.form['min_time']
        max_time = request.form['max_time']
        percent = request.form['percent']

        id_1 = int(re.search(r'\d+', re.search(r'\<\d+\>', race1).group()).group())
        id_2 = int(re.search(r'\d+', re.search(r'\<\d+\>', race2).group()).group())
        event_name1, date1 = sql.get_race_info(cur, id_1)
        event_name2, date2 = sql.get_race_info(cur, id_2)
        intro, thead, tbody, summary = sql.compare_races(
            cur, event_name1, date1, event_name2, date2, min_time, max_time, float(percent) / 100
        )
        return render_template("ListInfo.html", title='Comparison of Race Results',
                               intro=intro, thead=thead, tbody=tbody, summary=summary)

    return render_template("CompareRaces.html", races=races)


@app.route('/user/<username>', methods=["GET", "POST"])
def show_user_races(username):
    logger.debug('show_user_races: %s', username)
    cur = get_db().cursor()
    intro, thead, tbody, summary = sql.get_races_for_athlete(cur, username)
    return render_template("ListInfo.html", title='Races by Athlete',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/GarminSync', methods=["GET"])
def garmin_sync():
    conn = get_db()
    cur = conn.cursor()
    error = None
    activities = []
    try:
        client = garmin.get_client()
        raw = garmin.fetch_recent_activities(client, days=30)
        unlogged = garmin.find_unlogged(cur, raw)
        for act in unlogged:
            type_key = (act.get('activityType') or {}).get('typeKey', '')
            dist_km = (act.get('distance') or 0) / 1000.0
            total_secs = int(act.get('duration') or 0)
            act_id = act.get('activityId', '')
            date_str = (act.get('startTimeLocal') or '')[:10]
            name = act.get('activityName') or ''
            params = urlencode({
                'date': date_str,
                'dist': f'{dist_km:.2f}',
                'name': name,
                'type_key': type_key,
                'duration': total_secs,
            })
            activities.append({
                'activity_id': act_id,
                'date': date_str,
                'name': name,
                'wo_type': garmin._ACTIVITY_TYPE_MAP.get(type_key, type_key or 'Unknown'),
                'dist_km': f'{dist_km:.2f}',
                'duration_str': garmin._duration_str(total_secs),
                'link': f'/AddWorkoutFromGarmin/{act_id}?{params}',
            })
    except ValueError as e:
        error = str(e)
    except Exception as e:
        logger.error('Garmin sync error: %s', e)
        error = f'Garmin connection failed: {e}'
    return render_template("GarminSync.html", activities=activities, error=error)


@app.route('/AddWorkoutFromGarmin/<activity_id>', methods=["GET"])
def add_workout_from_garmin(activity_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT shortName FROM Shoes WHERE retired = 0 ORDER BY shortName')
    shoe_list = [row[0] for row in cur]
    cur.execute('SELECT type FROM wo_type')
    wo_type_list = [row[0] for row in cur]

    errors = []
    defaults = dict(
        val_date=datetime.date.today().strftime('%Y-%m-%d'),
        val_location='', val_objective='', val_notes='',
        val_distance='10.0', val_recovery='0:00:00', val_easy='0:00:00',
        val_threshold='0:00:00', val_interval='0:00:00', val_repetition='0:00:00',
        val_wo_type=wo_type_list[0] if wo_type_list else '',
    )
    try:
        # Reconstruct activity summary from URL params (passed by GarminSync page)
        # to avoid a second Garmin API call with a different response structure.
        activity = {
            'startTimeLocal': request.args.get('date', ''),
            'distance': float(request.args.get('dist', 0)) * 1000,
            'duration': float(request.args.get('duration', 0)),
            'activityName': request.args.get('name', ''),
            'activityType': {'typeKey': request.args.get('type_key', '')},
        }
        client = garmin.get_client()
        laps = garmin.fetch_laps(client, activity_id)
        defaults = garmin.map_to_form(activity, laps)
    except Exception as e:
        logger.error('Garmin activity fetch error: %s', e)
        errors = [f'Could not load Garmin activity: {e}']

    # Put the mapped workout type first so it is pre-selected in the dropdown
    matched_type = defaults.get('val_wo_type', '')
    ordered_types = [matched_type] + [t for t in wo_type_list if t != matched_type]

    return render_template("AddWorkout.html", wo_type_list=ordered_types,
                           shoe_list=shoe_list, errors=errors, **defaults)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # TODO: set debug=False before deploying to production
    app.run(debug=True, host='0.0.0.0', port=8080, passthrough_errors=True)
