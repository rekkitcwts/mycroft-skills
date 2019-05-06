# Copyright 2019 rekkitcwts
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import feedparser
import re
import os
import subprocess
import sqlite3

from adapt.intent import IntentBuilder
from mycroft.audio import wait_while_speaking
from mycroft.skills.core import MycroftSkill, intent_handler, intent_file_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.skills.context import adds_context, removes_context
import traceback
from requests import Session

import urllib, json
import requests
from urllib.request import urlopen


# Reworked! Now added SQLITE support for tracking saved audiobooks.
# Audiobook Skill, based on this feature request on github: https://github.com/MycroftAI/mycroft-skills/issues/47
# Used the Speak skill as a base.

# The class BufordSQLite that handles the sqlite database in an OOP manner
class BufordSQLite:
    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        self.conn = sqlite3.connect('buford.db')

    # Query that returns nothing (e.g. INSERT)
    def emptyQuery(self, query):
        self.conn.execute(query)

    # Query that returns something. Accepted Values - Single (1R x 1C), Columns(1R x nC), Table (nR x nC)
    def returnQuery(self, query, return_type="Single"):
        if return_type == "Single":
            return self.conn.execute(query).fetchone()[0] # Returns a single object
        if return_type == "Columns":
            return self.conn.execute(query).fetchone() # Returns a row
        if return_type == "Table":
            return self.conn.execute(query).fetchall() # Returns a n x n table

    # Required in order to make changes to database
    def commit(self):
        self.conn.commit()

    # Closes Database Connection
    def close(self):
        self.conn.close()


class Author:

    def __init__(self, author_id, first_name, last_name, dob, dod):
        self.id = author_id
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.dod = dod

    def getAuthorFullName(self):
        return self.first_name + " " + self.last_name

class Audiobook:

    def __init__(self, audiobook_id, title, description, num_sections, url_zip_file, author):
        self.audiobook_id = audiobook_id
        self.title = title
        self.description = description
        self.num_sections = num_sections
        self.url_zip_file = url_zip_file
        self.author = author
        

class AudiobookSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(AudiobookSkill, self).__init__(name="AudiobookSkill")
        
        # TODO: Initialize working variables used within the skill.
    
    # Lists saved audiobooks
    @intent_handler(IntentBuilder("ListAudiobookIntent").require("List").require("Saved").require("Audiobooks"))
    def handle_list_audiobook_intent(self, message):
        self.speak_dialog('no.audiobook')

    
    # Searches for the audiobook title, the user has the option to listen to the description or to save it.
    @intent_handler(IntentBuilder('AudiobookSearchIntent').require("Search").require("Audiobook"))
    @adds_context('AudiobookSearchChoicesContext')
    def handle_search_intent(self, message):
        # Get search term from utterance and separate from the intent words
        utterance = message.data.get('utterance')
        repeat = re.sub('^.*?' + message.data['Audiobook'], '', utterance)
        user_utterance = ""
        for x in repeat.split():
            user_utterance += x + " "
        self.speak("Now searching for audiobook " + user_utterance)
        # Tries to search the librivox API
        url = "https://librivox.org/api/feed/audiobooks/?title=" + user_utterance + "&format=json"
        raw_data = requests.get(url=url)
        json_data = raw_data.json()
        try:
            # Save the author and audiobook infos in an object
            author = Author(json_data["books"][0]["authors"][0]["id"], json_data["books"][0]["authors"][0]["first_name"], json_data["books"][0]["authors"][0]["last_name"], json_data["books"][0]["authors"][0]["dob"], json_data["books"][0]["authors"][0]["dod"])
            self.found_audiobook = Audiobook(json_data["books"][0]["id"], json_data["books"][0]["title"], json_data["books"][0]["description"], json_data["books"][0]["num_sections"], json_data["books"][0]["url_zip_file"], author)
            # Choices - read the description or download immediately
            self.speak('I found the audiobook on ' + user_utterance + ", would you like to listen to the description, or do you want to save immediately?", expect_response=True)
            # Keywords: Say the description, Save the audiobook
        except:
            # If an error is given
            self.speak("Please provide exact title.")


    # Reads the audiobook description
    @intent_handler(IntentBuilder('ReadAudiobookDescriptionSearchIntent').require("ReadDescription").require('AudiobookSearchChoicesContext').build())
    @removes_context('AudiobookSearchChoicesContext')
    @adds_context('SaveYesOrNoContext')
    def handle_read_description_intent(self, message):
        self.speak(self.found_audiobook.description)
        self.speak('Would you like to download this audiobook?', expect_response=True)

    # Handles the "no" response to the audiobook download question
    @intent_handler(IntentBuilder('DownloadAfterDescriptionNoIntent').require("SaveNo").require('SaveYesOrNoContext').build())
    @removes_context('SaveYesOrNoContext')
    def handle_download_no_intent(self, message):
        self.speak_dialog('download.choices.no')

    # Plays the audiobook.
    # Idea: Will save the audiobook zip file, then extract it, before
    # it can be played
    # NOTE: Rework this whole thing
    #@intent_handler(IntentBuilder("").require("Read").require("Audiobook"))
    #def handle_read_intent(self, message):
        # Get audiobook title from utterance
        #utterance = message.data.get('utterance')
        #repeat = re.sub('^.*?' + message.data['Audiobook'], '', utterance)
        #user_utterance = ""
        #for x in repeat.split():
        #    user_utterance += x + " "
        #book_title = {'title': repeat}
        #self.speak("Now searching for audiobook " + user_utterance)
        # Gets the JSON from the Librivox API
        # Code taken from https://www.powercms.in/blog/how-get-json-data-remote-url-python-script
        #url = "https://librivox.org/api/feed/audiobooks/?title=" + user_utterance + "&format=json"
        # Convert the JSON to dict
        #raw_data = requests.get(url=url)
        #json_data = raw_data.json()
        #try:
        #    self.speak(json_data["books"][0]["description"])
        #    self.speak("Downloading the audiobook, I will be back with the files in a moment.")
        #    if os.path.isdir(os.getcwd() + "/audiobook-tmp") == False:
        #        os.mkdir('audiobook-tmp')
        #    file_url = json_data["books"][0]["url_zip_file"]
        #    urllib.request.urlretrieve(file_url, os.getcwd() + "/audiobook-tmp/" + json_data["books"][0]["id"] + ".zip") 
        #    self.speak("Download complete. Loading the audiobook.")
        #except:
        #    self.speak("Please provide exact title.")
        

    # The "stop" method defines what Mycroft does when told to stop during
    # the skill's execution. In this case, since the skill's functionality
    # is extremely simple, there is no need to override it.  If you DO
    # need to implement stop, you should return True to indicate you handled
    # it.
    #
    def stop(self):
        pass

# The "create_skill()" method is used to create an instance of the skill.
# Note that it's outside the class itself.
def create_skill():
    return AudiobookSkill()
