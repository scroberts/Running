#!/usr/bin/env python3

import re
import csv
import sqlite3
import time
#import datetime
from datetime import datetime, timedelta
import numpy as np
from flask import Markup

import calendar
# from datetime import time
# from datetime import datetime, timedelta

import openpyxl
from openpyxl.styles import Font, Style, Alignment
from openpyxl.styles.colors import BLUE
from openpyxl import load_workbook

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

# Set Excel Styles
# Excel hyperlink style is calibri 11, underline blue
font_url_style = Font(color = BLUE, underline = 'single')
bold_style = Font(bold = True)
align_hv_cen_style = Alignment(horizontal = 'center', vertical = 'center')
align_ver_cen_style = Alignment(vertical = 'center')
align_wrap_cen_style = Alignment(wrap_text = True, vertical = 'center')

def parse_datestr(datestr):
    m = re.search('(^\d*)-(\d*)-(\d*)', datestr)
    return([m.group(1), m.group(2), m.group(3)])

def scrub_timestr(timestr):
    m = re.search('(^\d*):(\d*):(\d*)', timestr)
    hours = '%s' % int(m.group(1))
    mins = '%s' % int(m.group(2))
    secs = '%s' % int(m.group(3))
    return(hours + ':' + mins.zfill(2) + ':' + secs.zfill(2))
    
def timestr2pacestr(timestr):
    m = re.search('(^\d*):(\d*):(\d*)', timestr)
    hours = '%s' % int(m.group(1))
    mins = '%s' % int(m.group(2))
    secs = '%s' % int(m.group(3))
    return(mins + ':' + secs.zfill(2))
    
def scrub_pace(pacestr):
    m = re.search('(^\d*):(\d*)', pacestr)
    mins = '%s' % int(m.group(1))
    secs = '%s' % int(m.group(2))
    return(mins + ':' + secs.zfill(2))

def get_running_dict(conn, cur):
    cur.execute('SELECT Log.id, date, location, objective, notes, dist, time, pace, recovery, easy, \
                 threshold, interval, repetition, p8020, jd_int, shortName FROM Log \
                 JOIN Shoes ON Log.ShoeID = Shoes.id \
                 ORDER BY date')

    myRun = {}
    
    idx = 1
    
    for row in cur:

        myRun[idx] = {}       
#         print('date = ', row[1])
        myRun[idx]['id'] = row[0]
        myRun[idx]['date'] = datetime.strptime(row[1],'%Y-%m-%d')
        myRun[idx]['weekday'] = 'Monday'
        myRun[idx]['description'] = row[2]
        myRun[idx]['objective'] = row[3]
        myRun[idx]['notes'] = row[4]
        myRun[idx]['distance'] = row[5]
        myRun[idx]['time_run'] = row[6]
        myRun[idx]['pace'] = row[7]
        myRun[idx]['time_recovery'] = row[8]
        myRun[idx]['time_easy'] = row[9]
        myRun[idx]['time_tempo'] = row[10]
        myRun[idx]['time_interval'] = row[11]
        myRun[idx]['time_repetition'] = row[12]
        myRun[idx]['time_80_20'] = row[13]
        myRun[idx]['JD_Intensity'] = row[14]
        myRun[idx]['shoes'] = row[15]
        idx += 1
                
    return myRun

def read_ss(sheet, conn, cur):
    # define indices for spreadsheet row and dictionary row
    ssrow = 5
    dicrow = 1
    myRun = {}

    while sheet.cell(row=ssrow, column=1).value:
        print('\ndate = ',sheet.cell(row=ssrow, column=1).value) 
    
        # assign columns from spreadsheet to variables
        date = sheet.cell(row = ssrow, column = 1).value
        location = sheet.cell(row = ssrow, column = 2).value
        objective = sheet.cell(row = ssrow, column = 3).value
        notes = sheet.cell(row = ssrow, column = 4).value
        distance = sheet.cell(row = ssrow, column = 5).value
        time = sheet.cell(row = ssrow, column = 6).value
        if not time:
            time = "0:00:00"
        else: 
            time = '%s' % time
        pace = sheet.cell(row = ssrow, column = 7).value
        recovery = sheet.cell(row = ssrow, column = 8).value
        if not recovery:
            recovery = "0:00:00"
        else: 
            recovery = '%s' % recovery        
        easy = sheet.cell(row = ssrow, column = 9).value
        if not easy:
            easy = "0:00:00"
        else:
            easy = '%s' % easy
        threshold = sheet.cell(row = ssrow, column = 10).value
        if not threshold:
            threshold = "0:00:00"  
        else: 
            threshold = '%s' % threshold     
        interval = sheet.cell(row = ssrow, column = 11).value
        if not interval:
            interval = "0:00:00" 
        else: 
            interval = '%s' % interval        
        repetition = sheet.cell(row = ssrow, column = 12).value
        if not repetition:
            repetition = "0:00:00" 
        else: 
            repetition = '%s' % repetition   
        if recovery == "0:00:00" and easy == "0:00:00" and threshold == "0:00:00" and interval == "0:00:00" and repetition == "0:00:00":
            easy = time   
        time_80_20 = sheet.cell(row = ssrow, column = 13).value
        intensity = sheet.cell(row = ssrow, column = 14).value
        shoes = sheet.cell(row = ssrow, column = 15).value
    
        cur.execute('SELECT id FROM shoes WHERE shortName = ?', (shoes,))
        shoe_id = cur.fetchone()[0]

        print('times ', time, recovery, easy, threshold, interval, repetition)
        add_workout(conn, cur, date, location, objective, notes, distance, recovery, easy, threshold, interval, repetition, shoe_id)

        ssrow += 1
        dicrow += 1

    return
    
