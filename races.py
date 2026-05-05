#!/usr/bin/env python3

from flask import Flask, render_template, request, g
import sqlite3
import re
import datetime
import logging

logger = logging.getLogger(__name__)

import sql
from config import DATABASE

app = Flask(__name__)


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


@app.route('/ListWorkouts', methods=["GET", "POST"])
def list_workouts():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_workouts(cur)
    return render_template("ListInfo.html", title='Listing of Workouts',
                           intro='', thead=thead, tbody=tbody, summary=summary)


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

        cur.execute('SELECT id FROM shoes WHERE shortName = ?', (shoes,))
        shoe_id = cur.fetchone()[0]

        cur.execute('SELECT id FROM wo_type WHERE type = ?', (wo_type,))
        wo_type_id = cur.fetchone()[0]

        sql.change_workout(conn, cur, id, date, location, wo_type_id, objective, notes,
                           distance, recovery, easy, threshold, interval, repetition, shoe_id)

        intro, thead, tbody, summary = sql.get_workouts(cur)
        return render_template("ListInfo.html", title='Listing of Workouts',
                               intro=intro, thead=thead, tbody=tbody, summary=summary)

    return render_template("ChangeWorkout.html",
                           val_date=val_date, val_location=val_location,
                           val_wo_type=val_wo_type, wo_type_list=wo_type_list,
                           val_objective=val_objective, val_notes=val_notes,
                           val_distance=val_distance, val_recovery=val_recovery,
                           val_easy=val_easy, val_threshold=val_threshold,
                           val_interval=val_interval, val_repetition=val_repetition,
                           val_shoe=val_shoe, shoe_list=shoe_list)


@app.route('/ListAthletes', methods=["GET", "POST"])
def list_athletes():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_athletes(conn, cur, letter='C')
    return render_template("ListInfo.html", title='Listing of Athletes',
                           intro=intro, thead=thead, tbody=tbody, summary=summary)


@app.route('/ListHealth', methods=["GET", "POST"])
def list_health():
    conn = get_db()
    cur = conn.cursor()
    intro, thead, tbody, summary = sql.get_health_list(cur)
    return render_template("ListInfo.html", title='Listing of Health',
                           intro='', thead=thead, tbody=tbody, summary=summary)


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

    if request.method == "POST":
        date = request.form['date']
        weight = request.form['weight']
        waist = request.form['waist']
        waist_bb = request.form['waist_bb']
        hips = request.form['hips']
        chest = request.form['chest']
        hr = request.form['HR']
        notes = request.form['notes']

        sql.change_health(conn, cur, id, date, weight, waist, waist_bb, hips, chest, notes, hr)

        intro, thead, tbody, summary = sql.get_health_list(cur)
        return render_template("ListInfo.html", title='Listing of Health',
                               intro='', thead=thead, tbody=tbody, summary=summary)

    return render_template("AddHealth.html",
                           val_date=val_date, val_weight=val_weight,
                           val_waist=val_waist, val_waist_bb=val_waist_bb,
                           val_chest=val_chest, val_hips=val_hips,
                           val_notes=val_notes, val_HR=val_hr)


@app.route('/AddHealth', methods=["GET", "POST"])
def add_health():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        date = request.form['date']
        weight = request.form['weight']
        waist = request.form['waist']
        waist_bb = request.form['waist_bb']
        chest = request.form['chest']
        hips = request.form['hips']
        hr = request.form['HR']
        notes = request.form['notes']
        sql.add_health(conn, cur, date, weight, waist, waist_bb, hips, chest, notes, hr)

        intro, thead, tbody, summary = sql.get_health_list(cur)
        return render_template("ListInfo.html", title='Listing of Health',
                               intro='', thead=thead, tbody=tbody, summary=summary)

    return render_template("AddHealth.html",
                           val_date=datetime.date.today().strftime('%Y-%m-%d'),
                           val_weight='0.0', val_waist='0.0', val_waist_bb='0.0',
                           val_chest='0.0', val_hips='0.0', val_notes='notes...', val_HR=60)


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

        logger.debug('shoes=%s', shoes)
        cur.execute('SELECT id FROM shoes WHERE shortName = ?', (shoes,))
        shoe_id = cur.fetchone()[0]

        logger.debug('wo_type=%s', wo_type)
        cur.execute('SELECT id FROM wo_type WHERE type = ?', (wo_type,))
        wo_type_id = cur.fetchone()[0]

        sql.add_workout(conn, cur, date, location, wo_type_id, objective, notes,
                        distance, recovery, easy, threshold, interval, repetition, shoe_id)

        intro, thead, tbody, summary = sql.get_workouts(cur)
        return render_template("ListInfo.html", title='Listing of Workouts',
                               intro=intro, thead=thead, tbody=tbody, summary=summary)

    return render_template("AddWorkout.html",
                           val_date=datetime.date.today().strftime('%Y-%m-%d'),
                           val_location='Location...', wo_type_list=wo_type_list,
                           val_objective='Objective', val_notes='Notes...',
                           val_distance='10.0', val_recovery='0:00:00',
                           val_easy='0:00:00', val_threshold='0:00:00',
                           val_interval='0:00:00', val_repetition='0:00:00',
                           shoe_list=shoe_list)


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

    if request.method == "POST":
        short_name = request.form['shortName']
        long_name = request.form['longName']
        sql.add_shoes(conn, cur, short_name, long_name)
        intro, thead, tbody, summary = sql.get_shoes(cur)

    return render_template("ShoeInput.html", intro=intro, thead=thead, tbody=tbody,
                           val_shortName='', val_longName='')


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


if __name__ == "__main__":
    # TODO: set debug=False before deploying to production
    app.run(debug=True, host='0.0.0.0', port=8080, passthrough_errors=True)
