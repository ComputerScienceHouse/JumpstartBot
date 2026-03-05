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
WATCHED_CHANNELS = os.environ.get("SLACK_ANNOUNCEMENT_CHANNELS").split(",")


slack_client = WebClient(token=slack_bot_token)

emoji_list = {}
try:
    emoji_call = slack_client.emoji_list()
    if emoji_call["ok"]:
        emoji_list = emoji_call["emoji"]
except SlackApiError as e:
    logging.warning(f"Could not fetch emojis")

def clean_text(raw):
    """Strip Slack mrkdwn, HTML entities, and formatting characters."""
    text = re. sub (r"<[^>]+>", "", str(raw), flags=re.IGNORECASE)
    text = re.sub(r"&lt;.*?&gt;", "", text, flags=re.IGNORECASE)
    return text. replace("*", ""). replace("_", ""). replace("`", "").strip()

@app.route("/", methods=["GET"])
def index():
    return "Works"

@app.route("/slack/events", methods=["POST"])
def slack_events():
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
                "type": "mrkdwn",
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
            requests.post(response_url, json={"text": "Okay :( maybe next time", "replace_original": True})
        return make_response("", 200)
    
    logging.warning(f"Unknown action_id: {action_id}")
    return make_response("", 200)