def write_ss(conn, cur, xlfile):

    wb = openpyxl.Workbook()
    ws = wb.worksheets[0]
    
    rownum = 4
    col = 1
	
    # Write spreadsheet headings
    
    # date
    ws.cell(row = rownum, column = col).value = "Date"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # location
    col += 1
    ws.cell(row = rownum, column = col).value = "Location"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # objective
    col += 1
    ws.cell(row = rownum, column = col).value = "Objective"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # notes
    col += 1
    ws.cell(row = rownum, column = col).value = "Notes"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # dist
    col += 1
    ws.cell(row = rownum, column = col).value = "Dist"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # time
    col += 1
    ws.cell(row = rownum, column = col).value = "Time"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # pace
    col += 1
    ws.cell(row = rownum, column = col).value = "Pace"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # recovery
    col += 1
    ws.cell(row = rownum, column = col).value = "Recovery"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # easy
    col += 1
    ws.cell(row = rownum, column = col).value = "Easy"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # threshold
    col += 1
    ws.cell(row = rownum, column = col).value = "Threshold"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # interval
    col += 1
    ws.cell(row = rownum, column = col).value = "Interval"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # repetition
    col += 1
    ws.cell(row = rownum, column = col).value = "Repetition"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # p8020
    col += 1
    ws.cell(row = rownum, column = col).value = "80/20"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # intensity
    col += 1
    ws.cell(row = rownum, column = col).value = "Intensity"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    # shoes
    col += 1
    ws.cell(row = rownum, column = col).value = "Shoes"
    ws.cell(row = rownum, column = col).alignment = align_hv_cen_style 
    
    colmax = col + 1
    for col in range(1, colmax):
        ws.cell(row = rownum, column = col).font = bold_style
        
    [intro, thead, tbody, summary] = get_workouts(cur)
    
    ssrow = rownum
    
    for row in tbody:
        col = 1
        ssrow += 1
        
        # Column 1: Date
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment = align_hv_cen_style 
        # Column 2: Location
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_wrap_cen_style
        # Column 3: Objective
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_wrap_cen_style 
        # Column 4: Notes
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_wrap_cen_style 
        # Column 5: Distance
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style  
        # Column 6: time
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style 
        # Column 7: Pace
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style 
        # Column 8: Recovery
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style 
        # Column 9: Easy
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style  
        # Column 10: Threshold
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style  
        # Column 11: Interval
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style  
        # Column 12: Repetition
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style  
        # Column 13: p8020
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style  
        # Column 14: Intensity
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_hv_cen_style  
        # Column 15: Shoes
        col +=1
        ws.cell(row = ssrow, column = col).value = row[col-1]
        ws.cell(row = ssrow, column = col).alignment =  align_wrap_cen_style
        
#         Set column widths
        ws.column_dimensions["A"].width = 8.0
        ws.column_dimensions["B"].width = 20.0
        ws.column_dimensions["C"].width = 10.0
        ws.column_dimensions["D"].width = 40.0
        ws.column_dimensions["E"].width = 10.0
        ws.column_dimensions["F"].width = 10.0    
        ws.column_dimensions["G"].width = 10.0
        ws.column_dimensions["H"].width = 10.0
        ws.column_dimensions["I"].width = 10.0
        ws.column_dimensions["J"].width = 10.0
        ws.column_dimensions["K"].width = 10.0
        ws.column_dimensions["L"].width = 10.0
        ws.column_dimensions["M"].width = 10.0
        ws.column_dimensions["N"].width = 10.0
        ws.column_dimensions["O"].width = 20.0

        # Save the spreadsheet
        wb.save(xlfile)

def secs(str_time):
    # Returns number of seconds in time string formatted as HH:MM:SS
    x=time.strptime(str_time,'%H:%M:%S')
    return(timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds())

def str_time(secs):
    # Returns time string for a number of seconds
    return(str(timedelta(seconds=round(secs))))

def load_csv_health(conn, cur, csvfilename):
    with open(csvfilename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row['Date'], row['Weight (kg)'], row['Waist'], row['Waist at bb'], row['Hip'], row['Chest'], row['Notes'])
            try:
                add_health(conn, cur, row['Date'], row['Weight (kg)'], row['Waist'], \
                    row['Waist at bb'], row['Hip'], row['Chest'], row['Notes'])
            except:
                print('Error importing CSV file for Health')
                exit(1)        
    conn.commit()

def add_health(conn, cur, date, weight, smallWaist, bbWaist, hip, chest, notes, HR):
    try:
        cur.execute('INSERT INTO Health (date, weight, smallWaist, bbWaist, hip, chest, notes, HR) VALUES ( ?,?,?,?,?,?,?,? )', ( date, weight, smallWaist, bbWaist, hip, chest, notes, HR)) 
    except:
        print('Error - unable to enter heath, date = ', date)   
    conn.commit() 

def change_health(conn, id, cur, date, weight, smallWaist, bbWaist, hip, chest, notes, HR):
    try:
        cur.execute('UPDATE Health SET date=?, weight=?, smallWaist=?, bbWaist=?, hip=?, chest=?, notes=?, HR=? WHERE id = ?', ( date, weight, smallWaist, bbWaist, hip, chest, notes, HR, id)) 
    except:
        print('Error - unable to update heath record, id = ', id)   
    conn.commit() 

def get_health(cur, id):
    cur.execute('SELECT id, date, weight, smallWaist, bbWaist, hip, chest, HR, notes FROM Health WHERE id = ?', (id,))
    health = list(cur.fetchone())
    return(health)
    
