# https://jumpstart-slack.cs.house/slack/events
import os
import sys
import time
import re
import random
import logging
from flask import Flask, request, jsonify, redirect, make_response, Response
import json, random, textwrap, requests
from slackeventsapi import SlackEventAdapter
from slack import WebClient

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Get secrets
slack_verification_secret = os.environ.get("SLACK_VERIFICATION_TOKEN")
slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)
js_auth_token = os.environ.get("JS_AUTH_TOKEN")

# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_client = WebClient(slack_bot_token)

text = ""
username = ""
emoji_call = slack_client.emoji_list()

if emoji_call["ok"] == True:
    emoji_list = emoji_call["emoji"]
else:
    emoji_list = "None"

# Helper for verifying that requests came from Slack
def verify_slack_token(request_token):
    if slack_verification_secret != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, slack_verification_secret))
        return make_response("Request contains invalid Slack verification token", 403)

@app.route("/",  methods=["GET"])
def lol():
    return "Works"

@slack_events_adapter.on("message")
def handle_message(event_data):
    logging.info(event_data)
    message = event_data.get("event")
    channel = message.get("channel")
    subtype = message.get("subtype")
    usernamep = message.get("user")
    textp = message.get("text")

# C04S6SNCS is #announcements
# GTDAHFJCB is private channel
#     if "GTDAHFJCB" in channel:
    if "C04S6SNCS" in channel or "GTDAHFJCB" in channel:
        global text
        global username
        textpp = re.sub('<.*?>', '', str(textp), flags=re.IGNORECASE)
        text = re.sub('[&]lt;.*?[&]gt;', '', textpp, flags=re.IGNORECASE).replace('*', '').replace('_', '').replace('`', '')
        
        # textppp = re.sub('[:].*?[:]', '', textpp, flags=re.IGNORECASE)
        # textpp = re.sub('<[^>]+>', '', textp, flags=re.IGNORECASE)
        username = str(usernamep)
        
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
            slack_client.chat_postMessage(channel=usernamep, text="Would you like to post this message to Jumpstart?\n\n" + text, attachments=attachments_json)

# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    logging.info(form_json)

    # Verify that the request came from Slack
    verify_slack_token(form_json["token"])

    # Check to see what the user's selection was and update the message accordingly
    selection = form_json["actions"][0]["name"]
    
    print(selection)
    if selection == "yes_j":
        global text
        global username
        headers_json = {
            "content-type": "application/json",
            "authorization": js_auth_token
        }
        announcement_json = {
            "ann_body" : text,
            "emoji_list": emoji_list,
            "name": username
        }
        print(announcement_json)
        res = requests.post('https://jumpstart.csh.rit.edu/update-announcement', json=announcement_json, headers=headers_json)
        print(res)
        return make_response("Posting right now :^)", 200)
    elif selection == "no_j":
        personal_message = """:( okay :/ """
        return make_response(personal_message, 200)
    else:
        print("Unknown Response")

    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


@slack_events_adapter.on("error")
def error_handler(err):
    print(f"[ERROR] {str(err)}", file=sys.stderr)

