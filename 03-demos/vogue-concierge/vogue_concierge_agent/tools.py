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

from dotenv import load_dotenv
import os 

from google.cloud import bigquery
import vertexai
from vertexai import rag

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
RAG_REGION = os.getenv("RAG_REGION")
RAG_CORPUS_NAME = os.getenv("RAG_CORPUS_NAME")

BQ_DATASET_ID = os.getenv("BQ_DATASET_ID")
BQ_DATASET_LOCATION = os.getenv("BQ_DATASET_LOCATION")
BQ_INVENTORY_TABLE = os.getenv("BQ_INVENTORY_TABLE")
BQ_LOYALTY_TABLE = os.getenv("BQ_LOYALTY_TABLE")

bq_client = bigquery.Client(project=PROJECT_ID)

#------------------------------------------------------------------------#
# Get Corpus from display name
#------------------------------------------------------------------------#
def _get_corpus(project_id: str, rag_region: str, rag_corpus_name: str) -> rag.RagCorpus:
    vertexai.init(project=project_id, location=rag_region)
    existing = rag.list_corpora()
    for corpus in existing:
        if corpus.display_name == rag_corpus_name:
            return corpus
    return None

#------------------------------------------------------------------------#
# Catalog Search
#------------------------------------------------------------------------#
def search_catalog(query: str) -> dict:
    """Search the Vogue Concierge product catalog for items matching the query.

    Use this tool when a customer asks about products, recommendations,
    outfit suggestions, or wants to browse the catalog.

    Args:
        query: Natural language search query describing what the customer wants.
               Examples: "summer dress", "leather accessories", "business casual outfit"

    Returns:
        Dictionary with matching products including name, SKU, price, description,
        and image URL for each result.
    """
    try:
        rag_corpus = _get_corpus(PROJECT_ID, RAG_REGION, RAG_CORPUS_NAME)
            
        if rag_corpus is not None:
            rag_resources = [rag.RagResource(rag_corpus=rag_corpus.name)]

            retrieval_config = rag.RagRetrievalConfig(
                top_k=5, 
                filter=rag.Filter(
                    vector_distance_threshold=0.5
                )
            )

            response = rag.retrieval_query(
                rag_resources=rag_resources,
                text=query,
                rag_retrieval_config=retrieval_config
            )
            if response and response.contexts and response.contexts.contexts:
                results = []
                for ctx in response.contexts.contexts:
                    results.append({"content": ctx.text, "score": ctx.score})
                return {"source": "rag", "results": results}
            else:
                return {"error": "No results found in RAG corpus."}
        else:
            print("Unable to search RAG corpus")
            return {"error": f"Unable to find RAG corpus with name {RAG_CORPUS_NAME}"}
    except Exception as e:
        print(f"RAG search failed ({e})")
        return {"error": str(e)}
        

#------------------------------------------------------------------------#
# Trend Search
#------------------------------------------------------------------------#

def search_trend(query: str) -> dict:
    """Search the current fashion trend report for style insights and seasonal trends.

    Use this tool when customers ask about what is trending, current fashion
    directions, seasonal must-haves, or style forecasts.

    Args:
        query: Natural language query about fashion trends.
               Examples: "summer 2026 trends", "what colors are in this season"

    Returns:
        Dictionary with relevant trend insights and recommendations.
    """
    try:
        rag_corpus = _get_corpus(PROJECT_ID, RAG_REGION, RAG_CORPUS_NAME)
            
        if rag_corpus is not None:
            rag_resources = [rag.RagResource(rag_corpus=rag_corpus.name)]
            retrieval_config = rag.RagRetrievalConfig(
                top_k=5, 
                filter=rag.Filter(
                    vector_distance_threshold=0.5
                )
            )

            response = rag.retrieval_query(
                rag_resources=rag_resources,
                text=query,
                rag_retrieval_config=retrieval_config
            )

            if response and response.contexts and response.contexts.contexts:
                results = []
                for ctx in response.contexts.contexts:
                    results.append({"content": ctx.text, "score": ctx.score})
                return {"source": "rag", "results": results}
            else:
                return {"error": "No results found in RAG corpus."}
        else:
            print("Unable to search RAG corpus")
            return {"error": f"Unable to find RAG corpus with name {RAG_CORPUS_NAME}"}
    except Exception as e:
        print(f"RAG search failed ({e})")
        return {"error": str(e)}
    

#------------------------------------------------------------------------#
# Check Inventory
#------------------------------------------------------------------------#
def check_inventory(sku: str) -> dict:
    """Check real-time inventory levels for a specific product SKU.

    Use this tool when a customer asks about stock availability, sizes in stock,
    or whether an item is available.

    Args:
        sku: The product SKU to check (e.g. "SKU-001", "SKU-015").

    Returns:
        Dictionary with current stock levels per size and total units available.
    """
    try:
        query = f"""
            SELECT 
                sku, 
                product_name as name, 
                price, 
                size, 
                quantity_in_stock
            FROM `{PROJECT_ID}.{BQ_DATASET_ID}.{BQ_INVENTORY_TABLE}`
            WHERE sku = @sku
        """
        job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("sku", "STRING", sku)]
            )

        rows = list(bq_client.query(query, job_config=job_config))

        if not rows:
            return {"error": f"Product {sku} not found in catalog."}
        
        inventory = {row.size: row.quantity_in_stock for row in rows}
        total = sum(inventory.values())

        product = rows[0]

        return {
            "sku": sku,
            "name": product["name"],
            "price": product["price"],
            "inventory_by_size": inventory,
            "total_units": total,
            "low_stock_alert": total < 10,
        }
    except Exception as e:
        print(f"Error checking inventory for SKU {sku}: {e}")
        return {"error": f"Error checking inventory: {e}"}

#------------------------------------------------------------------------#
# Get Loyalty discount
#------------------------------------------------------------------------#
def get_loyalty_discount(customer_id: str) -> dict:
    """Look up loyalty program status and available discounts for a customer.

    Use this tool when a customer asks about their loyalty status, available
    discounts, or membership perks.

    Args:
        customer_id: The customer ID (e.g. "CUST-1042").

    Returns:
        Dictionary with loyalty tier, discount percentage, and points balance.
    """
    try:
        query = f"""
            SELECT 
                customer_id, 
                customer_name, 
                tier, 
                discount_percent, 
                points_balance, 
                free_shipping, 
                member_since
            FROM `{PROJECT_ID}.{BQ_DATASET_ID}.{BQ_LOYALTY_TABLE}`
            WHERE customer_id = @customer_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)]
        )

        results = list(bq_client.query(query, job_config=job_config))

        if not results:
            return {"error": f"Customer ID {customer_id} not found."}
        
        row = results[0]

        return {
            "customer_id": row.customer_id,
            "tier": row.tier,
            "discount_percent": row.discount_percent,
            "free_shipping": row.free_shipping,
            "points_balance": row.points_balance,
            "message": f"As a {row.tier} member, you get {row.discount_percent}% off!"
        }
    except Exception as e:
        print(f"Error getting loyalty discount for customer {customer_id}: {e}")
        return {"error": f"Error getting loyalty discount: {e}"}
    