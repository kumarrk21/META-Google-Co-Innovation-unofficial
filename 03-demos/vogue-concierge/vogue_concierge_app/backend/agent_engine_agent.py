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
from dotenv import load_dotenv

import vertexai
import config

load_dotenv()

backend_config = config.get_backend_config()

PROJECT_ID = backend_config["PROJECT_ID"]
AGENT_ENGINE_REGION = backend_config["AGENT_ENGINE_REGION"]
AGENT_ENGINE_ID = backend_config["AGENT_ENGINE_ID"]

agent_engine_healthy = "True"
agent_engine_status = ""

try:
    client = vertexai.Client(  
        project=PROJECT_ID,
        location=AGENT_ENGINE_REGION,
    )
    adk_app = client.agent_engines.get(name=f"projects/{PROJECT_ID}/locations/{AGENT_ENGINE_REGION}/reasoningEngines/{AGENT_ENGINE_ID}")
except Exception as e:
    agent_engine_healthy = "False"
    agent_engine_status = f"Unable to connect to Agent Engine agent - {e}"
    print(agent_engine_status)


# ----------------------------------------------------- #
# Create a new session
# ----------------------------------------------------- #
async def _create_session(userId:str) -> str|None:
    """Creates a new session for the user.

    :param userId: The ID of the user.
    :type userId: str
    :return: The session ID, or None if creation failed.
    :rtype: str | None
    """
    try:
        session = await adk_app.async_create_session(user_id=userId)
        return session['id']
    except Exception as e:
        print(f"Error creating session ID - {e}")
        return None

# ----------------------------------------------------- #
# Get existing session
# ----------------------------------------------------- #
async def _get_session(userId:str, sessionId:str) -> str|None:
    """Gets an existing session or creates a new one.

    :param userId: The ID of the user.
    :type userId: str
    :param sessionId: The ID of the session.
    :type sessionId: str
    :return: The session ID, or None if creation failed.
    :rtype: str | None
    """
    try:
        session = await adk_app.async_get_session(user_id=userId, session_id=sessionId)
        sessionId = session['id']
    except Exception as e:
        print(f"Error getting existing session - {e}") 
        sessionId = _create_session(userId)
    
    return sessionId


# ----------------------------------------------------- #
# Run the agent
# ----------------------------------------------------- #
async def _run(userId: str, sessionId: str, message: str) -> str:
    """Runs the agent and returns the response.

    :param userId: The ID of the user.
    :type userId: str
    :param sessionId: The ID of the session.
    :type sessionId: str
    :param message: The message from the user.
    :type message: str
    :return: The response from the agent.
    :rtype: str
    """
    response_text = "I seem to have an hit an issue and unable to proceed. Please try after sometime or raise a support ticket"
    data = []
    async for event in adk_app.async_stream_query(user_id=userId, session_id=sessionId, message=message):
        data.append(event)

    response_text = next((part["text"] 
                   for event in reversed(data) 
                   for part in reversed(event.get("content", {}).get("parts", [])) 
                   if "text" in part), None)
    
    return response_text


# ----------------------------------------------------- #
# Run the agent
# ----------------------------------------------------- # 
async def run(userId: str, sessionId: str, message: str) -> dict :
    """Runs the agent and returns the response.

    :param userId: The ID of the user.
    :type userId: str
    :param sessionId: The ID of the session.
    :type sessionId: str
    :param message: The message from the user.
    :type message: str
    :return: A dictionary containing the response and the session ID.
    :rtype: dict
    """
    if agent_engine_healthy == "False":
        return {
            "response": agent_engine_status,
            "session_id": sessionId,
        }
    
    if not sessionId: 
        sessionId = await _create_session(userId)
    else:
        sessionId = await _get_session(userId, sessionId)

    if not sessionId:
        return {
            "response": "I am unable to establish a session with the agent. Please try after sometime or raise a support ticket",
            "session_id": sessionId,
        }
    
    final_response = await _run(userId,sessionId,message)

    return {
        "response": final_response,
        "session_id": sessionId,
    }


