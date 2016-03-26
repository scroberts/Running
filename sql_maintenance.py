#!/usr/bin/env python3

import re
import csv
import sqlite3
import time
import datetime
from datetime import timedelta
import numpy as np
from flask import Markup

import calendar
# from datetime import time
# from datetime import datetime, timedelta

import openpyxl
from openpyxl.styles import Font, Style, Alignment
from openpyxl.styles.colors import BLUE
from openpyxl import load_workbook

import sql

def compare_list_of_races(cur):
    percent_diff = 0.2
    compare_races(cur, 'Cobble Hill 10k', '2015-01-25', 'TC 10K', '2015-04-26', '0:35:00', '0:45:00', percent_diff)
    compare_races(cur, 'Cobble Hill 10k', '2015-01-25', 'Sooke 10k', '2015-04-19', '0:35:00', '0:45:00', percent_diff)
    compare_races(cur, 'Sooke 10k', '2015-04-19', 'TC 10K', '2015-04-26', '0:35:00', '0:45:00', percent_diff)
    compare_races(cur, 'Pioneer 8k', '2015-01-11', 'Hatley Castle 8k', '2015-02-22', '0:28:00', '0:36:00', percent_diff)
    compare_races(cur, 'Pioneer 8k', '2016-01-10', 'Hatley Castle 8k', '2016-02-21', '0:28:00', '0:36:00', percent_diff)
    compare_races(cur, 'Cedar 12k', '2015-02-08', 'Cedar 12k', '2016-02-07', '0:45:00', '0:55:00', percent_diff)
    compare_races(cur, 'Oak Bay Half Marathon', '2015-05-24', 'Victoria Half Marathon', '2015-10-11', '1:20:00', '1:40:00', percent_diff)
    compare_races(cur, 'Comox Valley Half Marathon', '2015-03-22', 'Oak Bay Half Marathon', '2015-05-24', '1:20:00', '1:40:00', percent_diff)
    compare_races(cur, 'Comox Valley Half Marathon', '2015-03-22', 'Victoria Half Marathon', '2015-10-11', '1:20:00', '1:40:00', percent_diff)

def rebuild_database(conn, cur):
#     cur.execute('DROP TABLE IF EXISTS Events ')
#     cur.execute('DROP TABLE IF EXISTS Athletes ')
#     cur.execute('DROP TABLE IF EXISTS RaceTimes ')
#     cur.execute('DROP TABLE IF EXISTS Races ')
#     
#     cur.execute('DROP TABLE IF EXISTS Shoes ')
    cur.execute('DROP TABLE IF EXISTS Log ')
    

#     cur.execute('CREATE TABLE Events (id INTEGER PRIMARY KEY, eventname TEXT, dist REAL, min_elev INTEGER, max_elev INTEGER, gain_elev INTEGER, UNIQUE (eventname))')
#     cur.execute('CREATE TABLE Races (id INTEGER PRIMARY KEY, eventID INTEGER, date TEXT, UNIQUE (eventID, date))')
#     cur.execute('CREATE TABLE Athletes (id INTEGER PRIMARY KEY, name TEXT, age_group TEXT, club TEXT, hometown TEXT, UNIQUE (name, hometown))')
#     cur.execute('CREATE TABLE RaceTimes (id INTEGER PRIMARY KEY, athleteID INTEGER, raceID INTEGER, str_time TEXT, sec_time INTEGER, pace TEXT )')
#     cur.execute('CREATE TABLE Shoes (id INTEGER PRIMARY KEY, shortName TEXT, longName TEXT, UNIQUE (shortName) )')
#     cur.execute('CREATE TABLE Log (id INTEGER PRIMARY KEY, date TEXT, location TEXT, objective TEXT, \
#                 notes TEXT, dist REAL, time TEXT, pace TEXT, recovery TEXT, easy TEXT, \
#                 threshold TEXT, interval TEXT, repetition TEXT, p8020 REAL, jd_int REAL, shoeID INTEGER, \
#                 UNIQUE (date, location, objective, dist, time))')
#     cur.execute('CREATE TABLE Health (id INTEGER PRIMARY KEY, date TEXT, weight REAL, smallWaist REAL, bbWaist REAL, hip REAL, chest REAL, notes TEXT, UNIQUE (date) )')
    
