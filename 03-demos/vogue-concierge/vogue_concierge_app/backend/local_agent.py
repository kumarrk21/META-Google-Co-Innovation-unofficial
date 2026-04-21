# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
import config

load_dotenv()

backend_config = config.get_backend_config()
APP_NAME = backend_config["APP_NAME"]
LOCAL_PORT = backend_config["LOCAL_PORT"]
BASE_URL = f"http://localhost:{LOCAL_PORT}"


# ----------------------------------------------------- #
# Get existing session or create new session
# ----------------------------------------------------- #
def _get_session(userId:str, sessionId:str) -> str:
    """Gets an existing session or creates a new one for the local agent.

    :param userId: The ID of the user.
    :type userId: str
    :param sessionId: The ID of the session.
    :type sessionId: str
    :return: The session ID.
    :rtype: str
    """
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
    """Extracts the response text from the agent's output data.

    :param data: The response data from the agent.
    :type data: Any
    :return: The extracted response text, or None if not found.
    :rtype: str | None
    """
    response_text = next((part["text"] 
                   for event in reversed(data) 
                   for part in reversed(event.get("content", {}).get("parts", [])) 
                   if "text" in part), None)
    return response_text

# ----------------------------------------------------- #
# Run the  agent syncrhonously
# ----------------------------------------------------- # 
def _run(userId: str, sessionId: str, message: str) -> str:
    """Runs the local agent synchronously.

    :param userId: The ID of the user.
    :type userId: str
    :param sessionId: The ID of the session.
    :type sessionId: str
    :param message: The message from the user.
    :type message: str
    :return: The response from the agent.
    :rtype: str
    """
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
    """Runs the local agent and returns the response.

    :param userId: The ID of the user.
    :type userId: str
    :param sessionId: The ID of the session.
    :type sessionId: str
    :param message: The message from the user.
    :type message: str
    :return: A dictionary containing the response and the session ID.
    :rtype: dict
    """

    if not sessionId:
        sessionId = str(uuid.uuid4())

    sessionId = _get_session(userId, sessionId)

    final_response = _run(userId,sessionId,message)

    return {
        "response": final_response,
        "session_id": sessionId,
    }
