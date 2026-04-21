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

"""
Test Agent — Vogue Concierge
================================
Validates the ADK agent initializes correctly with all tools.

Usage:
    python tests/test_agent.py
"""

import sys
import os
from yaml_parser import YAMLParser
import vertexai
import asyncio
import traceback

from vogue_concierge_agent.agent import create_agent
from vogue_concierge_agent.tools import (
    search_catalog,
    search_trend,
    check_inventory,
    get_loyalty_discount
)


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ----------------------------------------------------- #
# Test agent creation
# ----------------------------------------------------- #

def test_agent_creation():
    """Test that the agent creates successfully."""
    print("Testing agent creation...")
    
    agent = create_agent()

    print(f"  Agent name: {agent.name}")
    print(f"  Model: {agent.model}")
    print(f"  Tools: {len(agent.tools)}")
    for tool in agent.tools:
        name = getattr(tool, '__name__', getattr(tool, 'name', str(tool)))
        print(f"    - {name}")

    assert agent.name == "vogue_concierge_agent"
    print("  PASSED")
    return True


# ----------------------------------------------------- #
# Test catalog search
# ----------------------------------------------------- #

def test_catalog_search():
    """Test the catalog search tool."""
    print("\nTesting catalog_search tool...")

    
    result = search_catalog("summer wedding dress")

    print(f"  Source: {result['source']}")
    print(f"  Results: {len(result['results'])}")
    for r in result['results'][:3]:
        if 'name' in r:
            print(f"    - {r['sku']}: {r['name']} (${r['price']})")
        else:
            print(f"    - {r.get('content', '')[:80]}...")

    assert len(result['results']) > 0
    print("  PASSED")
    return True


# ----------------------------------------------------- #
# Test trend search
# ----------------------------------------------------- #
def test_trend_search():
    """Test the trend search tool."""
    print("\nTesting trend_search tool...")

    
    result = search_trend("evening glamour cocktail")

    print(f"  Source: {result['source']}")
    print(f"  Results: {len(result['results'])}")
    for r in result['results'][:2]:
        print(f"    - {r['content'][:80]}...")

    assert len(result['results']) > 0
    print("  PASSED")
    return True



# ----------------------------------------------------- #
# Test fallback tools
# ----------------------------------------------------- #
def test_fallback_tools():
    """Test the fallback BigQuery tools."""
    print("\nTesting fallback tools...")


    inv = check_inventory("SKU-001")
    print(f"  Inventory for SKU-001: {inv['total_units']} units")
    assert 'sku' in inv

    loyalty = get_loyalty_discount("CUST-1042")
    print(f"  Loyalty for CUST-1042: {loyalty['tier']} ({loyalty['discount_percent']}% off)")
    assert 'tier' in loyalty

    print("  PASSED")
    return True

# ----------------------------------------------------- #
# Local test
# ----------------------------------------------------- #
def test_local() -> None:
    """Runs all the local tests."""
    print("=" * 60)
    print("Vogue Concierge — Agent Tests")
    print("=" * 60)

    results = []
    results.append(test_catalog_search())
    results.append(test_trend_search())
    results.append(test_fallback_tools())
    results.append(test_agent_creation())

    print(f"\n{'=' * 60}")
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'=' * 60}")

    return all(results)

# ----------------------------------------------------- #
# Agent Engine test
# ----------------------------------------------------- #
async def test_ae(project_id: str, agent_engine_region: str, agent_engine_id: str) -> None:
    """Tests the agent deployed to Agent Engine.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param agent_engine_region: The region of the Agent Engine.
    :type agent_engine_region: str
    :param agent_engine_id: The ID of the Agent Engine.
    :type agent_engine_id: str
    """
    client = vertexai.Client(  # For service interactions via client.agent_engines
        project=project_id,
        location=agent_engine_region,
    )
    ae_resource = f"projects/{project_id}/locations/{agent_engine_region}/reasoningEngines/{agent_engine_id}"
    # print(ae_resource)
    adk_app = client.agent_engines.get(name=ae_resource)
    USER_ID = "test_user"
    session = await adk_app.async_create_session(user_id=USER_ID)
    session_id = session.get('id')

    try:
        generator = adk_app.async_stream_query(
           user_id=USER_ID,
            session_id=session_id,
            message="I'm attending a summer wedding in Tuscany — what should I wear?"
        )
        async for event in generator:
            print("Received event:", event)
    except Exception as e:
        print(f"Error during stream: {e}")
        traceback.print_exc()
        
    await adk_app.async_delete_session(user_id=USER_ID, session_id=session_id)


# ----------------------------------------------------- #
# Main function
# ----------------------------------------------------- #
def main(project_id: str, agent_engine_region: str, agent_engine_id: str, target: str) -> None:
    match target:
        case "local":
            test_local()
            pass
        case "ae":  # test agent engine
            asyncio.run(test_ae(project_id, agent_engine_region, agent_engine_id))
            pass
        case _:
            pass


