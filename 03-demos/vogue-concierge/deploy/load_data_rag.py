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

import json
import os
import time

import vertexai
from vertexai import rag
from google.cloud.aiplatform_v1.types import ImportRagFilesResponse

from google.cloud import storage
from yaml_parser import YAMLParser


#------------------------------------------------------------------------------------#
# Create RAG Corpus
#------------------------------------------------------------------------------------#
def create_corpus(
    project_id: str, rag_region: str, rag_corpus_name: str, rag_corpus_desc: str
) -> rag.RagCorpus:
    """Creates a RAG corpus if it doesn't already exist.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param rag_region: The region for the RAG corpus.
    :type rag_region: str
    :param rag_corpus_name: The name of the RAG corpus.
    :type rag_corpus_name: str
    :param rag_corpus_desc: The description of the RAG corpus.
    :type rag_corpus_desc: str
    :return: The RAG corpus object.
    :rtype: rag.RagCorpus
    """
    try:
        vertexai.init(project=project_id, location=rag_region)
        existing = rag.list_corpora()
        for corpus in existing:
            if corpus.display_name == rag_corpus_name:
                print(f"Corpus '{rag_corpus_name}' already exists: {corpus.name}")
                return corpus
        

        # Create new corpus
        corpus = rag.create_corpus(
            display_name=rag_corpus_name,
            description=rag_corpus_desc,
        )
        print(f"Created corpus: {corpus.name}")
        return corpus
    except Exception as e:
        print(f"Error in creating RAG Corpus - {e}")
        return None

#------------------------------------------------------------------------------------#
# Prepare Catalog for Rag and upload it to GCS
#------------------------------------------------------------------------------------#
def upload_catalog_for_rag(
    local_data_folder: str,
    local_catalog_file: str,
    local_catalog_file_for_rag: str,
    storage_rag_folder: str,
    storage_catalog_file_for_rag: str,
    storage_bucket_name: str,
    bucket: storage.Bucket,
) -> str:
    """Prepares the catalog for RAG and uploads it to GCS.

    :param local_data_folder: The local folder where the data is stored.
    :type local_data_folder: str
    :param local_catalog_file: The name of the local catalog file.
    :type local_catalog_file: str
    :param local_catalog_file_for_rag: The name of the local catalog file for RAG.
    :type local_catalog_file_for_rag: str
    :param storage_rag_folder: The folder in the storage bucket where the RAG data is stored.
    :type storage_rag_folder: str
    :param storage_catalog_file_for_rag: The name of the catalog file for RAG in the storage bucket.
    :type storage_catalog_file_for_rag: str
    :param storage_bucket_name: The name of the storage bucket.
    :type storage_bucket_name: str
    :param bucket: The storage bucket object.
    :type bucket: storage.Bucket
    :return: The GCS URI of the uploaded file.
    :rtype: str
    """
    CATALOG_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{local_data_folder}/{local_catalog_file}"
    
    with open(CATALOG_PATH, "r") as f:
        catalog = json.load(f)

    lines = []
    lines.append("# Vogue Concierge — Product Catalog\n")
    lines.append(f"Total products: {len(catalog)}\n\n")

    for product in catalog:
        lines.append(f"## {product['name']} ({product['sku']})")
        lines.append(f"Price: ${product['price']:.2f}")
        lines.append(f"Category: {product['category']}")
        lines.append(f"Color: {product.get('color', 'N/A')}")
        lines.append(f"Material: {product.get('material', 'N/A')}")
        lines.append(f"Sizes: {', '.join(product.get('sizes', []))}")
        lines.append(f"Occasions: {', '.join(product.get('occasions', []))}")
        lines.append(f"Description: {product['description']}")
        if product.get("image_url"):
            lines.append(f"Image: {product['image_url']}")
        lines.append("")  # blank line between products

    CATALOG_RAG_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{local_data_folder}/{local_catalog_file_for_rag}"

    with open(CATALOG_RAG_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"Prepared catalog text file: {CATALOG_RAG_PATH} ({len(catalog)} products)")

    remote_filename = f"{storage_rag_folder}/{storage_catalog_file_for_rag}"
    blob = bucket.blob(remote_filename)
    blob.upload_from_filename(CATALOG_RAG_PATH, content_type="text/markdown")
    remote_filename = f"gs://{storage_bucket_name}/{remote_filename}"
    print(f"Uploaded catalog text to {remote_filename}")
    return remote_filename

