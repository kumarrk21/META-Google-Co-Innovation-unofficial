import os
from dotenv import load_dotenv

import vertexai

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
AGENT_ENGINE_REGION = os.getenv("AGENT_ENGINE_REGION")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")

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


