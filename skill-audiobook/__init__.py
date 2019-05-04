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

from adapt.intent import IntentBuilder
from mycroft.audio import wait_while_speaking
from mycroft.skills.core import MycroftSkill, intent_handler, intent_file_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
import traceback
from requests import Session

import urllib, json
import requests
from urllib.request import urlopen


# Each skill is contained within its own class, which inherits base methods
# from the MycroftSkill class.  You extend this class as shown below.

# Audiobook Skill, based on this feature request on github: https://github.com/MycroftAI/mycroft-skills/issues/47
# Used the Speak skill as a base.

class AudiobookSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(AudiobookSkill, self).__init__(name="AudiobookSkill")
        
        # TODO: Initialize working variables used within the skill.
        

    # Plays the audiobook.
    # Idea: Will save the audiobook zip file, then extract it, before
    # it can be played

    @intent_handler(IntentBuilder("").require("Read").require("Audiobook"))
    def handle_read_intent(self, message):
        # Get audiobook title from utterance
        utterance = message.data.get('utterance')
        repeat = re.sub('^.*?' + message.data['Audiobook'], '', utterance)
        user_utterance = ""
        for x in repeat.split():
            user_utterance += x + " "
        book_title = {'title': repeat}
        self.speak("Now searching for audiobook " + user_utterance)
        # Gets the JSON from the Librivox API
        # Code taken from https://www.powercms.in/blog/how-get-json-data-remote-url-python-script
        url = "https://librivox.org/api/feed/audiobooks/?title=" + user_utterance + "&format=json"
        headers = {'content-type': 'application/json; charset=utf-8'}
        # Convert the JSON to dict
        raw_data = requests.get(url=url)
        json_data = raw_data.json()
        try:
            self.speak(json_data["books"][0]["description"])
            self.speak("Downloading the audiobook, I will be back with the files in a moment.")
            if os.path.isdir(os.getcwd() + "/audiobook-tmp") == False:
                os.mkdir('audiobook-tmp')
            file_url = json_data["books"][0]["url_zip_file"]
            urllib.request.urlretrieve(file_url, os.getcwd() + "/audiobook-tmp/" + json_data["books"][0]["id"] + ".zip") 
            self.speak("Download complete. Loading the audiobook.")
        except:
            self.speak("Please provide exact title.")
        

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