#     add_event(conn, cur, 'Cedar 12k', 12.0, 23, 61, 108)
#     add_event(conn, cur, 'Cobble Hill 10k', 10.0, 62, 123, 75)
#     add_event(conn, cur, 'Pioneer 8k', 8.0, 67, 70, 22)
#     add_event(conn, cur, 'Cowichan Half Marathon', 21.0975, 0, 0, 0)
#     add_event(conn, cur, 'Victoria Half Marathon', 21.0975, 14, 36, 128)
#     add_event(conn, cur, 'Victoria Marathon', 42.195, 14, 36, 128)
#     add_event(conn, cur, 'MEC Race 1', 10.0, 0, 0, 0)
#     add_event(conn, cur, 'MEC Race 4', 15.0, 0, 0, 0)
#     add_event(conn, cur, 'Oak Bay Half Marathon', 21.0975, 0, 25, 111)
#     add_event(conn, cur, 'TC 10K', 10.0, 15, 30, 51)
#     add_event(conn, cur, 'Sooke 10k', 10.0, 16, 54, 72)
#     add_event(conn, cur, 'Comox Valley Half Marathon', 21.0975, 12, 101, 133)
#     add_event(conn, cur, 'Bazan Bay 5k', 5.0, 4, 19, 25)
#     add_event(conn, cur, 'Hatley Castle 8k', 8.0, 16, 101, 146)
# 
#     load_result(conn, cur, 'ComoxHalf_2016.csv', 'Comox Valley Half Marathon', '2016-03-20', 21.0975, 0, 0, 0)
#     load_result(conn, cur, 'Bazan5k_2016.csv', 'Bazan Bay 5k', '2016-03-06', 5.0, 4, 19, 25)
#     load_result(conn, cur, 'Hatley8k_2016.csv', 'Hatley Castle 8k', '2016-02-21', 8.0, 16, 101, 146)
#     load_result(conn, cur, 'Cedar12k_2016.csv', 'Cedar 12k', '2016-02-07', 12.0, 23, 61, 108)
#     load_result(conn, cur, 'Cobble10k_2016.csv', 'Cobble Hill 10k', '2016-01-24', 10.0, 62, 123, 75)
#     load_result(conn, cur, 'Pioneer8k_2016.csv', 'Pioneer 8k','2016-01-10', 8.0, 67, 70, 22)
# 
#     load_result(conn, cur, 'CowichanHalf_2015.csv', 'Cowichan Half Marathon','2014-10-25', 21.0975, 0, 0, 0)
#     load_result(conn, cur, 'VictoriaHalf_2015.csv', 'Victoria Half Marathon','2015-10-11', 21.0975, 14, 36, 128)
#     load_result(conn, cur, 'MEC_Race4_2015.csv', 'MEC Race 4','2015-09-06', 15.0, 0, 0, 0)
#     load_result(conn, cur, 'OakBayHalf_2015.csv', 'Oak Bay Half Marathon','2015-05-24', 21.0975, 0, 25, 111)
#     load_result(conn, cur, 'OakBayHalf_2012.csv', 'Oak Bay Half Marathon','2012-05-13', 21.0975, 0, 25, 111)
#     load_result(conn, cur, 'tc10k_2015.csv', 'TC 10K', '2015-04-26', 10.0, 15, 30, 51)
#     load_result(conn, cur, 'Sooke10k_2015.csv', 'Sooke 10k','2015-04-19', 10.0, 0, 0, 0)
#     load_result(conn, cur, 'ComoxHalf_2015.csv', 'Comox Valley Half Marathon', '2015-03-22', 21.0975, 0, 0, 0)
#     load_result(conn, cur, 'Bazan5k_2015.csv', 'Bazan Bay 5k', '2015-03-08', 5.0, 4, 19, 25)
#     load_result(conn, cur, 'Hatley8k_2015.csv', 'Hatley Castle 8k','2015-02-22', 8.0, 16, 101, 146)
#     load_result(conn, cur, 'Cedar12k_2015.csv', 'Cedar 12k', '2015-02-08', 12.0, 23, 61, 108)
#     load_result(conn, cur, 'Cobble10k_2015.csv', 'Cobble Hill 10k', '2015-01-25', 10.0, 0, 0, 0)
#     load_result(conn, cur, 'MEC_Race1_2015.csv','MEC Race 1', '2015-01-18', 10.0, 0, 0, 0)
#     load_result(conn, cur, 'Pioneer8k_2015.csv', 'Pioneer 8k', '2015-01-11', 8.0, 67, 70, 22)
# 
#     load_result(conn, cur, 'CowichanHalf_2014.csv', 'Cowichan Half Marathon', '2014-10-26', 21.0975, 0, 0, 0)
#     load_result(conn, cur, 'VictoriaHalf_2014.csv', 'Victoria Half Marathon', '2014-10-12', 21.0975, 0, 0, 0)
#     load_result(conn, cur, 'VictoriaMarathon_2014.csv', 'Victoria Marathon', '2014-10-12', 42.195, 0, 0, 0)
#     load_result(conn, cur, 'tc10k_2014.csv', 'TC 10K', '2014-04-27', 10.0, 0, 0, 0)

