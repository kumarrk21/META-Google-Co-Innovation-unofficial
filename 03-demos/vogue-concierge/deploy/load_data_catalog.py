from ast import List
import json
import os
import time

from google.cloud import storage
from google import genai
from google.genai.types import GenerateImagesConfig
from google.genai.types import GeneratedImage

from yaml_parser import YAMLParser


#------------------------------------------------------------------------------------#
# Create the bucket and set IAM policies
#------------------------------------------------------------------------------------#
def create_bucket(parser:YAMLParser) -> storage.Bucket:
    client = storage.Client(project=parser.PROJECT_ID)

    try:
        bucket = client.get_bucket(parser.AGENT_DS_STORAGE_BUCKET_NAME)
        print(f"Bucket {parser.AGENT_DS_STORAGE_BUCKET_NAME} already exists")
    except Exception:
        bucket = client.create_bucket(parser.AGENT_DS_STORAGE_BUCKET_NAME, location=parser.AGENT_DS_STORAGE_BUCKET_LOC)
        print(f"Created bucket: {parser.AGENT_DS_STORAGE_BUCKET_LOC}")

    return bucket

#------------------------------------------------------------------------------------#
# Generate image using imagen
#------------------------------------------------------------------------------------#
def generate_image(parser:YAMLParser, prompt:str) -> GeneratedImage | None :
    genai_client = genai.Client(vertexai=True, project=parser.PROJECT_ID, location=parser.AGENT_DS_IMAGEGEN_REGION)

    try:
        images = genai_client.models.generate_images(
            model = parser.AGENT_DS_IMAGEGEN_MODEL_ID,
            prompt=prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="3:4",
                safety_filter_level="BLOCK_ONLY_HIGH",
                person_generation="ALLOW_ADULT",
                include_rai_reason=True
            )
        )

        for idx, result in enumerate(images.generated_images):
            if (result.image and result.image.image_bytes!=None):
                print(f"  Image generated successfully")
                return result.image
            else:
                reason = result.rai_filtered_reason
                print(f"  Image not generated. Reason: {reason}")
                return None
            
    except Exception as e:
        print(f"  Image not generated. Reason: {e}")
        return None
        

#------------------------------------------------------------------------------------#
# Generate and upload images
#------------------------------------------------------------------------------------#
def generate_and_upload_images(parser:YAMLParser, catalog: list) -> List:
    
    
    LOCAL_IMAGE_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{parser.LOCAL_DATA_FOLDER}/{parser.LOCAL_IMAGE_FOLDER}"

    storage_client = storage.Client(client_options={"api_endpoint": "https://storage.googleapis.com"})
    bucket = storage_client.bucket(parser.AGENT_DS_STORAGE_BUCKET_NAME)

    updated_catalog = []
    for i, product in enumerate(catalog):
        sku = product["sku"]
        image_filename = f"{sku.lower().replace('-', '_')}.png"
        remote_image_filename = f"{parser.AGENT_DS_STORAGE_IMAGE_FOLDER}/{sku.lower().replace('-', '_')}.png"
        product["image_url"] = remote_image_filename

        # Check if image already exists
        blob = bucket.blob(remote_image_filename)
        try:
            blob.reload()
            print(f"  [{i+1}/30] {sku} — image exists, skipping")
        except:
            local_image_filename = f"{LOCAL_IMAGE_PATH}/{image_filename}"
            if os.path.exists(local_image_filename):
                print(f"           Image exists locally, uploading the local copy")
                try:
                    blob.upload_from_filename(local_image_filename, content_type="image/png")
                    print(f"           Uploaded to {remote_image_filename}")
                except Exception as e:
                    product["image_url"] = ""
                    print(f"           Error uploading image {e}")
                    
            elif parser.AGENT_DS_IMAGEGEN_USE == "TRUE":
                print(f"  [{i+1}/30] Generating image for {sku}: {product['name']}")
                image = generate_image(parser, product["image_prompt"])

                if image != None:
                    image.save(local_image_filename)
                    try:
                        blob.upload_from_filename(local_image_filename, content_type="image/png")
                        print(f"           Uploaded to {remote_image_filename}")
                    except Exception as e:
                        product["image_url"] = ""
                        print(f"           Error uploading image {e}")   
                else:
                    print(f"           Unable to generate image")   
                    product["image_url"] = ""

                # Rate limiting — be kind to the API
                if (i + 1) % 5 == 0:
                    print(f"           Pausing 10s after {i+1} images...")
                    time.sleep(10)
                else:
                    time.sleep(2)

        updated_catalog.append(product)

    return updated_catalog

#------------------------------------------------------------------------------------#
# Load trend report to GCS
#------------------------------------------------------------------------------------#
def upload_data_files(parser:YAMLParser , catalog: list) -> None:
    
    TREND_REPORT_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{parser.LOCAL_DATA_FOLDER}/{parser.LOCAL_TREND_REPORT_FILE}"

    client = storage.Client(project=parser.PROJECT_ID)
    bucket = client.bucket(parser.AGENT_DS_STORAGE_BUCKET_NAME)

    # Upload products.json
    blob = bucket.blob(f"{parser.AGENT_DS_STORAGE_DATA_FOLDER}/{parser.AGENT_DS_STORAGE_PRODUCT_DATA_FILE}")
    blob.upload_from_string(json.dumps(catalog, indent=2), content_type="application/json")
    print(f"Uploaded data/products.json to GCS")

    # Upload trend report
    if os.path.exists(TREND_REPORT_PATH):
        blob = bucket.blob(TREND_REPORT_PATH)
        blob.upload_from_filename(TREND_REPORT_PATH, content_type="text/markdown")
        print(f"Uploaded data/trend_report.md to GCS")
    else:
        print("No trend report found")


#------------------------------------------------------------------------------------#
# Load Data
#------------------------------------------------------------------------------------#
def load(parser: YAMLParser) -> None:

    CATALOG_FILE = os.path.dirname(os.path.realpath(__file__)) + f"/{parser.LOCAL_DATA_FOLDER}/{parser.LOCAL_CATALOG_FILE}"
    
    print("=" * 60)
    print("Vogue Concierge — Catalog & Image Setup")
    print("=" * 60)

    # Load catalog
    with open(CATALOG_FILE, "r") as f:
        catalog = json.load(f)
    print(f"Loaded {len(catalog)} products\n")

    # Create bucket
    print("Step 1: Creating GCS bucket...")
    create_bucket(parser)

    # Generate images
    print(f"\nStep 2: Generating {len(catalog)} product images with Imagen 3...")
    updated_catalog = generate_and_upload_images(parser, catalog)

    # Save updated catalog locally
    print("\nStep 3: Saving updated catalog with image URLs...")
    with open(CATALOG_FILE, "w") as f:
        json.dump(updated_catalog, f, indent=2)
    print(f"Updated {CATALOG_FILE}")

    # Upload data files to GCS
    print("\nStep 4: Uploading data files to GCS...")
    upload_data_files(parser, updated_catalog)

    # Summary
    success_count = sum(1 for p in updated_catalog if p.get("image_url"))
    print(f"\n{'=' * 60}")
    print(f"Catalog setup complete!")
    print(f"  Bucket: gs://{parser.AGENT_DS_STORAGE_BUCKET_NAME}")
    print(f"  Images: {success_count}/{len(updated_catalog)} generated")
    print(f"{'=' * 60}")
