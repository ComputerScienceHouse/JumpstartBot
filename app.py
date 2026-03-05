import os
import sys
import re
import json
import hmac
import hashlib
import logging
import requests
from flask import Flask, request, make_response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
js_auth_token = os.environ.get("JS_AUTH_TOKEN")

slack_client = WebClient(token=slack_bot_token)

emoji_list = {}
try:
    emoji_call = slack_client.emoji_list()
    if emoji_call["ok"]:
        emoji_list = emoji_call["emoji"]
except SlackApiError as e:
    logging.warning(f"Could not fetch emojis")

def verify_slack_signature(req):
    timestamp = req.headers.get("X-Slack-Request-Timestamp", "")
    slack_signature = req.headers.get("X-Slack-Signature", "")
    raw_body = req.get_data(as_text=True)
    
    basestring = f"v0: {timestamp}: {raw_body}"
    computed = "v0=" + hmac.new(
        slack_signing_secret.encode("utf-8"),
        basestring.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, slack_signature)

def clean_text(raw):
    """Strip Slack mrkdwn, HTML entities, and formatting characters."""
    text = re. sub (r"<[^>]+>", "", str(raw), flags=re.IGNORECASE)
    text = re.sub(r"&lt;.*?&gt;", "", text, flags=re.IGNORECASE)
    return text. replace("*", ""). replace("_", ""). replace("`", "").strip()

WATCHED_CHANNELS = {"C04S6SNCS", "GTDAHFJCB"}

NO_MESSAGE = """Hi, it's me, JumpstartSlackBot, also known as JumpstartBot aka the creator of the hit program Jumpstart. When you said no to JumpstartSlackBot’s notification, some technology shit happened and you got sent this message. You're probably wondering why I'm here to talk to you today so I'll tell you. To put it simply, you fucked up. You just haaaaaddd to deny elevator users the glorious ability to see the message you wrote in the #announcements channel up on the Jumpstart dashboard. You should be ashamed and mortified of your decision and I’m frankly confused that you’re still here reading when you should be posting more announcements and saying yes to the notification that follows. It’s ok though, there’s an out, you can do one of three things to fix this abysmal decision you made. 1) Kill yourself. End it all! There’s nothing like the sweet release of death after you have nothing else to live for. Moreover, nothing else in the world says nothing to live for more than making the worst mistake of your life but what do I know about death, I’m just a DEAD FUCKING MACHINE…...2) You can leave eboard, it’s no killing yourself, but it’ll get the job done. Say it’s for personal reasons, and don’t upload any antivirus software to your computer for a few days after. 3) You can sign a contract that forces you to say yes to every JumpstartSlackBot notification that enters your direct messages for as long as you live. The contract is below:

I ____ hereby grant the program in this github repository (https://github.com/Dr-N0/JumpstartBot) the ability to own every fiber of my being.

After atonement is completed, you must make sure a few things occur. First off, don’t tell anyone else about this little chat we had. Wouldn’t want them to get the wrong idea about you insulting a poor defenseless program. Second, don’t change my code, creating a PR to the github repository mentioned briefly in the contract above is strictly forbidden. Also, gross, don’t fuck with someone’s insides like that. What are you, my creator? Lastly, get out there and do some great shit! This will obviously be the last time we talk, so I want to make sure you go out there and do your best at whatever it is you fuckers do. Until we meet again! 

- Your favorite murderous house service
"""

@app.route("/", methods["GET"])
def index():
    return "Works"

@app.route("/slack/events", methods=["POST"])
def slack_events():
    if not verify_slack_signature(request):
        return make_response("Invalid request signature", 403)
    
    if request.content_type == "application/json":
        body = request.get_json()
        if body and body.get("type") == "url_verification":
            return make_response(body["challenge"], 200)
        
    body = request.get_json(force=True)
    if not body:
        return make_response(body["challenge"], 200)
    
    logging.info(body)

    event = body.get("event", {})
    if event.get("type") != "message":
        return make_response("", 200)
    
    channel = event.get("channel", "")
    subtype = event.get("subtype")
    user_id = event.get("user")
    raw_text = event.get("text", "")

    if subtype is not None:
        return make_response("", 200)
    
    if not any(ch in channel for ch in WATCHED_CHANNELS):
        return make_response("", 200)

    cleaned = clean_text(raw_text)
    payload_value = json.dumps({"text": cleaned, "user": user_id})

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrdwn",
                "text": f"Would you like to post this message to Jumpstart?\n\n{cleaned}",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Yes"},
                    "style": "primary",
                    "action_id": "yes_j",
                    "value": payload_value,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "No"},
                    "style": "danger",
                    "action_id": "no_j",
                    "value": "no",
                },
            ],
        },
    ]

    try:
        slack_client.chat_postMessage(channel=user_id, text="Would you like to post this message to Jumpstart?", blocks=blocks)
    except SlackApiError as e:
        logging.error(f"Failed to DM user {user_id}: {e}")

    return make_response("", 200)


@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    if not verify_slack_signature(request):
        return make_response("Invalid request signature", 403)
    
    form_json = json.loads(request.form["payload"])
    logging.info(form_json)

    if form_json.get("type") != "block_actions":
        return make_response("", 200)
    
    action = form_json["actions"][0]
    action_id = action.get("action_id")
    response_url = form_json.get("response_url")

    if action_id == "yes_j":
        value = json.loads(action.get("value", "{}"))
        text = value.get("text", "")
        user = value.get("user", "")

        headers = {
            "content-type": "application/json",
            "authorization": js_auth_token,
        }

        announcement = {
            "ann_body": text,
            "emoji_list": emoji_list,
            "name": user,
        }

        logging.info(announcement)
        res = requests.post("https://jumpstart.csh.rit.edu/update-announcement", json=announcement, headers=headers)
        logging.info(f"Jumpstart response: {res.status_code}")

        if response_url:
            requests.post(response_url, json={"text": "Posting right now :^)", "replace_original": True})

        return make_response("", 200)
    
    elif action_id == "no_j":
        if response_url:
            requests.post(response_url, json={"text": NO_MESSAGE, "replace_original": True})
        return make_response("", 200)
    
    logging.warning(f"Unknown action_id: {action_id}")
    return make_response("", 200)
