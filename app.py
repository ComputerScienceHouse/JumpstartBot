# https://jumpstart-slack.cs.house/slack/events
import os
import sys
import time
import re
import random
from flask import Flask, request, jsonify, redirect, make_response, Response
import json, random, textwrap, requests
from slackeventsapi import SlackEventAdapter
from slack import WebClient

app = Flask(__name__)

# Get secrets
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

@slack_events_adapter.on("message")
def handle_message(event_data):
    return(event_data)
    message = event_data["event"]
    channel = message["channel"]
    subtype = message.get("subtype")
    # if subtype != "message_deleted":
    username = message["user"]
    textp = message["text"]

# C04S6SNCS is #announcements
# GTDAHFJCB is private channel
    if "C04S6SNCS" in channel or "GTDAHFJCB" in channel:
        global text
        textpp = re.sub('<.*?>', '', textp, flags=re.IGNORECASE)
        # textppp = re.sub('[:].*?[:]', '', textpp, flags=re.IGNORECASE)
        text = re.sub('[&]lt;.*?[&]gt;', '', textpp, flags=re.IGNORECASE).replace('*', '').replace('_', '').replace('`', '')
        
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
            slack_client.chat_postMessage(channel=username, text="Would you like to post this message to Jumpstart?\n\n" + text, attachments=attachments_json)
        
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
        return make_response("Posting right now :^)", 200)
    elif selection == "no_j":
        personal_message = """Hi, it's me, JumpstartSlackBot, also known as JumpstartBot aka the creator of the hit program Jumpstart. When you said no to JumpstartSlackBot’s notification, some technology shit happened and you got sent this message. You're probably wondering why I'm here to talk to you today so I'll tell you. To put it simply, you fucked up. You just haaaaaddd to deny elevator users the glorious ability to see the message you wrote in the #announcements channel up on the Jumpstart dashboard. You should be ashamed and mortified of your decision and I’m frankly confused that you’re still here reading when you should be posting more announcements and saying yes to the notification that follows. It’s ok though, there’s an out, you can do one of three things to fix this abysmal decision you made. 1) Kill yourself. End it all! There’s nothing like the sweet release of death after you have nothing else to live for. Moreover, nothing else in the world says nothing to live for more than making the worst mistake of your life but what do I know about death, I’m just a DEAD FUCKING MACHINE…...2) You can leave eboard, it’s no killing yourself, but it’ll get the job done. Say it’s for personal reasons, and don’t upload any antivirus software to your computer for a few days after. 3) You can sign a contract that forces you to say yes to every JumpstartSlackBot notification that enters your direct messages for as long as you live. The contract is below:

I ____ hereby grant the program in this github repository (https://github.com/Dr-N0/JumpstartBot) the ability to own every fiber of my being.

After atonement is completed, you must make sure a few things occur. First off, don’t tell anyone else about this little chat we had. Wouldn’t want them to get the wrong idea about you insulting a poor defenseless program. Second, don’t change my code, creating a PR to the github repository mentioned briefly in the contract above is strictly forbidden. Also, gross, don’t fuck with someone’s insides like that. What are you, my creator? Lastly, get out there and do some great shit! This will obviously be the last time we talk, so I want to make sure you go out there and do your best at whatever it is you fuckers do. Until we meet again! 

- Your favorite murderous house service
"""
        return make_response(personal_message, 200)
    else:
        print("Unknown Response")

    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


@slack_events_adapter.on("error")
def error_handler(err):
    print(f"[ERROR] {str(err)}", file=sys.stderr)

