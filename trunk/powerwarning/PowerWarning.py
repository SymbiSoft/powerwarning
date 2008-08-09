# Power Monitor by Luca Cassioli 2008
# This program is freeware
#
# Program allows remote monitoring of power presence in home environment; it must
# be installed on a phone which is left at home while being away; the phone must
# be connected to battery charger. As soon as power is interrupted (for any reason),
# program detects power loss and sends SMS to user defined number(s). As soon as
# power is back, a proper message is sent to the number(s).
# Program is SMS activated:
# CHECK ON : Begin checking power at user defined intervals.
# CHECK OFF : turn off the checking.
# STATUS : requests a single power-status query. 
#
#
# **** Antitheft use ****
# If you add stiches to your doors/windows in such a way opening one of them interrupts
# the circuit which connects battery charger to phone, you'll be warned as soon as
# a door/window is opened. This use requires an additional phone connected directly to
# power grid: if you receive SMS from BOTH phones, it means power is missing; if you
# receive SMS only from the window-connected phone, it means the window has been opened.

import e32, messaging
import sysagent, esysagent
from graphics import *
from e32 import ao_sleep,Ao_lock
import keycapture
from appuifw import *
import inbox
import socket
import appuifw
import messaging
import os
import e32db
import time


def cb(state):
  print "Message status: ", state
  
def TimeString():
   t = repr(e32db.format_time(time.time()))
   timestamp = t[8:12] + t[5:7] + t[2:4] + "_" + t[13:15] + t[16:18] + t[19:21]
   return timestamp

def LogEvent(s):
  f2=open("E:\\nokia\\others\\powerlog.txt","a")
  f2.write(s+"\n")
  print s
  f2.close()
  
  
  
FILEPATH = "c:\\nokia\\others\\settings.ini"
STANDARD_POLLING_INTERVAL = 10
NOPOWER_POLLING_INTERVAL = 10
MAX_ATTEMPTS = 10

SettingsRead = False

LogEvent(TimeString() + " - " + "Program started.")

def CheckStatus():
  global STANDARD_POLLING_INTERVAL, NOPOWER_POLLING_INTERVAL , PHONE_NUMBER1, PHONE_NUMBER2, PHONE_NUMBER3,  SettingsRead
  if SettingsRead == False:
    LogEvent(TimeString() + " - " + "Errore configurazione. Programma terminato.")
    PowerStatus = "== Program error ==   Bad configuration file"
  else:
    PowerStatus = "ON"
    if sysagent.charger_status() != esysagent.ESAChargerConnected:
      print "power missing"
      PowerStatus = "OFF"
  print "Checking status: ",PowerStatus, " polling: ", STANDARD_POLLING_INTERVAL , ", ", NOPOWER_POLLING_INTERVAL
  return PowerStatus
            
def ReadSettings():
# Settings file must contain 1 line with this syntax:
#{'constant_name':'constant_value'},{'constant_name':'constant_value'},{'constant_name':'constant_value'},...
    global Recipient_number
    global FILEPATH
    global NOPOWER_POLLING_INTERVAL, STANDARD_POLLING_INTERVAL, PHONE_NUMBER1, PHONE_NUMBER2, PHONE_NUMBER3, SettingsRead
    try:
      LogEvent(TimeString() + " - " + "Opening file...")
      f=open(FILEPATH,'rt')  # Open for reading
      LogEvent(TimeString() + " - " + "Reading contents...")
      content = f.read()
      LogEvent(TimeString() + " - " + "Processing contents...")
      try:
        parameters=eval(content.rstrip()) # Store values
        f.close() 
        NOPOWER_POLLING_INTERVAL = int(parameters.get('NOPOWER_POLLING_INTERVAL',''))  # read value
        STANDARD_POLLING_INTERVAL = int(parameters.get('STANDARD_POLLING_INTERVAL',''))  # read value
        PHONE_NUMBER1 = parameters.get('PHONE_NUMBER1','')  # read value
        PHONE_NUMBER2 = parameters.get('PHONE_NUMBER2','')  # read value
        PHONE_NUMBER3 = parameters.get('PHONE_NUMBER3','')  # read value
        SettingsRead = True
        LogEvent(TimeString() + " - " + "Contents processed.")
      except:
        LogEvent(TimeString() + " - " + "Error parsing configuration file")
        SettingsRead = False
      else:
        LogEvent(TimeString() + " - " + "Settings successfully read.")
    except:
        LogEvent(TimeString() + " - " +  'Couldnt OPEN settings file - err 002') 
        SettingsRead = False   