def get_health_list(cur):
    cur.execute('SELECT id, date, weight, smallWaist, bbWaist, hip, chest, HR, notes FROM Health ORDER BY date DESC')

    intro = ['Listing of Health']
    thead = ['ID', 'Date', 'Weight', 'Waist', 'Waist at BB', 'Hip', 'Chest', 'HR', 'Notes']
    tbody = []
    for row in cur:
        row = list(row)
        row[0] = Markup('<strong><a href=http://localhost:8080/ChangeHealth/%s>%s</a></strong>' % (row[0],row[0]))
        tbody.append(row)
#         print(row)
    summary = 'Total of %d Entries' % len(tbody) 
    return( [intro,thead,tbody, summary] )  
    
# def get_recent_weight(cur):
    
    
def get_weight_report(cur):
    cur.execute('SELECT date FROM Health WHERE (weight > 0) ORDER BY date DESC')
    dates = []
    # create a list of dates as ascii strings
    for row in cur:
        dates.append(row[0])
    # find datetime format dates that span a week centered on date from list above
    datelist = []
    weightlist = []
    for strdate in dates:
        # get date span of week
        date = datetime.strptime(strdate,'%Y-%m-%d')
        datelist.append(date)
        date_3_days_ago = date - timedelta(days=3)
        date_3_days_future =  date + timedelta(days=3)
        #print(date.strftime('%Y-%m-%d'), date_3_days_ago.strftime('%Y-%m-%d'), date_3_days_future.strftime('%Y-%m-%d'))
        start = date_3_days_ago.strftime('%Y-%m-%d')
        end = date_3_days_future.strftime('%Y-%m-%d')
        print(start, end )
        try:
            cur.execute('SELECT AVG(weight) FROM Health WHERE (date between ? AND ?) AND weight > 0.0', (start, end))
#             for row in cur:
#                 print(strdate,' : %.2f' % row[0])
#             weightlist.append(row[0])
            weightlist.append(cur.fetchone())
        except:
            pass
#             print('No entries')
            
    # now print

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    #plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(90))
#     plt.plot([datetime.strptime('2016-10-01','%Y-%m-%d'),datetime.strptime('2016-10-02','%Y-%m-%d'),datetime.strptime('2016-10-03','%Y-%m-%d')],[1,2,30])
    plt.plot(datelist,weightlist)
    plt.gcf().autofmt_xdate()      
    plt.savefig('static/weight.png')
    # plt.show() 
    plt.clf()


        
def add_shoes(conn, cur, shortName, longName):
    print('Adding new shoes', shortName, longName)
    try:
        cur.execute('INSERT INTO Shoes (shortName, longName, retired) VALUES ( ?,?,? )', ( shortName, longName, 0 )) 
    except:
        print('Error - check if shoe already exists in table')   
    conn.commit() 
    
def get_shoes(cur):
#     cur.execute('SELECT id, shortName, longName FROM shoes ORDER BY shortName')

    cur.execute('SELECT Shoes.id, shortName, longName, sum(dist), max(date)  FROM Shoes \
                JOIN Log WHERE log.shoeID = Shoes.id GROUP BY log.shoeID ORDER BY max(date) DESC')

#     SELECT shoeID, sum(dist) FROM Log GROUP BY shoeID

    intro = ['Listing of Shoes']
    thead = ['ID', 'Short Name', 'Long Name', 'Dist', 'Date Last Used']
    tbody = []
    for row in cur:
        row = list(row)
        row[3] = '%.1f' % row[3]
        tbody.append(row)
    summary = 'Total of %d Entries' % len(tbody)
    return( [intro,thead,tbody,summary] )
 
def get_workout_calculated_data(date, distance, recovery, easy, threshold, interval, repetition):
    secs_recovery = secs(recovery)
    secs_easy = secs(easy)
    secs_threshold = secs(threshold)
    secs_interval = secs(interval)
    secs_repetition = secs(repetition)
    
    total_time = secs_recovery + secs_easy + secs_threshold + secs_interval + secs_repetition
    total_time_str = str_time(total_time)
    secs_pace = total_time/float(distance)
    pace = str_time(total_time/float(distance))
    
    # Calculate Percent 80/20
    p8020 = 100.0 * (secs_recovery + secs_easy)/total_time
    
    # Calculate Jack Daniels Intensity
    recovery_int = secs_recovery/60.0 * 0.15
    easy_int = secs_easy/60.0 * 0.2
    tempo_int = secs_threshold/60.0 * 0.6
    interval_int = secs_interval/60.0 * 1.0
    repetition_int = secs_repetition/60.0 * 1.5
    jd_int = recovery_int + easy_int + tempo_int + interval_int + repetition_int
    
    isodate = datetime.strptime(date,'%Y-%m-%d').isocalendar()
    year = '%s' % isodate[0]
    week = '%s' % isodate[1]
    day = '%s' % isodate[2]
    isodatestr = year + '-' + week.zfill(2) + '-' + day
    return([isodatestr,total_time_str, total_time, pace, secs_pace, secs_recovery, secs_easy, secs_threshold, secs_interval, secs_repetition, p8020, jd_int])

 
