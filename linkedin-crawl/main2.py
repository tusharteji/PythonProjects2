from crawljobs import CrawlJobs
from gtts import gTTS
from word2number import w2n
import configparser
import os
import playsound
import random
import speech_recognition as sr

recog = sr.Recognizer()     # Initiating speech recognizer


def parse_config():
    """Parses conf.ini configuration file for usernames and passwords"""
    config = configparser.ConfigParser()
    config.read("conf.ini")
    return config["linkedInAccount"], config["chromedriver"]


def get_voice_input(ask=False):
    """Captures voice inputs"""
    with sr.Microphone(device_index=1) as source:   # Using microphone connected at device source 1 as source
        recog.adjust_for_ambient_noise(source)      # Handling noise while listening through the source
        if ask:
            speak_back(ask)     # Speaks back all the user prompts and replies
        audio = recog.listen(source, 10, 3)     # Times out in 10 seconds and stops listening after 3 seconds
        voice_data = ''
        try:
            voice_data = recog.recognize_google(audio)
        except sr.UnknownValueError:
            speak_back("Sorry, I did not get that!")
        except sr.RequestError:
            speak_back("Sorry, my speech service is down!")
        return voice_data


def speak_back(audio_string):
    """Converts text to speech using Google's Text to Speech service (gTTS)"""
    tts = gTTS(text=audio_string, lang='en')
    num = random.randint(1, 100000000)
    audio_file = 'audio-' + str(num) + '.mp3'   # Temporarily saves the audio file with the string audio
    tts.save(audio_file)
    playsound.playsound(audio_file)     # Plays the audio file
    print(audio_string)
    os.remove(audio_file)       # Deletes the audio file afterwards


def respond(data):
    """The main function that defines all the replies and the tasks the voice assistant is capable to doing"""
    if "hello friend" in data:      # Responds to 'hello friend'
        task = get_voice_input("Hi Tushar, what can I do?")
        if "default" in task and "task" in task:
            speak_back("I am on it!")
            script()    # Calls the script function with default parameters and runs the crawljobs module process
            return
        if "search" in task and "jobs" in task:
            kws = get_voice_input("Any keywords?")
            if "default" in kws:
                keywords = "Python Developer"
            else:
                keywords = kws
            # Location
            loc = get_voice_input("Great, what about location?")
            if "default" in loc:
                location = "United States"
            else:
                location = loc
            # Experience Level filter
            exp = get_voice_input("Any experience level filter?")
            exp_filter = []
            if "entry" in exp:
                exp_filter.append('Entry level')
            if "associate" in exp:
                exp_filter.append('Associate')
            if "senior" in exp:
                exp_filter.append('Mid-Senior level')
            if "internship" in exp:
                exp_filter.append('Internship')
            if "default" in exp:
                exp_filter = ['Entry level', 'Associate']
            # Job Type filter
            jobtype = get_voice_input("Awesome, and what about job types?")
            jobtype_filter = []
            if "full" in jobtype:
                jobtype_filter.append("Full-time")
            if "part" in jobtype:
                jobtype_filter.append("Part-time")
            if "contract" in jobtype:
                jobtype_filter.append("Contract")
            if "internship" in jobtype:
                jobtype_filter.append("Internship")
            if "default" in jobtype:
                jobtype_filter = ['Full-time']
            # Number of pages to search or crawl
            pgs = get_voice_input("One last question! How many pages do you want me to crawl?")
            if "default" in pgs:
                pages = 10
            else:
                pages = w2n.word_to_num(pgs)
            # Calls the script function with collected parameters and runs the crawljobs module process
            speak_back("I am on it!")
            script(keywords=keywords, location=location, exp_filter=exp_filter, jobtype_filter=jobtype_filter,
                   pages=pages)
            return
        else:
            speak_back("Sorry, I cannot help you with that!")


def script(keywords="Python Developer", location="United States",
           exp_filter=['Entry level', 'Associate'], jobtype_filter=['Full-time'], pages=10):
    """Calls the crawljobs module and runs the jobs-scraping script after capturing all the arguments
    required for the script"""
    # Parsing config.ini file
    linkedin, chrome = parse_config()
    homepage, username, password = linkedin["homepage"], linkedin["username"], linkedin["password"]
    chromedriver = chrome["location"]

    # Crawling LinkedIn jobs listings
    cj = CrawlJobs(chromedriver)  # Initializing chromedriver
    cj.login(homepage, username, password)  # Login to LinkedIn
    cj.open_jobs()  # Open jobs section/page
    cj.search_jobs(keywords, location)  # Search jobs based on keywords and location provided
    cj.add_filter("Experience Level", exp_filter)  # Add filter for Experience Level
    cj.add_filter("Job Type", jobtype_filter)  # Add filter for Job Types
    scraped_data = cj.scrape_jobs(pages)    # Scrape jobs from first {pages} pages

    # Setting up file name and location
    folder_path, file_path = cj.file_setup()

    # Creating dataframe from the scraped data after handling duplicates from the previously saved xlsx's
    dframe = cj.create_dataframe(scraped_data, folder_path)

    # Save the final draft to an excel document and close the driver
    cj.save_to_excel(dframe, file_path)
    cj.close_driver()


if __name__ == "__main__":
    while True:
        voice_input = get_voice_input()
        respond(voice_input)
