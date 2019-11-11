import os
import sys
import time
from flask import Flask, request, jsonify, redirect, make_response, Response
import json, random, textwrap, requests
from slackeventsapi import SlackEventAdapter
from slack import WebClient

app = Flask(__name__)

# Our app's Slack Event Adapter for receiving actions via the Events API
slack_verification_secret = os.environ.get("SLACK_VERIFICATION_TOKEN")
slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_client = WebClient(slack_bot_token)

text = ""

# Helper for verifying that requests came from Slack
def verify_slack_token(request_token):
    if slack_verification_secret != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, slack_verification_secret))
        return make_response("Request contains invalid Slack verification token", 403)

@app.route("/",  methods=["GET"])
def lol():
    return "Works"

# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():

    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Verify that the request came from Slack
    verify_slack_token(form_json["token"])

    # Check to see what the user's selection was and update the message accordingly
    selection = form_json["actions"][0]["name"]

    print(selection)
    if selection == "yes_j":
        global text
        announcement_json = {"ann_body" : text }
        res = requests.post('https://jumpstart.csh.rit.edu/update-announcement', json=announcement_json)
        print(res)
        print("Interactivity API: " + text)
        return make_response("Posting right now :)", 200)
    elif selection == "no_j":
        return make_response("Aight bet", 200)
    else:
        print("Unknown Response")

    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)

@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]
    
    user = message["user"]
    channel = message["channel"]
    global text 
    text = message["text"]
    print("Event API: " + text)
    subtype = message.get("subtype")


    # A Dictionary of message attachment options
    attachments_json = [
        {
            "text": "Options:",
            "fallback": "You are unable to post this to Jumpstart",
            "callback_id": "send_to_jumpstart",
            "color": "#800080",
            "attachment_type": "default",
            "actions": [
                {
                    "name": "yes_j",
                    "text": "Yes",
                    "style": "primary",
                    "type": "button",
                    "value": "yes"
                },
                {
                    "name": "no_j",
                    "text": "No",
                    "style": "danger",
                    "type": "button",
                    "value": "no"
                }
            ]
        }
    ]

    if subtype == None:
        slack_client.chat_postMessage(channel=user, text="Would you like to post this message to Jumpstart?", attachments=attachments_json)
        

@slack_events_adapter.on("error")
def error_handler(err):
    print(f"[ERROR] {str(err)}", file=sys.stderr)