def change_workout(id, conn, cur, date, location, wo_type_id, objective, notes, distance, recovery, easy, threshold, interval, repetition, shoe_id):
    print('Changing Workout ID: ',id)
    
    [isodatestr, total_time_str, total_time, pace, secs_pace, secs_recovery, secs_easy, secs_threshold, secs_interval, secs_repetition, p8020, jd_int] = get_workout_calculated_data(date, distance, recovery, easy, threshold, interval, repetition)
    
    try:
        cur.execute('UPDATE Log SET date=?, location=?, wo_type=?, objective=?, notes=?, dist=?, \
                    time = ?, time_secs = ?, pace = ?, pace_secs = ?, recovery = ?, \
                    recovery_secs = ?, easy = ?, easy_secs = ?, threshold = ?, \
                    threshold_secs = ?, interval = ?, interval_secs = ?, repetition = ?, \
                    repetition_secs = ?, p8020 = ?, jd_int = ?, shoeID = ?, isodate = ? WHERE id = ?',
                    (date, location, wo_type_id, objective, notes, float(distance), total_time_str, 
                    total_time, pace, secs_pace, recovery, secs_recovery, easy, secs_easy, 
                    threshold, secs_threshold, interval, secs_interval, repetition, 
                    secs_repetition, p8020, jd_int, shoe_id, isodatestr, id ))
        conn.commit() 

    except:
        print('Error - log entry couldn\'t be changed')   

        
def add_workout(conn, cur, date, location, wo_type_id, objective, notes, distance, recovery, easy, threshold, interval, repetition, shoe_id):
    print('Adding Workout for Date: ',date)
    
    [isodatestr,total_time_str, total_time, pace, secs_pace, secs_recovery, secs_easy, secs_threshold, secs_interval, secs_repetition, p8020, jd_int] = get_workout_calculated_data(date, distance, recovery, easy, threshold, interval, repetition)
    
#     print('Jack Daniels Intensity = ',jd_int)
#     print('Pace = ', pace)
#     print('SQL AddWorkout: recovery = %s, easy = %s, threshold = %s, interval = %s, repetition = %s' % (recovery, easy, threshold, interval, repetition))

    cur.execute('INSERT INTO Log (date, location, wo_type, objective, notes, dist, time, time_secs, pace, pace_secs, recovery, recovery_secs, easy, easy_secs, threshold, threshold_secs, interval, interval_secs, repetition, repetition_secs, p8020, jd_int, shoeID, isodate) VALUES \
                ( ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,? )', 
        ( date, location, wo_type_id, objective, notes, float(distance), total_time_str, total_time, pace, secs_pace, recovery, secs_recovery, easy, secs_easy, threshold, secs_threshold, interval, secs_interval, repetition, secs_repetition, p8020, jd_int, shoe_id, isodatestr )) 

    conn.commit() 
    
def get_workout(cur, id):
    cur.execute('SELECT date, location, type, objective, notes, dist, recovery, easy, \
                 threshold, interval, repetition, shortName FROM Log \
                 JOIN Shoes ON Log.ShoeID = Shoes.id \
                 JOIN wo_type ON Log.wo_type = wo_type.id \
                WHERE Log.id = ?', ( id , ))
                 
    workout = list(cur.fetchone())    
#     print(workout)
    return(workout)
    

def get_workouts(cur):
    cur.execute('SELECT Log.id, date, location, objective, notes, dist, time, pace, recovery, easy, \
                 threshold, interval, repetition, p8020, jd_int, shortName FROM Log \
                 JOIN Shoes ON Log.ShoeID = Shoes.id \
                 ORDER BY date DESC')

                
    intro = ['Listing of Workouts']

    thead = ['ID','Run Date','Workout Description', 'Dist', 'Time', 'Pace', 'Time in Zones', 
            '80/20', 'JD Intensity', 'Shoes']    

    print(intro)
    
    f = open('workout_listing.txt','w')

    tbody = []
    for row in cur:
        row = list(row)
        id_tag = Markup('<strong><a href=http://localhost:8080/ChangeWorkout/%s>%s</a></strong>' % (row[0],row[0]))
        date = Markup('%s' % row[1])
        location = row[2]
        objective = row[3]
        notes = row[4]
        dist = row[5]
        time = row[6]
        pace = row[7]
        recovery = row[8]
        easy = row[9]
        threshold = row[10]
        interval = row[11]
        repetition = row[12]
        p8020 = '% .1f%%' % row[13] 
        intensity = '% .2f' % row[14] 
        shoes = row[15]
                
        if location is None:
            location = ''
        if objective is None:
            objective = ''
        if notes is None:
            notes = ''
        description = Markup('<strong>Location: </strong>' + location + '<br /><strong>Objective: </strong>' + objective + '<br /><strong>Notes: </strong>' + notes)

        zones = zones_str(recovery, easy, threshold, interval, repetition)
        
        tbody.append([id_tag, date, description, dist, time, pace, zones, 
                p8020, intensity, shoes])
                
        print(row[0],row[1],location,objective,dist,time,pace,recovery,easy,threshold,interval,repetition,p8020,intensity,shoes,sep='|',file=f)

    summary = 'Total of %d Workouts' % len(tbody) 
    
    f.close()
    
    return([intro, thead, tbody, summary])

def zones_str(recovery, easy, threshold, interval, repetition):
    zones = ''
    if recovery != '0:00:00':
        zones += '<strong>Recovery: </strong>' + recovery + '\n'
    if easy != '0:00:00':
        zones += '<strong>Easy: </strong>' + easy + '\n'      
    if threshold != '0:00:00':
        zones += '<strong>Threshold: </strong>' + threshold + '\n' 
    if interval != '0:00:00':
        zones += '<strong>Interval: </strong>' + interval + '\n' 
    if repetition != '0:00:00':
        zones += '<strong>Repetition: </strong>' + repetition + '\n'
    return(Markup(zones))

def add_event(conn, cur, racename, dist, min_elev, max_elev, gain_elev):
    print('Adding Event: ',racename)
    try:
        cur.execute('INSERT INTO Events (eventname, dist, min_elev, max_elev, gain_elev) VALUES ( ?,?,?,?,? )', ( racename, dist, min_elev, max_elev, gain_elev )) 
    except:
        print('Event already exists in table')   
    conn.commit()     

