import os
import sys
from flask import Flask, request, jsonify
import json, random, textwrap, requests
from slackeventsapi import SlackEventAdapter
from slack import WebClient
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", server=app)

# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_client = WebClient(slack_bot_token)

# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]
    txt = message["text"]
    announcement_json = {"text": f"{txt}" }
    post_announcement = requests.post('http://127.0.0.1:5000/announcement', json=announcement_json)
    print(post_announcement.text)
    
    # # If the incoming message contains "hi", then respond with a "Hello" message
    # if message.get("subtype") is None and "hi" in message.get('text'):
        # user = message["user"]
        # message = f"Hello <@{user}>! :tada:"
        # slack_client.chat_postMessage(channel=user, text=message)
        
        # get = requests.get('https://jumpstart.csh.rit.edu/calendar').content
        # print(get)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    print(f"[ERROR] {str(err)}", file=sys.stderr)