#------------------------------------------------------------------------------------#
# Prepare Trend report for Rag and upload it to GCS
#------------------------------------------------------------------------------------#
def upload_trend_report_for_rag(
    local_data_folder: str,
    local_trend_report_file: str,
    storage_rag_folder: str,
    storage_trend_report_file: str,
    storage_bucket_name: str,
    bucket: storage.Bucket,
) -> str:
    """Prepares the trend report for RAG and uploads it to GCS.

    :param local_data_folder: The local folder where the data is stored.
    :type local_data_folder: str
    :param local_trend_report_file: The name of the local trend report file.
    :type local_trend_report_file: str
    :param storage_rag_folder: The folder in the storage bucket where the RAG data is stored.
    :type storage_rag_folder: str
    :param storage_trend_report_file: The name of the trend report file in the storage bucket.
    :type storage_trend_report_file: str
    :param storage_bucket_name: The name of the storage bucket.
    :type storage_bucket_name: str
    :param bucket: The storage bucket object.
    :type bucket: storage.Bucket
    :return: The GCS URI of the uploaded file.
    :rtype: str
    """
    TREND_REPORT_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{local_data_folder}/{local_trend_report_file}"
    remote_filename = f"{storage_rag_folder}/{storage_trend_report_file}"
    blob = bucket.blob(remote_filename)
    blob.upload_from_filename(TREND_REPORT_PATH, content_type="text/markdown")
    remote_filename = f"gs://{storage_bucket_name}/{remote_filename}"
    print(f"Uploaded trend report to {remote_filename}")
    return remote_filename

#------------------------------------------------------------------------------------#
# Injest files
#------------------------------------------------------------------------------------#
def ingest_files(
    project_id: str,
    storage_bucket_name: str,
    local_data_folder: str,
    local_catalog_file: str,
    local_catalog_file_for_rag: str,
    storage_rag_folder: str,
    storage_catalog_file_for_rag: str,
    local_trend_report_file: str,
    storage_trend_report_file: str,
    corpus: rag.RagCorpus,
) -> ImportRagFilesResponse:
    """Ingests the files into the RAG corpus.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param storage_bucket_name: The name of the storage bucket.
    :type storage_bucket_name: str
    :param local_data_folder: The local folder where the data is stored.
    :type local_data_folder: str
    :param local_catalog_file: The name of the local catalog file.
    :type local_catalog_file: str
    :param local_catalog_file_for_rag: The name of the local catalog file for RAG.
    :type local_catalog_file_for_rag: str
    :param storage_rag_folder: The folder in the storage bucket where the RAG data is stored.
    :type storage_rag_folder: str
    :param storage_catalog_file_for_rag: The name of the catalog file for RAG in the storage bucket.
    :type storage_catalog_file_for_rag: str
    :param local_trend_report_file: The name of the local trend report file.
    :type local_trend_report_file: str
    :param storage_trend_report_file: The name of the trend report file in the storage bucket.
    :type storage_trend_report_file: str
    :param corpus: The RAG corpus object.
    :type corpus: rag.RagCorpus
    :return: The response from the RAG import files API.
    :rtype: ImportRagFilesResponse
    """
    try:
        client = storage.Client(project=project_id)
        bucket = client.bucket(storage_bucket_name)

        gcs_rag_uris = []

        gcs_rag_uris.append(
            upload_catalog_for_rag(
                local_data_folder=local_data_folder,
                local_catalog_file=local_catalog_file,
                local_catalog_file_for_rag=local_catalog_file_for_rag,
                storage_rag_folder=storage_rag_folder,
                storage_catalog_file_for_rag=storage_catalog_file_for_rag,
                storage_bucket_name=storage_bucket_name,
                bucket=bucket,
            )
        )
        gcs_rag_uris.append(
            upload_trend_report_for_rag(
                local_data_folder=local_data_folder,
                local_trend_report_file=local_trend_report_file,
                storage_rag_folder=storage_rag_folder,
                storage_trend_report_file=storage_trend_report_file,
                storage_bucket_name=storage_bucket_name,
                bucket=bucket,
            )
        )

        response = rag.import_files(
            corpus_name=corpus.name,
            paths=gcs_rag_uris,
            transformation_config=rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(
                    chunk_size=512,
                    chunk_overlap=100,
                ),
            ),
        )

        print(f"RAG ingestion complete: {response.imported_rag_files_count} files imported")
        return response
    except Exception as e:
        print(f"Error in RAG ingestion - {e} ")
        return None