def test_load_result(conn, cur, csvfilename, eventname, date, dist, min_elev, max_elev, gain_elev):
    print('Test loading results for ',eventname)
    
    cur.execute('SELECT id FROM Events WHERE (eventname = ?) LIMIT 1', ( eventname , ))
    eventID = cur.fetchone()[0]
    
    print('Found eventID:', eventID, ' for eventname') 
        
#     cur.execute('SELECT id FROM Races WHERE eventID = ? AND date = ? LIMIT 1', ( eventID , date ))
#     raceID = cur.fetchone()[0]
#     
#     print('Found raceID:', raceID, ' for eventID') 
  
    with open(csvfilename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row['name'], row['age_group'], row['club'], row['hometown'], scrub_timestr(row['time']), secs(row['time']), row['pace'])  
        

def load_result(conn, cur, csvfilename, eventname, date, dist, min_elev, max_elev, gain_elev):
    print('Loading results for ',eventname)
    
    cur.execute('SELECT id FROM Events WHERE (eventname = ?) LIMIT 1', ( eventname , ))
    eventID = cur.fetchone()[0]
    
    try:
        cur.execute('INSERT INTO Races (eventID, date) VALUES (?,?) ', ( eventID , date, )) 
    except:
        print('Racename already exists in table')
        exit(0)  
        
    cur.execute('SELECT id FROM Races WHERE eventID = ? AND date = ? LIMIT 1', ( eventID , date ))
    raceID = cur.fetchone()[0]
  
    with open(csvfilename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                cur.execute('INSERT INTO Athletes (name, age_group, club, hometown) VALUES ( ?, ?, ?, ? )', ( row['name'], row['age_group'], row['club'], row['hometown'],))    
            except:
                pass            
    conn.commit()

    with open(csvfilename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cur.execute('SELECT id FROM Athletes WHERE (name = ? AND hometown = ?) LIMIT 1', ( row['name'], row['hometown'], ))
            AthleteID = cur.fetchone()[0]
            print(AthleteID, raceID, row['time'], row['pace'] )
            try:
                cur.execute('INSERT INTO RaceTimes (athleteID, raceID, str_time, sec_time, pace) VALUES ( ?, ?, ?, ?, ?)', ( AthleteID, raceID, scrub_timestr(row['time']), secs(row['time']), row['pace'] ) )    
            except:
                print('Error adding to RaceTimes')
                exit(1)
    conn.commit()
    
def get_race_info(cur, race_id):
    cur.execute('SELECT eventname, date FROM Races JOIN Events WHERE Races.id = ? AND Events.id = Races.eventID',(race_id,))
    result = cur.fetchall()
    eventname = result[0][0]
    date = result[0][1]
    return([eventname, date])
    
def get_races_for_athlete(cur, name):
    cur.execute('SELECT eventname, date, str_time, pace FROM RaceTimes \
                JOIN Athletes ON RaceTimes.athleteID = Athletes.id \
                JOIN Races ON RaceTimes.raceID = Races.id \
                JOIN Events ON Events.id = Races.eventID \
                WHERE Athletes.name = ? ORDER BY date DESC',(name,))
                
    intro = [name]
    thead = ['Event','Date','Time', 'Pace']
    print(intro)

    tbody = []
    for row in cur:
        tbody.append(row)
        print(row)
        
    summary = 'Total of %d Races' % len(tbody) 
    return([intro, thead, tbody, summary])
    
    
def compare_races(cur, eventname1, date1, eventname2, date2, racetime1, racetime2, max_percent):
    print('\n\nPeople who ran both races: [', eventname1, date1, '] and [', eventname2, date2, ']\n with times between', racetime1, 'and', racetime2, 'where difference in time is less than', max_percent * 100, '%')
    intro = ('People who ran both races:', \
             '[%s on %s] and [%s on %s]' % (eventname1, date1, eventname2, date2), \
             'with times between %s and %s' % (racetime1, racetime2), \
             'where difference in time is less than %d%s' % (max_percent * 100, '%'))
    print(intro)

    cur.execute('DROP TABLE IF EXISTS race1 ')
    cur.execute('DROP TABLE IF EXISTS race2 ')
    cur.execute('DROP TABLE IF EXISTS race_compare  ')
    
    cur.execute('CREATE TABLE race1 AS SELECT athleteID, str_time, sec_time, pace FROM RaceTimes \
        JOIN Races ON Races.id = RaceTimes.raceID \
        JOIN Events ON Races.eventID = Events.id AND Events.eventname = ? AND Races.date = ?', \
        (eventname1, date1, ))
        
    cur.execute('SELECT * FROM race1')
    rows = cur.fetchall()
    print('\nrace1\n')
    for row in rows:
        print('%s\t%s\t%s\t%s' % row)        
        
    cur.execute('CREATE TABLE race2 AS SELECT athleteID, str_time, sec_time, pace FROM RaceTimes \
        JOIN Races ON Races.id = RaceTimes.raceID \
        JOIN Events ON Races.eventID = Events.id AND Events.eventname = ? AND Races.date = ?', \
        (eventname2, date2, ))

    cur.execute('SELECT * FROM race2')        
    print('\nrace2\n')
    for row in rows:
        print('%s\t%s\t%s\t%s' % row) 
        
#     cur.execute('CREATE TABLE race2 AS SELECT athleteID, str_time, sec_time, pace FROM RaceTimes \
#         JOIN Races WHERE Races.eventID = Events.id AND Events.eventname = ? AND Races.date = ? AND Races.id = RaceTimes.raceID', \
#         (eventname2,date2))
#     cur.execute('CREATE TABLE race2 AS SELECT athleteID, racename, str_time, sec_time, pace FROM RaceTimes JOIN Races WHERE Races.racename = ? AND Races.id = RaceTimes.raceID', (racename2,))
    cur.execute('CREATE TABLE race_compare AS \
                    SELECT race2.athleteID, Athletes.name, \
                    race1.str_time AS race1_time_str, race1.sec_time AS race1_time_sec, \
                    race2.str_time AS race2_time_str, race2.sec_time AS race2_time_sec, \
                    race2.sec_time - race1.sec_time AS diff, \
                    (race2.sec_time-race1.sec_time)*2/CAST((race2.sec_time+race1.sec_time)AS REAL) AS percent_diff \
                    FROM race2 \
                    JOIN race1 ON race2.athleteID = race1.athleteID \
                    JOIN Athletes ON race2.AthleteID = Athletes.id \
                    WHERE race1.str_time BETWEEN ? AND ? \
                    AND race2.str_time BETWEEN ? AND ?', (racetime1, racetime2, racetime1, racetime2))
                        
    cur.execute('SELECT * FROM race_compare WHERE abs(percent_diff) < ?', (max_percent,))
    rows = cur.fetchall()
    diffs = []
#     print('%s\t%20s\t%s\t%s\t%s\t%s\t%s\t%s' % ('ID','Name','Time 1','Secs','Time 2','Secs','Diff','%'))

    tbody = []
    for row in rows:
#         print('%d\t%20s\t%s\t%d\t%s\t%d\t%5d\t%.4f' % row)
        percent = '%.2f' % (row[7]*100,)
        name_tag = Markup('<strong><a href=http://localhost:8080/user/%s>%s</a></strong>' % (row[1].replace(' ','%20'), row[1]))
        tbody.append([row[0], name_tag, row[2], row[3], row[4], row[5], row[6], percent])
        diffs.append(row[6])
    mean = np.mean(diffs)
    std = np.std(diffs)
        
    print('\nmean = %.2f, standard deviation = %.2f [seconds]\n\n' % (mean, std)) 
    summary = 'mean = %.2f, standard deviation = %.2f [seconds]' % (mean, std)
    
    
    thead = ['ID','Name','Time 1','Secs','Time 2','Secs','Diff','%']
    
#     cur.execute('DROP TABLE IF EXISTS race1 ')
#     cur.execute('DROP TABLE IF EXISTS race2 ')
#     cur.execute('DROP TABLE IF EXISTS race_compare  ')
    
    return([intro, thead, tbody, summary])
          
def get_races(cur):
    # Print a table of races and dates
    races = []
    cur.execute('SELECT Events.eventname, Events.dist, Races.date, Races.id FROM Events JOIN Races WHERE Races.eventID = Events.id ORDER BY Events.eventname, Races.date')
    for row in cur:
        races.append(row[0] + ' : ' + row[2] + ' <' + str(row[3]) + '>')
        print(row)
    return(races)

def load_database(db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    print(conn,cur)
    return([conn, cur])
    
def get_log_sum(vals):
    dist = '%.1f' % vals[0]
    intensity = '%.1f' % vals[1]
    td_str = '%s' % timedelta(hours=0,minutes=0,seconds=vals[2])
    recovery_str = '%s' % timedelta(hours=0,minutes=0,seconds=vals[3])
    easy_str = '%s' % timedelta(hours=0,minutes=0,seconds=vals[4])
    threshold_str = '%s' % timedelta(hours=0,minutes=0,seconds=vals[5])
    interval_str = '%s' % timedelta(hours=0,minutes=0,seconds=vals[6])
    repetition_str = '%s' % timedelta(hours=0,minutes=0,seconds=vals[7])
    return([dist, intensity, td_str, recovery_str, easy_str, threshold_str, interval_str, repetition_str])    
    
def get_log_sums_byisodate(cur, isostr):
    # isostr is in the format '2016-1%'
    
    cur.execute('SELECT sum(dist), sum(jd_int), sum(time_secs), sum(recovery_secs), \
                sum(easy_secs), sum(threshold_secs), sum(interval_secs), \
                sum(repetition_secs) FROM Log WHERE isodate LIKE (?)', (isostr,))
    return(get_log_sum(cur.fetchone()))
    
    
def get_log_sums_bygregdate(cur, datestr):
    # datestr is in the format '2016-01%'
    
    cur.execute('SELECT sum(dist), sum(jd_int), sum(time_secs), sum(recovery_secs), sum(easy_secs), sum(threshold_secs), sum(interval_secs), sum(repetition_secs) FROM Log WHERE date LIKE (?)', (datestr,))
    return(get_log_sum(cur.fetchone()))
    
def get_log_sums_for_all_weeks(conn, cur):
    # List workouts by week
    cur.execute('SELECT noday(isodate), nodaymatch(isodate) FROM Log GROUP BY noday(isodate) ORDER by nodaymatch(isodate) DESC')
    curlist = cur.fetchall()
    
    tbody = []
    for row in curlist:  
        noday = row[0]
        nodaymatch = row[1]
        tbody.append(get_log_sums_byisodate(cur, nodaymatch))
        print('sums for :', noday, get_log_sums_byisodate(cur, nodaymatch))
    return

def get_log_sums_for_all_months(conn, cur):
    # list workouts by month
    cur.execute('SELECT noday(date), nodaymatch(date) FROM Log GROUP BY noday(date) ORDER by noday(date) DESC')
    curlist = cur.fetchall()
    
    for row in curlist:  
        noday = row[0]
        nodaymatch = row[1]
        print('sums for :', noday, get_log_sums_bygregdate(cur, nodaymatch))
    return
 

def get_log_sums_over_months(cur, month_ago_nearest, month_ago_furthest):
    # this month_ago is month 0, last month is month 1, etc.
    
    months = month_ago_furthest - month_ago_nearest + 1
    
    # Get list of isodates
    cur.execute('SELECT noday(date) FROM Log GROUP BY noday(date) ORDER by noday(date) DESC')
    curlist = cur.fetchall()
    
    # get the weekdays for the last day of nearest and the first day of furthest week 
    startdate = curlist[month_ago_furthest][0]
    enddate = curlist[month_ago_nearest][0]
    startdatematch = curlist[month_ago_furthest][0] + '-01'
    enddatematch = curlist[month_ago_nearest][0] + '-31'

    cur.execute('SELECT sum(dist), sum(jd_int), sum(time_secs), sum(recovery_secs), sum(easy_secs), \
                sum(threshold_secs), sum(interval_secs), sum(repetition_secs) \
                FROM Log WHERE date BETWEEN ? and ?', (startdatematch, enddatematch))
    vals = cur.fetchone()
    
    total_secs = vals[2]
    recovery_secs = vals[3]
    easy_secs = vals[4]
    p8020 = '%.1f' % (100.0 * (recovery_secs + easy_secs) / total_secs)

    dist = '%.1f' % (vals[0]/months)
    intensity = '%.1f' % (vals[1]/months)
    td_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[2]/months))
    recovery_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[3]/months))
    easy_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[4]/months))
    threshold_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[5]/months))
    interval_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[6]/months))
    repetition_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[7]/months))
    
    zones = zones_str(recovery_str, easy_str, threshold_str, interval_str, repetition_str)
    
    return([dist, td_str, zones, intensity, p8020])

