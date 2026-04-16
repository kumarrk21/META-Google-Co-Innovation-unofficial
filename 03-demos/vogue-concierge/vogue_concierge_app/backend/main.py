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
# ----------------------------------------------------- #
# Run the agent
# ----------------------------------------------------- # 
load_dotenv()
app = FastAPI()

is_agent_local = os.getenv("LOCAL_AGENT", False)


PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
BUCKET_NAME = os.getenv("BUCKET_NAME")
IMAGE_FOLDER = os.getenv("IMAGE_FOLDER")
DATA_FOLDER = os.getenv("DATA_FOLDER")
PRODUCT_DATA_FILE = os.getenv("PRODUCT_DATA_FILE")
CLOUD_RUN_SA = os.getenv("CLOUD_RUN_SA")

# ----------------------------------------------------- #
# Load Product data from GCS
# TODO: Move this to BQ later
# ----------------------------------------------------- # 
def _get_catalog_data():
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"{DATA_FOLDER}/{PRODUCT_DATA_FILE}")
        data = blob.download_as_text()
        return json.loads(data)
        
    except Exception as e:
        print(f"Error loading catalog from GCS bucket: {e}")
        return None

# ----------------------------------------------------- #
# Get Signed URL with impersonation
# ----------------------------------------------------- # 
def _get_signed_url_with_impersonation(product: dict) -> dict:
    updated_product = product
    try:
        target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        adc_creds, project_id = default(scopes=target_scopes)
        impersonated_creds = impersonated_credentials.Credentials(
            source_credentials=adc_creds,
            target_principal=CLOUD_RUN_SA,
            target_scopes=target_scopes,
        )
        storage_client = storage.Client(credentials=impersonated_creds, project=PROJECT_ID)
        
        bucket = storage_client.bucket(BUCKET_NAME)    
        blob = bucket.blob(product['image_url'])

        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="GET",
            service_account_email=CLOUD_RUN_SA
        )
        updated_product['image_url'] = url

    except Exception as e:
        print(f"Error getting signed url with impersonation: {e}")    
    
    return updated_product

# ----------------------------------------------------- #
# Get Signed URL without impersonation
# ----------------------------------------------------- # 
def _get_signed_url_without_impersonation(product: dict) -> dict:
    updated_product = product
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)    
        blob = bucket.blob(product['image_url'])

        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="GET",
        )
        updated_product['image_url'] = url
    except Exception as e:
        print(f"Error getting signed url without impersonation: {e}")    
    
    return updated_product

# ----------------------------------------------------- #
# Get Signed URL
# ----------------------------------------------------- # 
def _get_signed_url_for_image(product: dict) -> dict:
    
    # updated_product = product
    # credentials, project_id = google.auth.default()
    # if hasattr(credentials, 'service_account_email'):
    #    print("Credentials has service account")
    #    updated_product = _get_signed_url_without_impersonation(product)
    # else:
    #    print("Credentials doesn't have a service account")
    #    updated_product = _get_signed_url_with_impersonation(product)
       
    updated_product = _get_signed_url_with_impersonation(product)
    
    return updated_product
        

# ----------------------------------------------------- #
# Extract product details
# ----------------------------------------------------- # 
def _extract_product_mentions(text: str) -> list:
    catalog = _get_catalog_data()
    mentioned = []
    
    sku_pattern = re.compile(r"SKU-0*(\d{1,2})")
    matches = sku_pattern.findall(text)
    seen_skus = set()
    for match in matches:
        sku = f"SKU-{int(match):03d}"
        if sku not in seen_skus:
            product = next((p for p in catalog if p["sku"] == sku), None)
            if product:
                product = _get_signed_url_for_image(product)
                mentioned.append(product)
                seen_skus.add(sku)
    for product in catalog:
        if product["sku"] not in seen_skus:
            if product["name"].lower() in text.lower():
                product = _get_signed_url_for_image(product)
                mentioned.append(product)
                seen_skus.add(product["sku"])
    return mentioned[:6]


# API Routes (Define these BEFORE mounting the UI)
# ----------------------------------------------------- #
# Chat API
# ----------------------------------------------------- # 
@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    messages = body.get("messages",[])
    if not messages:
        raise HTTPException(status_code=400, detail="No messages or Agent Engine not connected")

    session_id = body.get("session_id") or None
    
    user_id = body.get("user_id") or "web_user"
    latest_message = messages[-1]["content"]

    if is_agent_local is True or is_agent_local == "True":
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
    return FileResponse("out/index.html")
