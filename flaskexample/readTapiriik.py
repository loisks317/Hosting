# readTapiriik.py
#
# read in the Garmin .tcx data from Tapiriik and run some statistics with
# the weather
#
# LKS, June 2016, part of the Insight Data Science Program
#
# import
import numpy as np
import tcxparser
import os
import glob
from geopy.geocoders import Nominatim
import webScrapeFunctions as WS
import plottingFunctions as pf
import datetime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
import matplotlib.pyplot as plt
import psycopg2
import sys
#
#

def loadData(username, password, loc2):

   tableName=username
   if username=='Jimmy':
      # this is an oopsie hack
      tableName='JIMMY22'

   con = None
   con = psycopg2.connect(dbname='postgres', user='loisks', host='localhost', password='poppy33')

   # make it create individual data base
   ActiveLabels=['Date', 'ActiveTime', 'Location', 'Distance', 'Calories']
   con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
   con2 = psycopg2.connect("dbname='tapiriik' user='loisks'")  
   cur=con2.cursor()

   # get all the files
   fileList=glob.glob('*.tcx')
   try:
     query='SELECT * FROM '+tableName
     cur.execute(query) # access data currently in data base 
     prevData=cur.fetchall()
     startDate=datetime.datetime.strftime(prevData[-1][0]+datetime.timedelta(days=1), '%Y-%m-%d')

   except(None):
      con2 = psycopg2.connect("dbname='tapiriik' user='loisks'")  
      cur=con2.cursor()
      query2=" CREATE TABLE "+ tableName +" (Date TIMESTAMP, ActiveTime REAL, \
        Distance REAL, Calories REAL, \
        meanTemperature REAL, maxTemperature REAL, minTemperature REAL,precipitation REAL, wind REAL); "
      cur.execute(query2)
      startDate=fileList[0][0:10] # grabs the date string
  
# collect the data
# find the start date in list

      mStartDate=datetime.datetime.strptime(startDate, '%Y-%m-%d')
      try:
        indexList=[i for i, s in enumerate(fileList) if startDate in s][0]
      except:
        startDate=datetime.datetime.strftime(mStartDate-datetime.timedelta(days=1), '%Y-%m-%d')
        # to get the nearest index on restart
        indexList=[i for i, s in enumerate(fileList) if startDate in s][0]+1

      # another crappy hack 
      for iFile in range(indexList,len(fileList)-6):
       try:
        #
        curDate=datetime.datetime.strptime(fileList[iFile][0:10], '%Y-%m-%d')
        #
        # extract data
        #
        tcx = tcxparser.TCXParser(fileList[iFile])
        #
        # get data
        workoutTime=tcx.duration
        latitude=str(tcx.latitude)
        longitude=str(tcx.longitude)
        timeStamp=tcx.completed_at
        try:
                distance=tcx.distance
        except:
                distance=1e-31
        calories=tcx.calories
        #
        # turn lat and longitude into a city
        geolocator = Nominatim()
        location = (geolocator.reverse(latitude+','+longitude)).address
        #
        # now get the weather data 
        #
        dateLink=datetime.datetime.strftime(curDate,'%d'+'.'+'%m'+'.'+'%Y')    
        weatherData=WS.getWeatherData(curDate, location)  # returns a list
        print('Acquired Weather Data')
        
        #
        #
        query = 'INSERT INTO JIMMY22 (DATE, ACTIVETIME, DISTANCE, CALORIES, \
        MEANTEMPERATURE, MAXTEMPERATURE, MINTEMPERATURE,\
        PRECIPITATION, WIND) VALUES (%s, %s, %s, %s,\
        %s, %s, %s, %s, %s);'
        data=( curDate, workoutTime,distance, calories, \
               weatherData[0], \
               weatherData[1], weatherData[2], weatherData[3], weatherData[4])
        print data
        cur.execute(query,data)
        con2.commit()
       except:
         print iFile
# 
#
   activeList=['ActiveTime',  'Distance', 'Calories']
   weatherList=['MeanTemperature', 'MaxTemperature', 
        'MinTemperature','Precip', 'Wind']
   activeLabels=['Active Time [s]','Distance [m]',  'Calories']
   weatherLabels=['Average Temperature [F]', \
        'Max Temperature [F]', 'Min Temperature [F]',\
                  'Precipitation [inches]', \
        'Wind [mph]']
   # loc2 is for preditions
   data=pf.plotter(activeList, weatherList, activeLabels, weatherLabels, \
                      'tapiriik', tableName, loc2,color='#FFA500', nn=15 \
                      )
   cals=data.CalPredict
   bestCorr=data.bestCorr
   bestDay=data.bestDay
   return(cals,bestCorr,bestDay)
   