def get_log_sums_over_weeks(cur, week_ago_nearest, week_ago_furthest):
    # this week_ago is week 0, last week is week 1, etc.
    
    weeks = week_ago_furthest - week_ago_nearest + 1
    
    # Get list of isodates
    cur.execute('SELECT noday(isodate) FROM Log GROUP BY noday(isodate) ORDER by noday(isodate) DESC')
    curlist = cur.fetchall()
    print(curlist)
    
    # get the weekdays for the last day of nearest and the first day of furthest week 
    startdate = curlist[week_ago_furthest][0]
    enddate = curlist[week_ago_nearest][0]
    startdatematch = curlist[week_ago_furthest][0] + '-1'
    enddatematch = curlist[week_ago_nearest][0] + '-7'
    print(startdatematch, enddatematch)

    cur.execute('SELECT sum(dist), sum(jd_int), sum(time_secs), sum(recovery_secs), sum(easy_secs), \
                sum(threshold_secs), sum(interval_secs), sum(repetition_secs) \
                FROM Log WHERE isodate BETWEEN ? and ?', (startdatematch, enddatematch))
    vals = cur.fetchone()
    print(vals) 
    
    total_secs = vals[2]
    recovery_secs = vals[3]
    easy_secs = vals[4]
    p8020 = '%.1f' % (100.0 * (recovery_secs + easy_secs) / total_secs)

    dist = '%.1f' % (vals[0]/weeks)
    intensity = '%.1f' % (vals[1]/weeks)
    td_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[2]/weeks))
    recovery_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[3]/weeks))
    easy_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[4]/weeks))
    threshold_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[5]/weeks))
    interval_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[6]/weeks))
    repetition_str = '%s' % timedelta(hours=0,minutes=0,seconds=int(vals[7]/weeks))
    
    zones = zones_str(recovery_str, easy_str, threshold_str, interval_str, repetition_str)
    print(zones)
    
    return([dist, td_str, zones, intensity, p8020])
    
