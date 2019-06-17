import RPi.GPIO as GPIO
import time
import requests
from pyrebase import pyrebase

#Firebase Configuration
config = {
  "apiKey": "AIzaSyDM0tsZW9478u-IVn3tGCdE9Gr3li9QHu4",
  "authDomain": "raspberry-pi-53500.firebaseapp.com",
  "databaseURL": "https://raspberry-pi-53500.firebaseio.com",
  "projectId": "raspberry-pi-53500",
  "storageBucket": "raspberry-pi-53500.appspot.com",
  "messagingSenderId": "310222627960",
  "appId": "1:310222627960:web:6ac907bba29c610f"
}

firebase = pyrebase.initialize_app(config)

#GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)

#Firebase Database Intialization
db = firebase.database()

#While loop to run until user kills program
while(True):
    #Get value of LED 
    led = db.child("led").get()
    #print("Success")

    #Sort through children of LED(we only have one)
    for user in led.each():
        #Check value of child(which is 'state')
        if(user.val() == "off"):
            #If value is off, turn LED off
            print("off")
            GPIO.output(18, False)
        else:
            #If value is not off(implies it's on), turn LED on
            print("on")
            GPIO.output(18, True)

        #0.1 Second Delay
        time.sleep(0.1)   
