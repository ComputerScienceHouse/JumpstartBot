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
    message = event_data["event"]
    username = message["user"]
    channel = message["channel"]
    textp = message["text"]
    subtype = message.get("subtype")

# C04S6SNCS is #announcements
# GTDAHFJCB is private channel
    if "C04S6SNCS" in channel or "CRDPKAAUV" in channel:
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
        copy_pastas = ["""My name is Yoshikage Kira. I'm 33 years old. My house is in the northeast section of Morioh, where all the villas are, and I am not married. I work as an employee for the Kame Yu department stores, and I get home every day by 8 PM at the latest. I don't smoke, but I occasionally drink.
I'm in bed by 11 PM, and make sure I get eight hours of sleep, no matter what. After having a glass of warm milk and doing about twenty minutes of stretches before going to bed, I usually have no problems sleeping until morning. Just like a baby, I wake up without any fatigue or stress in the morning. I was told there were no issues at my last check-up.
I'm trying to explain that I'm a person who wishes to live a very quiet life. I take care not to trouble myself with any enemies, like winning and losing, that would cause me to lose sleep at night. That is how I deal with society, and I know that is what brings me happiness. Although, if I were to fight I wouldn't lose to anyone.
""", """You take the moon and you take the sun.
You take everything that sounds like fun.

You stir it all together and then you're done.

Rada rada rada rada rada rada.""", """What the fuck did you just fucking say about me, you little bitch? 
I'll have you know I graduated top of my class in the Navy Seals, and I've been involved in numerous secret raids on Al-Quaeda, and I have over 300 confirmed kills. 
I am trained in gorilla warfare and I'm the top sniper in the entire US armed forces. You are nothing to me but just another target. 
I will wipe you the fuck out with precision the likes of which has never been seen before on this Earth, mark my fucking words. 
You think you can get away with saying that shit to me over the Internet? Think again, fucker. 
As we speak I am contacting my secret network of spies across the USA and your IP is being traced right now so you better prepare for the storm, maggot. 
The storm that wipes out the pathetic little thing you call your life. 
You're fucking dead, kid. I can be anywhere, anytime, and I can kill you in over seven hundred ways, and that's just with my bare hands. 
Not only am I extensively trained in unarmed combat, but I have access to the entire arsenal of the United States Marine Corps and I will use it to its full extent to wipe your miserable ass off the face of the continent, you little shit. 
If only you could have known what unholy retribution your little "clever" comment was about to bring down upon you, maybe you would have held your fucking tongue. 
But you couldn't, you didn't, and now you're paying the price, you goddamn idiot. 
I will shit fury all over you and you will drown in it. 
You're fucking dead, kiddo.""", """hi every1 im new!!!!!!! *holds up spork* my name is katy but u can call me t3h PeNgU1N oF d00m!!!!!!!! lol...as u can see im very random!!!! thats why i came here, 2 meet random ppl like me ^_^... im 13 years old (im mature 4 my age tho!!) i like 2 watch invader zim w/ my girlfreind (im bi if u dont like it deal w/it) its our favorite tv show!!! bcuz its SOOOO random!!!! shes random 2 of course but i want 2 meet more random ppl =) like they say the more the merrier!!!! lol...neways i hope 2 make alot of freinds here so give me lots of commentses!!!!
DOOOOOMMMM!!!!!!!!!!!!!!!! <--- me bein random again ^_^ hehe...toodles!!!!!

love and waffles,

t3h PeNgU1N oF d00m""", """I sexually Identify as an Attack Helicopter. Ever since I was a boy I dreamed of soaring over the oilfields dropping hot sticky loads on disgusting foreigners. People say to me that a person being a helicopter is Impossible and I'm fucking retarded but I don't care, I'm beautiful. I'm having a plastic surgeon install rotary blades, 30 mm cannons and AMG-114 Hellfire missiles on my body. From now on I want you guys to call me "Apache" and respect my right to kill from above and kill needlessly. If you can't accept me you're a heliphobe and need to check your vehicle privilege. Thank you for being so understanding."""]
        lmfao = copy_pastas[random.randrange(0, len(copy_pastas))]
        return make_response(lmfao, 200)
    else:
        print("Unknown Response")

    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


@slack_events_adapter.on("error")
def error_handler(err):
    print(f"[ERROR] {str(err)}", file=sys.stderr)

