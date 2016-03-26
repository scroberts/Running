#!/usr/bin/env python3

from flask import Flask, render_template, request, g
import sqlite3
import sql
import re

# global conn
# global cur
# global races

DATABASE = '/Users/sroberts/Dropbox/TMT/Python/Running/db/races.sqlite'
 
app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db
    
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods = ["GET", "POST"])
def Homepage():
    return render_template("homepage.html")

@app.route('/WorkoutWeekStats', methods = ["GET", "POST"])
def WorkoutWeekStats():
    conn = get_db()
    cur = conn.cursor()
    
    [intro, thead, tbody, summary] = sql.get_log_week_stats(conn, cur)
    title = 'Workout Statistics'

    return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

@app.route('/WorkoutMonthStats', methods = ["GET", "POST"])
def WorkoutMonthStats():
    conn = get_db()
    cur = conn.cursor()
    
    [intro, thead, tbody, summary] = sql.get_log_month_stats(conn, cur)
    title = 'Workout Statistics'

    return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

@app.route('/ListWorkouts', methods = ["GET", "POST"])
def ListWorkouts():

    conn = get_db()
    cur = conn.cursor()
    
    [intro, thead, tbody, summary] = sql.get_workouts(cur)
    title = 'Listing of Workouts'
    intro = ''
    return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

@app.route('/ChangeWorkout/<id>', methods = ["GET", "POST"])
def ChangeWorkout(id):
    conn = get_db()
    cur = conn.cursor()
    print('id = ', id)
    wo = sql.get_workout(cur, id)
    
    val_date = wo[0]
    val_location = wo[1]
    val_objective = wo[2]
    val_notes = wo[3]
    val_distance = wo[4]
    val_recovery = wo[5]
    val_easy = wo[6]
    val_threshold = wo[7]
    val_interval = wo[8]
    val_repetition = wo[9]
    val_shoe = wo[10]
    
    cur.execute('SELECT shortName FROM shoes ORDER BY shortName')
    
    shoe_list = [val_shoe]
    for row in cur:
        shoe_list.append(row[0])
        
    if request.method == "POST":
        print('entered POST request')
        date = request.form['date'] 
        location = request.form['location'] 
        objective = request.form['objective'] 
        notes = request.form['notes'] 
        distance = request.form['distance'] 
        recovery = request.form['recovery'] 
        easy = request.form['easy'] 
        threshold = request.form['threshold'] 
        interval = request.form['interval'] 
        repetition = request.form['repetition']         
        shoes = request.form['shoes']

        print('shoes = ', shoes)
        cur.execute('SELECT id FROM shoes WHERE shortName = ?', (shoes,))
        shoe_id = cur.fetchone()[0]
        
        sql.change_workout(id, conn, cur, date, location, objective, notes, distance, recovery, easy, threshold, interval, repetition, shoe_id)
        
        [intro, thead, tbody, summary] = sql.get_workouts(cur)
        title = 'Listing of Workouts'
        return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

    return(render_template("ChangeWorkout.html", val_date = val_date,
                val_location = val_location, val_objective = val_objective,
                val_notes = val_notes, val_distance = val_distance, 
                val_recovery = val_recovery, val_easy = val_easy,  
                val_threshold =  val_threshold, val_interval = val_interval, 
                val_repetition = val_repetition, val_shoe = val_shoe, shoe_list = shoe_list))

@app.route('/ListAthletes', methods = ["GET", "POST"])
def ListAthletes():
    conn = get_db()
    cur = conn.cursor()
    title = 'Listing of Athletes'
    [intro, thead, tbody, summary] = sql.get_athletes(conn, cur, Letter = 'C')
    return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)
    
@app.route('/ListHealth', methods = ["GET", "POST"])
def ListHealth():

    conn = get_db()
    cur = conn.cursor()
    
    [intro, thead, tbody, summary] = sql.get_health_list(cur)
    title = 'Listing of Health'
    intro = ''
    return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)


@app.route('/ChangeHealth/<id>', methods = ["GET", "POST"])
def ChangeHealth(id):
    conn = get_db()
    cur = conn.cursor()
    
    health = sql.get_health(cur, id)
    
    val_date = health[1]
    val_weight = health[2]
    val_waist = health[3]
    val_waist_bb = health[4]
    val_chest = health[5]
    val_hips = health[6]
    val_HR = health[7]
    val_notes = health[8]
    
    if request.method == "POST":
        date = request.form['date'] 
        weight = request.form['weight'] 
        waist = request.form['waist']    
        waist_bb = request.form['waist_bb']
        chest = request.form['chest'] 
        hips = request.form['hips'] 
        HR = request.form['HR']
        notes = request.form['notes'] 
        
        sql.change_health(conn, id, cur, date, weight, waist, waist_bb, chest, hips, notes, HR)
        
        [intro, thead, tbody, summary] = sql.get_health_list(cur)
        title = 'Listing of Health'
        intro = ''
        return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

    return(render_template("AddHealth.html", val_date = val_date,
                val_weight = val_weight, val_waist = val_waist,
                val_waist_bb =  val_waist_bb, val_chest = val_chest, 
                val_hips = val_hips, val_notes = val_notes, val_HR = val_HR))        