def SendMess(n,m):
  Sent = 0
  Failed = 0
  while Failed<MAX_ATTEMPTS and Sent == 0:
    try:
      messaging.sms_send(n,m,callback=cb) # DEBUG
      e32.ao_sleep(10)
      for b in range(1,10):
          print "Ciclo attesa...",b
          e32.ao_sleep(2)      
      Sent = 1
    except Exception, e: 
      Failed = Failed+1
      Sent = 0
      ErrorText = str(e)  
      print "Error while sending:" + ErrorText
      LogEvent(TimeString() + " - " + "Error sending message >" +m+ "< to " +n+ ": "+ ErrorText)
      e32.ao_sleep(10)  # Always wait a bit to prevent "overlaps" in sending.
  if Failed == MAX_ATTEMPTS and Sent == 0:
      LogEvent(TimeString() + " - ERROR - Couldn't send message.")
  if Sent == 1:
      LogEvent(TimeString() + " - Message sent: >" + m + "< to " + n )
  
def read_sms(id): 
    global  PHONE_NUMBER1, PHONE_NUMBER2, PHONE_NUMBER3, TRACKING
    ##############################à
    #sms_text="TRACK ON" # DEBUG*********
    ##############################à
    e32.ao_sleep(0.1)
    i=inbox.Inbox() 
    sms_text=i.content(id) 
      #appuifw.note(u"Messaggio da elaborare: " + sms_text, "info")
      #print "Message:", sms_text
      
      
    # Execute different actions depending on SMS contents:
    
    if sms_text[0:8] == 'CHECK ON':
      i.delete(id) # Delete just received message
      print "Activation message received"
      LogEvent(TimeString()+" - "+"ACTIVATED")
      SendMess(PHONE_NUMBER1,'Power monitor ACTIVATED!')
      #SendMess(PHONE_NUMBER2,'Power monitor ACTIVATED!')
      #SendMess(PHONE_NUMBER3,'Power monitor ACTIVATED!')
      TRACKING = 1
      while (TRACKING == 1):
        # Continuously checks for power loss. 
        # Send message as long as power is missing.
        e32.ao_sleep(STANDARD_POLLING_INTERVAL)
        msg=CheckStatus()
        if msg == "OFF":
          print "POWER LOSS DETECTED, SENDING MESSAGE"
          LogEvent(TimeString()+" - "+"Power OFF detected")
          SendMess(PHONE_NUMBER1,'STATUS: '+msg+'\nSend message CHECK OFF to stop polling')            
          LogEvent(TimeString()+" - "+ "STARTING CYCLE: WAITING FOR POWER BACK...")
          while msg == "OFF" and TRACKING == 1: # Continuously check till power comes back:
            e32.ao_sleep(NOPOWER_POLLING_INTERVAL)
            msg=CheckStatus()
            print "WAITING FOR POWER BACK..."
          SendMess(PHONE_NUMBER1,'POWER IS ON AGAIN')   
        #SendMess(PHONE_NUMBER2,'STATUS: '+msg)  
        #SendMess(PHONE_NUMBER3,'STATUS: '+msg)  
        else:
          pass # Power is on, so nothing to do.
        
    if sms_text[0:9] == 'CHECK OFF':
      i.delete(id) # Delete just received message
      print "DE-activation message received"
      LogEvent(TimeString()+" - "+"DEACTIVATED")
      TRACKING = 0
      SendMess(PHONE_NUMBER1, "Power monitor DEactivated!")
      #SendMess(PHONE_NUMBER2, "Power monitor DEactivated!")
      #SendMess(PHONE_NUMBER3, "Power monitor DEactivated!")
      
    if sms_text[0:6] == 'STATUS':
      i.delete(id) # Delete just received message
      print 'Reading status....'      
      msg=CheckStatus()
      print 'Sending status: ' + msg 
      LogEvent(TimeString()+" - "+"Query received")
      SendMess(PHONE_NUMBER1, msg) # Send SMS.
      #SendMess(PHONE_NUMBER2, msg) # Send SMS.
      #SendMess(PHONE_NUMBER3, msg) # Send SMS.

  
def quit():
    app.exit_key_handler = None
    print "TERMINATO."
    print

#LogEvent(TimeString() + " - " + "Reading settigs...")  
ReadSettings()
#LogEvent(TimeString() + " - " + "Data read:")
#LogEvent(TimeString() + " - " + "Phone1: " + PHONE_NUMBER1)
#LogEvent(TimeString() + " - " + "Phone2: " + PHONE_NUMBER2)
#LogEvent(TimeString() + " - " + "Phone3: " + PHONE_NUMBER3)
#LogEvent(TimeString() + " - " + "Standard polling: " + str(STANDARD_POLLING_INTERVAL))
#LogEvent(TimeString() + " - " + "Power off polling: " + str(NOPOWER_POLLING_INTERVAL))

f2=open("E:\\nokia\\others\\powerlog.txt","w")
f2.write("Power status log\n")
f2.close()

print 'connecting to inbox...'
i=inbox.Inbox()  
# Connect messages-receiving to program:   
i.bind(read_sms) 
print 'Connected. Waiting for incoming messages...'
print "Done."

