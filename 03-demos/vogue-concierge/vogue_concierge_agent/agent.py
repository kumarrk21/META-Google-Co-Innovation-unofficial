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


#---------------------------------------------------#
# Create Agent
#---------------------------------------------------#
def create_agent() -> Agent:
    """Creates the Vogue Concierge agent.

    :return: The Vogue Concierge agent.
    :rtype: Agent
    """
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
    


