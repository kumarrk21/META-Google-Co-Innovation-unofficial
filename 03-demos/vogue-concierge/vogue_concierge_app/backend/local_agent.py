import os
from typing import Any 
from dotenv import load_dotenv
import uuid
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
import json
import re
from google.cloud import storage
from google.auth import impersonated_credentials, default
import datetime

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "vogue_concierge_agent" )
LOCAL_PORT = os.getenv("LOCAL_PORT", 8000 )
BASE_URL = f"http://localhost:{LOCAL_PORT}"


# ----------------------------------------------------- #
# Get existing session or create new session
# ----------------------------------------------------- #
def _get_session(userId:str, sessionId:str) -> str:
    # Create a session
    url = f"{BASE_URL}/apps/{APP_NAME}/users/{userId}/sessions/{sessionId}"
    try:
        response = requests.post(url)
        match response.status_code:
            case 200:
                data = response.json()
                return data["id"]
            case 409: # Conflict, Session already exists
                return sessionId
            case _:
                response.raise_for_status()
        
    except RequestException as req_err:
        print(f"HTTP error occurred: {req_err}")
        return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

# ----------------------------------------------------- #
# Get response text from the agent
# ----------------------------------------------------- # 
def _get_response_text(data: Any) -> str|None:
    response_text = next((part["text"] 
                   for event in reversed(data) 
                   for part in reversed(event.get("content", {}).get("parts", [])) 
                   if "text" in part), None)
    return response_text

# ----------------------------------------------------- #
# Run the  agent syncrhonously
# ----------------------------------------------------- # 
def _run(userId: str, sessionId: str, message: str) -> str:
    url = f"{BASE_URL}/run"
    body = {
        "appName": APP_NAME,
        "userId": userId,
        "sessionId": sessionId,
        "newMessage": {
            "role": "user",
            "parts": [
                {
                    "text": message
                } 
            ]
        }
    }

    try:
        response = requests.post(url, json=body)
        match response.status_code:
            case 200:
                data = response.json()
                return _get_response_text(data) or "Sorry, I received no text response. Please try again later"

            case _:
                response.raise_for_status()
        
    except RequestException as req_err:
        print(f"HTTP error occurred: {req_err}")
        return f"Request Exception when calling agent: {str(req_err)}"
    except Exception as e:
        print(f"Error in calling the agent: {e}")
        return f"Error in calling the agent: {str(e)}"


# ----------------------------------------------------- #
# Run the agent
# ----------------------------------------------------- # 
def run(userId: str, sessionId: str, message: str) -> dict :

    if not sessionId:
        sessionId = str(uuid.uuid4())

    sessionId = _get_session(userId, sessionId)

    final_response = _run(userId,sessionId,message)

    return {
        "response": final_response,
        "session_id": sessionId,
    }