def update_racetimes_time(conn,cur):
    cur.execute('SELECT id, str_time FROM Racetimes')
    curlist = cur.fetchall()
    
    for row in curlist:  
        cur.execute('UPDATE Racetimes SET str_time = ? WHERE id = ?',(sql.scrub_timestr(row[1]),row[0]))
    conn.commit()
    
def update_racetimes_pace(conn,cur):
    cur.execute('SELECT id, pace FROM Racetimes')
    curlist = cur.fetchall()
    
    for row in curlist:  
        cur.execute('UPDATE Racetimes SET pace = ? WHERE id = ?',(sql.scrub_pace(row[1]),row[0]))
    conn.commit()
    
def update_isodate(conn,cur):
    cur.execute('SELECT id, date FROM Log')
    curlist = cur.fetchall()
    
    for row in curlist:  
        isodate = datetime.datetime.strptime(row[1],'%Y-%m-%d').isocalendar()
        year = '%s' % isodate[0]
        week = '%s' % isodate[1]
        day = '%s' % isodate[2]
        isodatestr = year + '-' + week.zfill(2) + '-' + day
        print(row[0], isodatestr)
        cur.execute('UPDATE Log SET isodate = ? WHERE id = ?',(isodatestr,row[0]))
    conn.commit()
    
def update_secs(conn,cur):
    cur.execute('SELECT id, time, pace, recovery, easy, threshold, interval, repetition FROM Log')
    curlist = cur.fetchall()
    
    for row in curlist:  
        id = row[0]
        time_secs = secs(row[1])
        pace_secs = secs(row[2])
        recovery_secs = secs(row[3])
        easy_secs = secs(row[4])
        threshold_secs = secs(row[5])
        interval_secs = secs(row[6])
        repetition_secs = secs(row[7])
        
        print(row)
        
        cur.execute('UPDATE Log SET time_secs = ?, pace_secs = ?, recovery_secs = ?, easy_secs = ?, threshold_secs = ?, interval_secs = ?, repetition_secs = ? WHERE id = ?',(time_secs, pace_secs, recovery_secs, easy_secs, threshold_secs, interval_secs, repetition_secs, id))
    conn.commit()

def main_sql():

    [conn, cur] = sql.load_database('/Users/sroberts/Dropbox/TMT/Python/SQL/races.sqlite')    
    update_racetimes_pace(conn,cur)
        
    cur.close()

if __name__ == "__main__":
	main_sql()



#     rebuild_database(conn, cur)

#     races = get_races(cur)
#     print(races)
    
#     compare_list_of_races(cur)
#     [eventname1, date1] = get_race_info(cur,4)
#     [eventname2, date2] = get_race_info(cur,1)
#     compare_races(cur, eventname1, date1, eventname2, date2, "0:00:00", "4:00:00", 0.2)
#     
#     get_races_for_athlete(cur, 'Scott Roberts')
    
#     write_ss(conn, cur, 'workouts.xlsx')

    # print('Athletes:')
    # cur.execute('SELECT name, club FROM Athletes WHERE age_group = "M30-34"')
    # for row in cur:
    #     print(row)
    
    # print('\n\nFinish times close to me')
    # cur.execute('SELECT Athletes.name, Races.racename, RaceTimes.str_time, RaceTimes.pace FROM RaceTimes \
    #     JOIN Athletes ON Racetimes.athleteID = Athletes.id \
    #     JOIN Races ON Racetimes.raceID = Races.id \
    #     WHERE RaceTimes.str_time BETWEEN "0:41:00" AND "0:41:40" \
    #     ORDER BY Athletes.name')
    # for row in cur:
    #     print(row)
    

    # cur.execute('SELECT Athletes.name, RaceTimes.racename, RaceTimes.str_time, RaceTimes.pace FROM RaceTimes \
    #     JOIN Athletes ON Racetimes.athleteID = Athletes.id \
    #     WHERE racename IN ("TC10K 2015", "Cobble Hill 2015") \
    #     GROUP BY Racetimes.athleteID HAVING COUNT(Racetimes.athleteID) > 1 ')


    # print('\n\nFind Athlete')
    # cur.execute('SELECT * FROM Athletes WHERE name = "Mike Janes" ')

    # record = cur.fetchone()
    # if record == None:
    #     print('Name not found')
    # else:
    #     print(record)        

    # for row in cur:
    #     print(row)
    
    # Read the workout log into the database
#     path = r'/Users/sroberts/Dropbox/TMT/Python/SQL/SQLExerciseLog.xlsx'  
    # Open the spreadsheet
#     wb=openpyxl.load_workbook( path, data_only=True )

    # read the running log by sheet name
#     sheet = wb.get_sheet_by_name('Sheet')

    # Read in the spreadsheet to a dictionary structure
#     read_ss( sheet, conn, cur )

