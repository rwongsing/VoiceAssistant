from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import pyttsx3
import speech_recognition as sr
import pytz
import subprocess
import sys
from bs4 import BeautifulSoup
import requests

# Global variables
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
DAY_EXT = ["rd", "th", "st", "nd"]

# Read text and speak
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Get audio from user
def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        # Listen and print a string or throw an error if no sound
        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
            print("Exception: " + str(e))

    return said.lower()

# Implement Google Calendars API
# Authenticate google account each time and stored data in .pickle file
def authenticate_google():

    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    return service

# FEATURE - Parameters (Number of events, Authenticated Google Account)
def get_events(day, service):
    # Call the Calendar API
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
    utc = pytz.utc
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)

    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(),
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f"You have {len(events)} events on this day.")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split("-")[0])

            if int(start_time.split(":")[0]) < 12:
                start_time = start_time + "am"
            else:
                start_time = str(int(start_time.split(":")[0])-12) + start_time.split(":")[1]
                start_time = start_time + "pm"
            
            speak(event["summary"] + " at " + start_time)

# Find the day being talked about
def get_date(text):
    text = text.lower()
    today = datetime.date.today()

    if text.count("today") > 0:
        return today
    
    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    # Look for keywords in text (Months, Days of the week, Days)
    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXT:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])
                    except:
                        pass

    # Always referring to future dates
    if month < today.month and month != -1:
        year = year + 1
    
    if day < today.day and month == -1 and day != -1:
        month = month + 1
    
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week

        if dif < 0:
            dif += 7
            if text.count("next") >= 1:
                dif += 7
        
        return today + datetime.timedelta(dif)

    if day != -1:
        return datetime.date(month=month, day=day, year=year)

# FEATURE - Make a note in a text document
def note(text):
    date = datetime.datetime.now()
    file_name = str(date).replace(":", "-") + "-note.txt"
    with open(file_name, "w") as f:
        f.write(text)

    #subprocess.Popen(["TextEdit", file_name])

# FEATURE - Scrape Dictionary.com for a definition to word
def definition(word):
    url = ""

# MAIN
WAKE = "hey robert"
SERVICE = authenticate_google()

while True:
    print("Listening")
    text = get_audio()
    q = False

    # Utilize a wake word similar to "alexa" or "hey google"
    if text.count(WAKE) > 0 and q == False:
        speak("I am ready")
        text = get_audio()

        # FEATURE - Get events from google calendar
        CALENDAR_TRGR = ["what do i have", "do i have plans", "am i busy", "what's happening", "what am i doing"]
        for phrase in CALENDAR_TRGR:
            if phrase in text.lower():
                date = get_date(text)
                if date:
                    get_events(date, SERVICE)
                else:
                    speak("I don't understand")

        # FEATURE - Make a note in a textfile that saves to your pc
        NOTE_TRGR = ["make a note", "write this down", "remember this", "jot this down"]
        for phrase in NOTE_TRGR:
            if phrase in text.lower():
                speak("What would you like me to write down?")
                note_text = get_audio()
                note(note_text)
                speak("I've made a note of that.")
        
        # FEATURE - Ask a question to be googled and be redirected to a page

        # FEATURE - Ask for the definition of a word and be told
        DEF_TRGR = ["look up a word", "define the word", "define", "tell me the meaning of", "tell me the definition of"]
        for phrase in DEF_TRGR:
            if phrase in text.lower():
                speak("What word would you like me to define?")
                word = get_audio()
                definition(word)

        # End the program
        QUIT_TRGR = ["quit", "that is all", "goodbye", "see you later"]
        for phrase in QUIT_TRGR:
            if phrase in text.lower():
                speak("Goodbye")
                sys.exit(0)

