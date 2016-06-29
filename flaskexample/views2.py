from flask import render_template
from flaskexample import app
from flask import request
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
import numpy as np
import trackerFuncs as TF
import os
import datetime

#from flask import Flask
#app = Flask(__name__, static_url_path = "static", static_folder = "static")
UPLOAD_FOLDER_RAW = '/Users/loisks/Documents/tmp/raw/'
UPLOAD_FOLDER_EDIT = '/Users/loisks/Documents/tmp/edit/'
ALLOWED_EXTENSIONS = set(['csv','CSV'])

app.config['UPLOAD_RAW_DEST'] = UPLOAD_FOLDER_RAW
app.config['UPLOAD_EDIT_DEST'] = UPLOAD_FOLDER_EDIT
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_RAW

# check file is ok
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
#
# try looking at app.show 
@app.route('/')
#@app.route('/index')
def index():
    return render_template("cesareans.html",
       title = 'Home', user = { 'nickname': 'Miguel' },
       )
#
# the forum
#@app.route('/')
#def my_form():
#    return render_template("my-form.html")




#@app.route('/db')
#def db():
#   user = 'loisks'
#   user2=userNameForum()
#   user2='Jimmy'
#   trackerType=trackerForum()
#   #user2 = 'JIMMY' #add your username here (same as previous postgreSQL)
#   
#   activeList=['ActiveTime',  'Distance', 'Calories']
#   weatherList=['MeanTemperature', 'MaxTemperature', 
#           'MinTemperature','Precip', 'Wind']
#   activeLabels=['Active Time [s]','Distance [m]',  'Calories']
#   weatherLabels=['Average Temperature [F]', \
#           'Max Temperature [F]', 'Min Temperature [F]',\
#                  'Precipitation [inches]', \
#                  'Wind [mph]']
#   Parameters=activeList+weatherList
#   Labels=activeLabels+weatherLabels
#   
#   host = 'localhost'
#   if trackerType=='Endomondo':
#      dbname = 'tapiriik'
#      TF.endomondo(user2)
#      
#   db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
#   con2 = None
#   con2 = psycopg2.connect(database=dbname, user=user)  
#   cur=con2.cursor()
#   cur.execute("SELECT * FROM "+user2)
#   #
#   # get all the data 
#   AllUserData=cur.fetchall()
#   #
#   # get the dates 
#   dates=pd.DatetimeIndex(np.swapaxes(AllUserData, 1,0)[0])
#   dataOnly=np.swapaxes(np.swapaxes(AllUserData,1,0)[1:],1,0)
#   df=pd.DataFrame(dataOnly, columns=Parameters)
#   caloriesBurned=''
#   for iCal in range(len(df['Calories'])):
#      caloriesBurned+=str(df['Calories'][iCal])
#      caloriesBurned+="<br>"
#   return(caloriesBurned)

#@app.route('/output')
#def output():
#    #
#    # just try to print the csv file to screen
#    
#    csvFile = getData()
#    csvConvert=np.genfromtxt(csvFile, delimiter=',')
#    print('Yes!!!')
#    
#    return (render_template("output.html",
#                            title = 'Home', user = { 'nickname': 'Miguel' }),
#            csvConvert
#    )

@app.route('/output',methods=['POST'])
def output():
 #
 # man, this sucks
 #
    
 
 tracker=request.form.get('Tracker')
 username=request.form.get('Username')
 password=request.form.get('Password')
 location=request.form.get('Location')
 dateStart=request.form.get('StartDate')
 print("Date start is: " + str(dateStart))
 dateEnd=request.form.get('EndDate')
 dataModified=0 # for Jawbone file check           
 try:
    #
    # THIS GETS THE FILE. FLASK.
    #
   file = request.files['file']
   
   if file and allowed_file(file.filename):
       filename=file.filename
       file.save(os.path.join(app.config['UPLOAD_RAW_DEST'],filename))
       print filename
       #        return redirect(url_for('report_match',filename=filename))
   #get location of saved file
   print( 'filename: ' + filename)
   filepath = os.path.join(app.config['UPLOAD_RAW_DEST'],filename)
   print filepath
   print app.config['UPLOAD_RAW_DEST']

   if tracker=='Jawbone':
       import glob
       # then this is a csv file
       os.chdir('/Users/loisks/Documents/tmp/raw')
       # get the file
       print("FILE NAME IS: " +str(filename))
       ff=glob.glob(filename)[0]
       dataAll=np.swapaxes(np.genfromtxt(ff, delimiter=','), 1, 0)
      
       temp=[ datetime.datetime.strptime(str(int(dataAll[0][j])), \
              '%Y%m%d') for j in range(1,len(dataAll[0]))]
       dataYears=list( dataAll[0])
       time=[np.nan]+ temp
       # now get the data that matters 
       # 
       # 41 is steps
       # 37 is distance in meters
       # 43 is calories
       # 35 is active time in seconds
       # 48 is sleep time
       #
       params=['Dates', 'Steps', 'Distance', 'Calories', 'ActiveTime', 'SleepTime']
       indicies=[0,41, 37, 43, 35, 48]
       dataModified={}
       # now have to adjust for the right dates
       for iP in range(len(params)):
           dataModified[params[iP]]=[]
       goodvals= np.isnan(dataYears[41]) # get rid of the nans
      
       dataModified['Steps']+=list(dataAll[41])
       dataModified['Distance']+=list(dataAll[37])
       dataModified['Calories']+=list(dataAll[43])
       dataModified['ActiveTime']+=list(dataAll[35])
       dataModified['SleepTime']+=list(dataAll[48])
       dataModified['Dates']+=list(np.array(time))
       #

   elif tracker=='PolarLoop':
      # this means get the Polar Loop Data
      os.chdir('/Users/loisks/Documents/InsightProject/PolarLoop/')
      import assimilateData as ASSD
      ASSD.getData(username,password,dateStart,dateEnd)
      # this *should* set up the data base and table with
      # the username and password the user inputs
    
 except:
     print("no file uploaded")

#
# now load the relevant figures
#
 if tracker=='Jawbone':
         import readJawBone as PL 
         data=PL.loadData(username, password, location, dateStart,\
                           data=dataModified)
         
 elif tracker=='Polar Loop':         
         import dataStats as PL
         data=PL.loadData(username, password, location, instartDate=dateStart, \
                          inendDate=dateEnd)
#
# Jimmy's data 
 elif tracker=='Endomondo':         
         import readTapiriik as PL
         data=PL.loadData(username, password, location)

 dd=data[0]
 temp=data[0]*1.1
 goal=("%.0f" % temp )
 cals=("%.0f" % dd)
 dayofweek=data[2]
 weather=data[1]

 boxwhisker="/static/"+username+"/boxwhisker_Calories_daysofweek.png"
 scatter1="/static/"+username+"/seaborn_Calories_Wind_scatter.png.png"
 scatter2="/static/"+username+"/seaborn_Calories_MeanTemperature_scatter.png.png"
 scatter3="/static/"+username+"/seaborn_Calories_Precip_scatter.png.png"
 os.chdir('/Users/loisks/Documents/InsightProject/Hosting/flaskexample')
 print(scatter1)
 
 return render_template("output.html", calories=cals, tracker=tracker, \
                        goal=goal, dayofweek=str(dayofweek),\
                        weather=str(weather), boxwhisker=boxwhisker, \
                        scatter1=scatter1, scatter2=scatter2, \
                        scatter3=scatter3)