#------------------------------------------------------------------------------------#
# Test RAG with a simple query
#------------------------------------------------------------------------------------#
def test_rag_query(corpus:rag.RagCorpus) -> None:
    """Tests the RAG corpus with a simple query.

    :param corpus: The RAG corpus object.
    :type corpus: rag.RagCorpus
    """
    
    try:
        query_text = "summer wedding dress"
        
        print("\nTesting RAG query: '{query_text}'")

        rag_retrieval_config = rag.RagRetrievalConfig(
            top_k=3,
            filter=rag.Filter(vector_distance_threshold=0.5),
        )
        
        response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=corpus.name,
                )
            ],
            text=query_text,
            rag_retrieval_config=rag_retrieval_config,
    )

        if response and response.contexts and response.contexts.contexts:
            for i, ctx in enumerate(response.contexts.contexts):
                print(f"  Result {i+1} (score: {ctx.score:.3f}): {ctx.text[:100]}...")
        else:
            print("  No results — corpus may still be indexing. Try again in a few minutes.")
    except Exception as e:
        print("Error while testing Rag Query - {e}")

#------------------------------------------------------------------------------------#
# Load data
#------------------------------------------------------------------------------------#
def load(
    project_id: str,
    agent_ds_rag_region: str,
    agent_ds_rag_corpus_name: str,
    agent_ds_rag_corpus_desc: str,
    agent_ds_storage_bucket_name: str,
    local_data_folder: str,
    local_catalog_file: str,
    local_catalog_file_for_rag: str,
    agent_ds_storage_rag_folder: str,
    agent_ds_storage_catalog_file_for_rag: str,
    local_trend_report_file: str,
    agent_ds_storage_trend_report_file: str,
) -> None:
    """Loads the data for the RAG demo.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param agent_ds_rag_region: The region for the RAG corpus.
    :type agent_ds_rag_region: str
    :param agent_ds_rag_corpus_name: The name of the RAG corpus.
    :type agent_ds_rag_corpus_name: str
    :param agent_ds_rag_corpus_desc: The description of the RAG corpus.
    :type agent_ds_rag_corpus_desc: str
    :param agent_ds_storage_bucket_name: The name of the storage bucket.
    :type agent_ds_storage_bucket_name: str
    :param local_data_folder: The local folder where the data is stored.
    :type local_data_folder: str
    :param local_catalog_file: The name of the local catalog file.
    :type local_catalog_file: str
    :param local_catalog_file_for_rag: The name of the local catalog file for RAG.
    :type local_catalog_file_for_rag: str
    :param agent_ds_storage_rag_folder: The folder in the storage bucket where the RAG data is stored.
    :type agent_ds_storage_rag_folder: str
    :param agent_ds_storage_catalog_file_for_rag: The name of the catalog file for RAG in the storage bucket.
    :type agent_ds_storage_catalog_file_for_rag: str
    :param local_trend_report_file: The name of the local trend report file.
    :type local_trend_report_file: str
    :param agent_ds_storage_trend_report_file: The name of the trend report file in the storage bucket.
    :type agent_ds_storage_trend_report_file: str
    """


    print("=" * 60)
    print("Vogue Concierge — RAG Setup")
    print("=" * 60)

     # Create corpus
    print("\nStep 1: Creating RAG corpus...")
    corpus:rag.Corpus = create_corpus(
        project_id=project_id,
        rag_region=agent_ds_rag_region,
        rag_corpus_name=agent_ds_rag_corpus_name,
        rag_corpus_desc=agent_ds_rag_corpus_desc,
    )

    if not corpus:
        print("Unable to proceed without a RAG corpus")
        return
    
    # Ingest files
    print("\nStep 2: Ingesting files...")
    ingest_response = ingest_files(
        project_id=project_id,
        storage_bucket_name=agent_ds_storage_bucket_name,
        local_data_folder=local_data_folder,
        local_catalog_file=local_catalog_file,
        local_catalog_file_for_rag=local_catalog_file_for_rag,
        storage_rag_folder=agent_ds_storage_rag_folder,
        storage_catalog_file_for_rag=agent_ds_storage_catalog_file_for_rag,
        local_trend_report_file=local_trend_report_file,
        storage_trend_report_file=agent_ds_storage_trend_report_file,
        corpus=corpus,
    )

    if not ingest_response:
        print("Unable to proceed without ingesting data in to the RAG corpus")
        return
    


    # Wait a moment for indexing
    print("\nWaiting 30 seconds for indexing...")
    time.sleep(30)

    # Test
    print("\nStep 3: Testing RAG query...")
    test_rag_query(corpus)

    print(f"\n{'=' * 60}")
    print("RAG setup complete!")
    print(f"  Corpus: {corpus.name}")
    print(f"  Region: {agent_ds_rag_region}")
    print(f"  Files: catalog.md, trend_report.md")
    print(f"{'=' * 60}")