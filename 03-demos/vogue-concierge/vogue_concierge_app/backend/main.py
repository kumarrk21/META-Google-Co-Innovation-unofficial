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
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from google.adk.sessions import InMemorySessionService
from requests import session

from google.cloud import storage
import google.auth
from google.auth import impersonated_credentials, default
import datetime
import json

import local_agent
import agent_engine_agent
import config

# ----------------------------------------------------- #
# Run the agent
# ----------------------------------------------------- # 
load_dotenv() # Ensure .env is loaded at the start
app = FastAPI()

backend_config = config.get_backend_config()
IS_AGENT_LOCAL = backend_config["IS_AGENT_LOCAL"]
PROJECT_ID = backend_config["PROJECT_ID"]
BUCKET_NAME = backend_config["BUCKET_NAME"]
IMAGE_FOLDER = backend_config["IMAGE_FOLDER"]
DATA_FOLDER = backend_config["DATA_FOLDER"]
PRODUCT_DATA_FILE = backend_config["PRODUCT_DATA_FILE"]
CLOUD_RUN_SA = backend_config["CLOUD_RUN_SA"]


# ----------------------------------------------------- #
# Load Product data from GCS
# TODO: Move this to BQ later
# ----------------------------------------------------- # 
def _get_catalog_data():
    """Loads product catalog data from Google Cloud Storage.

    :return: The product catalog data as a JSON object, or None if an error occurred.
    :rtype: dict | None
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"{DATA_FOLDER}/{PRODUCT_DATA_FILE}")
        data = blob.download_as_text()
        return json.loads(data)
    except storage.exceptions.NotFound:
        print(f"Error: Catalog file not found in GCS bucket: gs://{BUCKET_NAME}/{DATA_FOLDER}/{PRODUCT_DATA_FILE}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in catalog file: gs://{BUCKET_NAME}/{DATA_FOLDER}/{PRODUCT_DATA_FILE}")
        return None
    except Exception as e:
        print(f"Error loading catalog from GCS bucket: {e}")
        return None

# ----------------------------------------------------- #
# Get Signed URL with impersonation
# ----------------------------------------------------- # 
def _get_signed_url_for_image(product: dict) -> dict:
    """Generates a signed URL for a product image.

    :param product: The product dictionary containing image_url.
    :type product: dict
    :return: The product dictionary with the updated image_url.
    :rtype: dict
    """
    updated_product = product
    try:
        credentials, project_id = google.auth.default()
        
        # If the default credentials are not a service account, use impersonation
        # if not hasattr(credentials, 'service_account_email'):
        target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        credentials = impersonated_credentials.Credentials(
                source_credentials=credentials,
                target_principal=CLOUD_RUN_SA,
                target_scopes=target_scopes,
        )

        storage_client = storage.Client(credentials=credentials, project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(product['image_url'])

        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="GET",
        )
        updated_product['image_url'] = url

    except Exception as e:
        print(f"Error getting signed url: {e}")

    return updated_product
        

# ----------------------------------------------------- #
# Extract product details
# ----------------------------------------------------- # 
def _extract_product_mentions(text: str) -> list:
    """Extracts mentioned products (SKUs and names) from a given text.

    :param text: The text to extract product mentions from.
    :type text: str
    :return: A list of dictionaries, each representing a mentioned product with a signed image URL.
    :rtype: list
    """
    catalog_data = _get_catalog_data()
    if not catalog_data:
        return []

    mentioned_products = []
    seen_skus = set()
    
    # Create a mapping for quick lookup
    sku_to_product = {product["sku"]: product for product in catalog_data}
    name_to_sku = {product["name"].lower(): product["sku"] for product in catalog_data}

    # Extract SKUs using regex
    sku_pattern = re.compile(r"SKU-0*(\d{1,3})")  # Adjusted to match up to 3 digits
    for match in sku_pattern.findall(text):
        sku = f"SKU-{int(match):03d}"
        if sku in sku_to_product and sku not in seen_skus:
            product = sku_to_product[sku]
            mentioned_products.append(_get_signed_url_for_image(product.copy()))
            seen_skus.add(sku)

    # Extract product names
    for product_name_lower, sku in name_to_sku.items():
        if product_name_lower in text.lower() and sku not in seen_skus:
            product = sku_to_product[sku]
            mentioned_products.append(_get_signed_url_for_image(product.copy()))
            seen_skus.add(sku)
            
    return mentioned_products[:6]


# API Routes (Define these BEFORE mounting the UI)
# ----------------------------------------------------- #
# Chat API
# ----------------------------------------------------- # 
@app.post("/api/chat")
async def chat(request: Request):
    """Handles chat requests by interacting with the agent.

    :param request: The FastAPI request object.
    :type request: Request
    :raises HTTPException: If no messages are provided or Agent Engine is not connected.
    :return: A dictionary containing the agent's response, session ID, and mentioned products.
    :rtype: dict
    """
    body = await request.json()
    messages = body.get("messages",[])
    if not messages:
        raise HTTPException(status_code=400, detail="No messages or Agent Engine not connected")

    session_id = body.get("session_id") or None
    
    user_id = body.get("user_id") or "web_user"
    latest_message = messages[-1]["content"]

    if IS_AGENT_LOCAL is True or IS_AGENT_LOCAL == "True":
        agent_response = local_agent.run(user_id,session_id,latest_message)
    else:
        agent_response = await agent_engine_agent.run(user_id,session_id,latest_message)


    if agent_response and agent_response.get('response'):
         agent_response['products'] = _extract_product_mentions(agent_response.get('response'))
    
    return agent_response
        
    
# ----------------------------------------------------- #
# Mount the UI
# ----------------------------------------------------- # 
# 2. Mount the Next.js 'out' directory
app.mount("/", StaticFiles(directory="out", html=True), name="ui")

# 3. Handle Client-Side Routing
# If user refreshes and puts in an arbitrary path, this catch-all route sends them back to index.html so Next.js can handle it.
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    """Handles 404 Not Found exceptions by serving the index.html file.

    :param request: The FastAPI request object.
    :type request: Request
    :param exc: The exception object.
    :type exc: Exception
    :return: The index.html file.
    :rtype: FileResponse
    """
    return FileResponse("out/index.html")
