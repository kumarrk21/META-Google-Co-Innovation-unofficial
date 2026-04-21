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
def create_bucket(
    project_id: str, bucket_name: str, bucket_location: str
) -> storage.Bucket:
    """Creates a Google Cloud Storage bucket if it doesn't already exist.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param bucket_name: The name of the bucket to create.
    :type bucket_name: str
    :param bucket_location: The location of the bucket.
    :type bucket_location: str
    :return: The bucket object.
    :rtype: storage.Bucket
    """
    client = storage.Client(project=project_id)

    try:
        bucket = client.get_bucket(bucket_name)
        print(f"Bucket {bucket_name} already exists")
    except Exception:
        bucket = client.create_bucket(bucket_name, location=bucket_location)
        print(f"Created bucket: {bucket_location}")

    return bucket

#------------------------------------------------------------------------------------#
# Generate image using imagen
#------------------------------------------------------------------------------------#
def generate_image(
    project_id: str, imagegen_region: str, imagegen_model_id: str, prompt: str
) -> GeneratedImage | None:
    """Generates an image using Imagen.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param imagegen_region: The region for the Imagen model.
    :type imagegen_region: str
    :param imagegen_model_id: The ID of the Imagen model.
    :type imagegen_model_id: str
    :param prompt: The prompt for generating the image.
    :type prompt: str
    :return: The generated image object or None if generation failed.
    :rtype: GeneratedImage | None
    """
    genai_client = genai.Client(vertexai=True, project=project_id, location=imagegen_region)

    try:
        images = genai_client.models.generate_images(
            model=imagegen_model_id,
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
def generate_and_upload_images(
    project_id: str,
    imagegen_region: str,
    imagegen_model_id: str,
    imagegen_use: str,
    local_data_folder: str,
    local_image_folder: str,
    storage_bucket_name: str,
    storage_image_folder: str,
    catalog: list,
) -> List:
    """Generates and uploads images for the products in the catalog.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param imagegen_region: The region for the Imagen model.
    :type imagegen_region: str
    :param imagegen_model_id: The ID of the Imagen model.
    :type imagegen_model_id: str
    :param imagegen_use: Whether to use Imagen to generate images.
    :type imagegen_use: str
    :param local_data_folder: The local folder where the data is stored.
    :type local_data_folder: str
    :param local_image_folder: The local folder where the images are stored.
    :type local_image_folder: str
    :param storage_bucket_name: The name of the storage bucket.
    :type storage_bucket_name: str
    :param storage_image_folder: The folder in the storage bucket where the images are stored.
    :type storage_image_folder: str
    :param catalog: A list of products in the catalog.
    :type catalog: list
    :return: The updated catalog with the image URLs.
    :rtype: List
    """
    
    
    LOCAL_IMAGE_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{local_data_folder}/{local_image_folder}"

    storage_client = storage.Client(client_options={"api_endpoint": "https://storage.googleapis.com"})
    bucket = storage_client.bucket(storage_bucket_name)

    updated_catalog = []
    for i, product in enumerate(catalog):
        sku = product["sku"]
        image_filename = f"{sku.lower().replace('-', '_')}.png"
        remote_image_filename = f"{storage_image_folder}/{sku.lower().replace('-', '_')}.png"
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
                    
            elif imagegen_use == "TRUE":
                print(f"  [{i+1}/30] Generating image for {sku}: {product['name']}")
                image = generate_image(project_id, imagegen_region, imagegen_model_id, product["image_prompt"])

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
def upload_data_files(
    project_id: str,
    local_data_folder: str,
    local_trend_report_file: str,
    storage_bucket_name: str,
    storage_data_folder: str,
    storage_product_data_file: str,
    catalog: list,
) -> None:
    """Uploads the data files to Google Cloud Storage.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param local_data_folder: The local folder where the data is stored.
    :type local_data_folder: str
    :param local_trend_report_file: The name of the local trend report file.
    :type local_trend_report_file: str
    :param storage_bucket_name: The name of the storage bucket.
    :type storage_bucket_name: str
    :param storage_data_folder: The folder in the storage bucket where the data is stored.
    :type storage_data_folder: str
    :param storage_product_data_file: The name of the product data file in the storage bucket.
    :type storage_product_data_file: str
    :param catalog: A list of products in the catalog.
    :type catalog: list
    """
    
    TREND_REPORT_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{local_data_folder}/{local_trend_report_file}"

    client = storage.Client(project=project_id)
    bucket = client.bucket(storage_bucket_name)

    # Upload products.json
    blob = bucket.blob(f"{storage_data_folder}/{storage_product_data_file}")
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
def load(
    project_id: str,
    agent_ds_storage_bucket_name: str,
    agent_ds_storage_bucket_loc: str,
    agent_ds_imagegen_region: str,
    agent_ds_imagegen_model_id: str,
    agent_ds_imagegen_use: str,
    local_data_folder: str,
    local_image_folder: str,
    local_catalog_file: str,
    local_trend_report_file: str,
    agent_ds_storage_image_folder: str,
    agent_ds_storage_data_folder: str,
    agent_ds_storage_product_data_file: str,
) -> None:
    """Loads the catalog and images for the demo.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param agent_ds_storage_bucket_name: The name of the storage bucket.
    :type agent_ds_storage_bucket_name: str
    :param agent_ds_storage_bucket_loc: The location of the storage bucket.
    :type agent_ds_storage_bucket_loc: str
    :param agent_ds_imagegen_region: The region for the Imagen model.
    :type agent_ds_imagegen_region: str
    :param agent_ds_imagegen_model_id: The ID of the Imagen model.
    :type agent_ds_imagegen_model_id: str
    :param agent_ds_imagegen_use: Whether to use Imagen to generate images.
    :type agent_ds_imagegen_use: str
    :param local_data_folder: The local folder where the data is stored.
    :type local_data_folder: str
    :param local_image_folder: The local folder where the images are stored.
    :type local_image_folder: str
    :param local_catalog_file: The name of the local catalog file.
    :type local_catalog_file: str
    :param local_trend_report_file: The name of the local trend report file.
    :type local_trend_report_file: str
    :param agent_ds_storage_image_folder: The folder in the storage bucket where the images are stored.
    :type agent_ds_storage_image_folder: str
    :param agent_ds_storage_data_folder: The folder in the storage bucket where the data is stored.
    :type agent_ds_storage_data_folder: str
    :param agent_ds_storage_product_data_file: The name of the product data file in the storage bucket.
    :type agent_ds_storage_product_data_file: str
    """

    CATALOG_FILE = os.path.dirname(os.path.realpath(__file__)) + f"/{local_data_folder}/{local_catalog_file}"
    
    print("=" * 60)
    print("Vogue Concierge — Catalog & Image Setup")
    print("=" * 60)

    # Load catalog
    with open(CATALOG_FILE, "r") as f:
        catalog = json.load(f)
    print(f"Loaded {len(catalog)} products\n")

    # Create bucket
    print("Step 1: Creating GCS bucket...")
    create_bucket(
        project_id=project_id,
        bucket_name=agent_ds_storage_bucket_name,
        bucket_location=agent_ds_storage_bucket_loc,
    )

    # Generate images
    print(f"\nStep 2: Generating {len(catalog)} product images with Imagen 3...")
    updated_catalog = generate_and_upload_images(
        project_id=project_id,
        imagegen_region=agent_ds_imagegen_region,
        imagegen_model_id=agent_ds_imagegen_model_id,
        imagegen_use=agent_ds_imagegen_use,
        local_data_folder=local_data_folder,
        local_image_folder=local_image_folder,
        storage_bucket_name=agent_ds_storage_bucket_name,
        storage_image_folder=agent_ds_storage_image_folder,
        catalog=catalog,
    )

    # Save updated catalog locally
    print("\nStep 3: Saving updated catalog with image URLs...")
    with open(CATALOG_FILE, "w") as f:
        json.dump(updated_catalog, f, indent=2)
    print(f"Updated {CATALOG_FILE}")

    # Upload data files to GCS
    print("\nStep 4: Uploading data files to GCS...")
    upload_data_files(
        project_id=project_id,
        local_data_folder=local_data_folder,
        local_trend_report_file=local_trend_report_file,
        storage_bucket_name=agent_ds_storage_bucket_name,
        storage_data_folder=agent_ds_storage_data_folder,
        storage_product_data_file=agent_ds_storage_product_data_file,
        catalog=updated_catalog,
    )

    # Summary
    success_count = sum(1 for p in updated_catalog if p.get("image_url"))
    print(f"\n{'=' * 60}")
    print(f"Catalog setup complete!")
    print(f"  Bucket: gs://{agent_ds_storage_bucket_name}")
    print(f"  Images: {success_count}/{len(updated_catalog)} generated")
    print(f"{'=' * 60}")
