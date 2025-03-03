import hashlib
from flask import Flask, request, jsonify, Response
import requests
import io
import json
import re
import uuid
import random
import time
from functools import wraps

app = Flask(__name__)

TARGET_URL = "https://grok.com/rest/app-chat/conversations/new"
CHECK_URL = "https://grok.com/rest/rate-limits"
MODELS = ["grok-2", "grok-3", "grok-3-thinking"]
CONFIG = {}
TEMPORARY_MODE = False
COOKIE_NUM = 0
COOKIE_LIST = []
LAST_COOKIE_INDEX = {}
PASSWORD = ""


def resolve_config():
    global COOKIE_NUM, COOKIE_LIST, LAST_COOKIE_INDEX, TEMPORARY_MODE, CONFIG, PASSWORD
    with open("config.json", "r") as f:
        CONFIG = json.load(f)
    for cookies in CONFIG["cookies"]:
        session = requests.Session()
        session.headers.update(
            {"user-agent": random.choice(USER_AGENTS), "cookie": cookies}
        )

        COOKIE_LIST.append(session)
    COOKIE_NUM = len(COOKIE_LIST)
    TEMPORARY_MODE = CONFIG["temporary_mode"]
    for model in MODELS:
        LAST_COOKIE_INDEX[model] = CONFIG["last_cookie_index"][model]
    PASSWORD = CONFIG.get("password", "")


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not PASSWORD:
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or not check_auth(auth.token):
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)

    return decorated


def check_auth(password):
    return hashlib.sha256(password.encode()).hexdigest() == PASSWORD


def get_next_account(model):
    current = (LAST_COOKIE_INDEX[model] + 1) % COOKIE_NUM
    LAST_COOKIE_INDEX[model] = current
    CONFIG["last_cookie_index"][model] = current
    with open("config.json", "w") as f:
        json.dump(CONFIG, f, indent=4)
    return COOKIE_LIST[current]


def send_message(message, model, disable_search, force_concise, is_reasoning):
    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://grok.com",
        "priority": "u=1, i",
        "referer": "https://grok.com/",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    payload = {
        "temporary": TEMPORARY_MODE,
        "modelName": model,
        "message": message,
        "disableSearch": disable_search,
        "forceConcise": force_concise,
        "isReasoning": is_reasoning,
    }

    session = get_next_account(model)
    response = session.post(TARGET_URL, headers=headers, json=payload)
    return response.json()


def send_message_non_stream(message, model, disable_search, force_concise, is_reasoning):
    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://grok.com",
        "priority": "u=1, i",
        "referer": "https://grok.com/",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    payload = {
        "temporary": TEMPORARY_MODE,
        "modelName": model,
        "message": message,
        "disableSearch": disable_search,
        "forceConcise": force_concise,
        "isReasoning": is_reasoning,
    }

    session = get_next_account(model)
    response = session.post(TARGET_URL, headers=headers, json=payload)
    return response.json()


def check_rate_limit(session, model, is_reasoning):
    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://grok.com",
        "priority": "u=1, i",
        "referer": "https://grok.com/",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    payload = {
        "requestKind": "REASONING" if is_reasoning else "DEFAULT",
        "modelName": model,
    }

    response = session.post(CHECK_URL, headers=headers, json=payload)
    return response.json()


resolve_config()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9898)