def get_log_52weeks(conn, cur):

    conn.create_function("NODAY", 1, noday)
    
    intro = ['Weekly Stats']
    thead = ['Description','Dist.','Time','Time in Zones','Int.','%80/20']
    summary = '' 
    
    tbody = []
    for week in range (1,53):
        tbody.append(['%d weeks ago' % week] + get_log_sums_over_weeks(cur, week, week))
    
    return([intro, thead, tbody, summary])  
      
def get_log_week_stats(conn, cur):

    conn.create_function("NODAY", 1, noday)
    
    intro = ['Weekly Stats']
    thead = ['Description','Dist.','Time','Time in Zones','Int.','%80/20']
    summary = '' 
    
    tbody = []
    tbody.append(['This Week'] + get_log_sums_over_weeks(cur, 0, 0))
    tbody.append(['Last Week'] + get_log_sums_over_weeks(cur, 1, 1))
    tbody.append(['Two Weeks Ago'] + get_log_sums_over_weeks(cur, 2, 2))
    tbody.append(['Three Weeks Ago'] + get_log_sums_over_weeks(cur, 3, 3))
    tbody.append(['Four Weeks Ago'] + get_log_sums_over_weeks(cur, 4, 4))
    tbody.append(['Ave: Last 2 weeks'] + get_log_sums_over_weeks(cur, 1, 2))    
    tbody.append(['Ave: Last 4 weeks'] + get_log_sums_over_weeks(cur, 1, 4))      
    tbody.append(['Ave: Last 8 weeks'] + get_log_sums_over_weeks(cur, 1, 8))     
    tbody.append(['Ave: Last 16 weeks'] + get_log_sums_over_weeks(cur, 1, 16)) 
    tbody.append(['Ave: Last 32 weeks'] + get_log_sums_over_weeks(cur, 1, 32))  
    tbody.append(['Ave: Last 52 weeks'] + get_log_sums_over_weeks(cur, 1, 52)) 
    
    return([intro, thead, tbody, summary])    
    
