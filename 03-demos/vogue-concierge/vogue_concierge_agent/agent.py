from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import SYSTEM_PROMPT
from .tools import (
    search_catalog,
    search_trend,
    check_inventory,
    get_loyalty_discount
)

LLAMA4_SCOUT = "llama-4-scout-17b-16e-instruct-maas"
LLAMA4_MAVERICK = "llama-4-maverick-17b-128e-instruct-maas"
LLAMA3_3 = "llama-3.3-70b-instruct-maas"
GEMINI2_5_FLASH = "gemini-2.5-flash"


def create_agent() -> Agent:
    agent = Agent(
        model=LiteLlm(model=f"vertex_ai/meta/{LLAMA3_3}"),
        # model = GEMINI2_5_FLASH,
        name="vogue_concierge_agent",
        description="A helpful assistant for user questions.",
        instruction=SYSTEM_PROMPT,
        tools=[search_catalog, search_trend, check_inventory, get_loyalty_discount],
    )
    return agent

root_agent = create_agent()
    