@app.route('/AddHealth', methods = ["GET", "POST"])
def AddHealth():
    conn = get_db()
    cur = conn.cursor()
    val_date = '2016-MM-DD'
    val_weight = '0.0'
    val_waist = '0.0'
    val_waist_bb = '0.0'
    val_chest = '0.0'
    val_hips = '0.0'
    val_notes = 'notes...'
    val_HR = 60
    
    if request.method == "POST":
        print('entered Health POST request')
        date = request.form['date'] 
        weight = request.form['weight'] 
        waist = request.form['waist']    
        waist_bb = request.form['waist_bb']
        chest = request.form['chest'] 
        hips = request.form['hips'] 
        HR = request.form['HR']
        notes = request.form['notes'] 
        sql.add_health(conn, cur, date, weight, waist, waist_bb, chest, hips, notes, HR)
        
        [intro, thead, tbody, summary] = sql.get_health_list(cur)
        title = 'Listing of Health'
        intro = ''
        return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

        
    return(render_template("AddHealth.html", val_date = val_date,
                val_weight = val_weight, val_waist = val_waist,
                val_waist_bb =  val_waist_bb, val_chest = val_chest, 
                val_hips = val_hips, val_notes = val_notes, val_HR = val_HR))


@app.route('/AddWorkout', methods = ["GET", "POST"])
def AddWorkout():

    conn = get_db()
    cur = conn.cursor()

    val_date = '2016-MM-DD'
    val_location = 'Location...'
    val_objective = 'Objective'
    val_notes = 'Notes...'
    val_distance = '10.0'
    val_recovery = '0:00:00'
    val_easy = '0:00:00'
    val_threshold = '0:00:00'
    val_interval = '0:00:00'
    val_repetition = '0:00:00'
    
    cur.execute('SELECT shortName FROM shoes ORDER BY shortName')
    
    shoe_list = []
    for row in cur:
        shoe_list.append(row[0])
    print('In homepage')
    
    if request.method == "POST":
        print('entered POST request')
        date = request.form['date'] 
        location = request.form['location'] 
        objective = request.form['objective'] 
        notes = request.form['notes'] 
        distance = request.form['distance'] 
        recovery = request.form['recovery'] 
        easy = request.form['easy'] 
        threshold = request.form['threshold'] 
        interval = request.form['interval'] 
        repetition = request.form['repetition']         
        shoes = request.form['shoes']

        print('shoes = ', shoes)
        cur.execute('SELECT id FROM shoes WHERE shortName = ?', (shoes,))
        shoe_id = cur.fetchone()[0]
        print('about to add workout\n')
        
        print('AddWorkout: recovery = %s, easy = %s, threshold = %s, interval = %s, repetition = %s' % (recovery, easy, threshold, interval, repetition))
        
        sql.add_workout(conn, cur, date, location, objective, notes, distance, recovery, easy, threshold, interval, repetition, shoe_id)
        
        print('Date =', date)
        print('Shoes =', shoes)
        [intro, thead, tbody, summary] = sql.get_workouts(cur)
        title = 'Listing of Workouts'
        return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

    
    return(render_template("AddWorkout.html", val_date = val_date,
                val_location = val_location, val_objective = val_objective,
                val_notes = val_notes, val_distance = val_distance, 
                val_recovery = val_recovery, val_easy = val_easy,  
                val_threshold =  val_threshold, val_interval = val_interval, 
                val_repetition = val_repetition, shoe_list = shoe_list))


@app.route('/ListShoes', methods = ["GET", "POST"])
def ListShoes():

    conn = get_db()
    cur = conn.cursor()
    
    [intro, thead, tbody, summary] = sql.get_shoes(cur)
    title = 'Listing of Shoes'
    intro = ''
    return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

@app.route('/AddShoes', methods = ["GET", "POST"])
def Addshoes():
    val_shortName = 'Short Name'
    val_longName = 'Long Name'
    
    conn = get_db()
    cur = conn.cursor()
    
    [intro,thead,tbody,summary] = sql.get_shoes(cur)

    if request.method == "POST":
        shortName = request.form['shortName'] 
        longName = request.form['longName'] 
        sql.add_shoes(conn, cur, shortName, longName)
        [intro,thead,tbody,summary] = sql.get_shoes(cur)
    
    return(render_template("ShoeInput.html", intro = intro, thead = thead, tbody = tbody))

@app.route('/Compare', methods = ["GET", "POST"])
def compare():

    conn = get_db()
    cur = conn.cursor()

    races = sql.get_races(cur)
    
    if request.method == "POST":
        race1 = request.form['race1'] 
        print('Race 1 =', race1)
        race2 = request.form['race2'] 
        print('Race 2 =', race2)
        min_time = request.form['min_time'] 
        print('Min Time =', min_time)
        max_time = request.form['max_time'] 
        print('Max Time =', max_time)
        percent = request.form['percent'] 
        print('Percent =', percent)       
        
        id_1 = int(re.search('\d+',re.search('\<\d+\>',race1).group()).group())
        print('id_1 = ',id_1)
        id_2 = int(re.search('\d+',re.search('\<\d+\>',race2).group()).group())
        print('id_2 = ',id_2)
        [eventname1, date1] = sql.get_race_info(cur,id_1)
        [eventname2, date2] = sql.get_race_info(cur,id_2)
        [intro, thead, tbody, summary] = sql.compare_races(cur, eventname1, date1, eventname2, date2, min_time, max_time, float(percent)/100)
        title = 'Comparison of Race Results'
        return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

    return render_template("CompareRaces.html", races = races)

@app.route('/user/<username>', methods = ["GET", "POST"])
def show_user_races(username):
    print('username = ', username)
    cur = get_db().cursor()
    [intro, thead, tbody, summary] = sql.get_races_for_athlete(cur, username)
    title = 'Races by Athlete'
    return render_template("ListInfo.html", title = title, intro = intro, thead = thead, tbody = tbody, summary = summary)

if __name__ == "__main__":
    app.run(debug = True, host='0.0.0.0', port=8080, passthrough_errors=True)