def get_log_12months(conn, cur):

    conn.create_function("NODAY", 1, noday)
    
    intro = ['Monthly Stats']
    thead = ['Description','Dist.','Time','Time in Zones','Int.','%80/20']
    summary = '' 
    
    tbody = []
    for month in range (1,13):
        tbody.append(['%d months ago' % month] + get_log_sums_over_months(cur, month, month))
    
    return([intro, thead, tbody, summary])  
    

def get_log_month_stats(conn, cur):
    # returns this month, last month, then averages of 1,2,4,8,12 months with latest month being last month
    
    conn.create_function("NODAY", 1, noday)
    
    intro = ['Monthly Stats']
    thead = ['Description','Dist.','Time','Time in Zones','Int.','%80/20']
    summary = '' 
    
    tbody = []
    tbody.append(['This Month'] + get_log_sums_over_months(cur, 0, 0))
    tbody.append(['Last Month'] + get_log_sums_over_months(cur, 1, 1))
    tbody.append(['Two Months Ago'] + get_log_sums_over_months(cur, 2, 2))
    tbody.append(['Three Months Ago'] + get_log_sums_over_months(cur, 3, 3))
    tbody.append(['Four Months Ago'] + get_log_sums_over_months(cur, 4, 4))
    tbody.append(['Ave: Last 2 months'] + get_log_sums_over_months(cur, 1, 2))  
    tbody.append(['Ave: Last 3 months'] + get_log_sums_over_months(cur, 1, 3))        
    tbody.append(['Ave: Last 4 months'] + get_log_sums_over_months(cur, 1, 4))  
    tbody.append(['Ave: Last 5 months'] + get_log_sums_over_months(cur, 1, 5)) 
    tbody.append(['Ave: Last 6 months'] + get_log_sums_over_months(cur, 1, 6))             
    tbody.append(['Ave: Last 8 months'] + get_log_sums_over_months(cur, 1, 8))     
    tbody.append(['Ave: Last 12 months'] + get_log_sums_over_months(cur, 1, 12)) 
    
    return([intro, thead, tbody, summary])  
    
def get_athletes(conn, cur, **kwargs):
    letter = kwargs.get('Letter')
    if letter is not None:
        cur.execute('SELECT id, name, age_group, club, hometown FROM Athletes WHERE name LIKE ? ORDER by name LIMIT 10 OFFSET 0',("%s%%" % letter,))
    else:
        cur.execute('SELECT id, name, age_group, club, hometown FROM Athletes ORDER by name')
    tbody = []
    for recs in cur:
        id = recs[0]
        name = recs[1]
        age_group = recs[2]
        club = recs[3]
        hometown = recs[4]
        id_tag = Markup('<strong><a href=http://localhost:8080/user/%s>%d</a></strong>' % (name.replace(' ','%20'),id))
        tbody.append([id_tag, name, age_group, club, hometown])
       
    intro = ''
    thead = ['id', 'name', 'age_group', 'club', 'hometown']
    summary = 'Total of %d Entries' % len(tbody) 
    return([intro, thead, tbody, summary])   
        

def noday(datestr):
    [year, mw, day] = parse_datestr(datestr)
    return(year + '-' + mw)

def nodaymatch(datestr):
    [year, mw, day] = parse_datestr(datestr)
    return(year + '-' + mw + '-%')              

def norm_race_elev(timestr, elev, dist):
    # timestr in "0:00:00" format
    # elev in m
    # dist in km
    timesec = secs(timestr)
    avegrade = elev/(dist*1000)
    percent_increase = 1.5 * avegrade
    adjusted_time = (1 - percent_increase) * timesec
    return(str_time(adjusted_time))

def norm_race_dist(timestr, orig_dist, norm_dist):
    timesec = secs(timestr)
    timesec = timesec * (norm_dist/orig_dist) ** 1.06
    return(str_time(timesec))
    
def main_sql():
    ######## MAIN FUNCTION ############

    [conn, cur] = load_database('/Users/sroberts/Dropbox/TMT/Python/Running/db/races.sqlite')
    
#     get_weight_report(cur)

    load_result(conn, cur, '/Users/sroberts/Dropbox/TMT/Python/Running/csv/Cobble10k_2017.csv', 'Cobble Hill 10k', '2017-01-22', 10.0, 62, 123, 75)
    load_result(conn, cur, '/Users/sroberts/Dropbox/TMT/Python/Running/csv/Pioneer8k_2017.csv', 'Pioneer 8k','2017-01-8', 8.0, 67, 70, 22)
       
#     load_result(conn, cur, '/Users/sroberts/Dropbox/TMT/Python/Running/csv/CowichanHalf_2016.csv', 'Cowichan Half Marathon', '2016-10-23', 21.0975, 0, 0, 85)
       
        
#     load_result(conn, cur, '/Users/sroberts/Dropbox/TMT/Python/Running/csv/CowichanHalf_2016.csv', 'Cowichan Half Marathon', '2016-10-23', 21.0975, 0, 0, 85)
#     add_event(conn, cur, 'Victoria 8k', 8.0, 0, 0, 0)
#     load_result(conn, cur, '/Users/sroberts/Dropbox/TMT/Python/Running/csv/Victoria_8k_2016.csv', 'Victoria 8k', '2016-10-09', 8.0, 0, 0, 0)
#     load_result(conn, cur, '/Users/sroberts/Dropbox/TMT/Python/Running/csv/VictoriaHalf_2016.csv', 'Victoria Half Marathon', '2016-10-09', 21.0975, 14, 36, 128)

#     conn.create_function("NODAY", 1, noday)
#     conn.create_function("NODAYMATCH", 1, nodaymatch)
#         
#     print(norm_race_dist("0:41:15",10,21.0975))
#     print(norm_race_elev("0:51:03",97,12))
#         
    conn.commit()
    cur.close()

if __name__ == "__main__":
	main_sql()

