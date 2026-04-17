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
def create_corpus(parser: YAMLParser) -> rag.RagCorpus:
    try:
        vertexai.init(project=parser.PROJECT_ID, location=parser.AGENT_DS_RAG_REGION)
        existing = rag.list_corpora()
        for corpus in existing:
            if corpus.display_name == parser.AGENT_DS_RAG_CORPUS_NAME:
                print(f"Corpus '{parser.AGENT_DS_RAG_CORPUS_NAME}' already exists: {corpus.name}")
                return corpus
        

        # Create new corpus
        corpus = rag.create_corpus(
            display_name=parser.AGENT_DS_RAG_CORPUS_NAME,
            description=parser.AGENT_DS_RAG_CORPUS_DESC,
        )
        print(f"Created corpus: {corpus.name}")
        return corpus
    except Exception as e:
        print(f"Error in creating RAG Corpus - {e}")
        return None

#------------------------------------------------------------------------------------#
# Prepare Catalog for Rag and upload it to GCS
#------------------------------------------------------------------------------------#
def upload_catalog_for_rag(parser:YAMLParser, bucket: storage.Bucket) -> str:
    CATALOG_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{parser.LOCAL_DATA_FOLDER}/{parser.LOCAL_CATALOG_FILE}"
    
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

    CATALOG_RAG_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{parser.LOCAL_DATA_FOLDER}/{parser.LOCAL_CATALOG_FILE_FOR_RAG}"

    with open(CATALOG_RAG_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"Prepared catalog text file: {CATALOG_RAG_PATH} ({len(catalog)} products)")

    remote_filename = f"{parser.AGENT_DS_STORAGE_RAG_FOLDER}/{parser.AGENT_DS_STORAGE_CATALOG_FILE_FOR_RAG}"
    blob = bucket.blob(remote_filename)
    blob.upload_from_filename(CATALOG_RAG_PATH, content_type="text/markdown")
    remote_filename = f"gs://{parser.AGENT_DS_STORAGE_BUCKET_NAME}/{remote_filename}"
    print(f"Uploaded catalog text to {remote_filename}")
    return remote_filename

#------------------------------------------------------------------------------------#
# Prepare Trend report for Rag and upload it to GCS
#------------------------------------------------------------------------------------#
def upload_trend_report_for_rag(parser:YAMLParser, bucket:storage.Bucket) -> str:
    TREND_REPORT_PATH = os.path.dirname(os.path.realpath(__file__)) + f"/{parser.LOCAL_DATA_FOLDER}/{parser.LOCAL_TREND_REPORT_FILE}"
    remote_filename = f"{parser.AGENT_DS_STORAGE_RAG_FOLDER}/{parser.AGENT_DS_STORAGE_TREND_REPORT_FILE}"
    blob = bucket.blob(remote_filename)
    blob.upload_from_filename(TREND_REPORT_PATH, content_type="text/markdown")
    remote_filename = f"gs://{parser.AGENT_DS_STORAGE_BUCKET_NAME}/{remote_filename}"
    print(f"Uploaded trend report to {remote_filename}")
    return remote_filename

#------------------------------------------------------------------------------------#
# Injest files
#------------------------------------------------------------------------------------#
def ingest_files(parser: YAMLParser, corpus:rag.RagCorpus) -> ImportRagFilesResponse:
    try:
        client = storage.Client(project=parser.PROJECT_ID)
        bucket = client.bucket(parser.AGENT_DS_STORAGE_BUCKET_NAME)

        gcs_rag_uris = []

        gcs_rag_uris.append(upload_catalog_for_rag(parser, bucket))
        gcs_rag_uris.append(upload_trend_report_for_rag(parser, bucket))

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
def load(parser: YAMLParser) -> None:


    print("=" * 60)
    print("Vogue Concierge — RAG Setup")
    print("=" * 60)

     # Create corpus
    print("\nStep 1: Creating RAG corpus...")
    corpus:rag.Corpus = create_corpus(parser) 

    if not corpus:
        print("Unable to proceed without a RAG corpus")
        return
    
    # Ingest files
    print("\nStep 2: Ingesting files...")
    ingest_response = ingest_files(parser, corpus)

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
    print(f"  Region: {parser.AGENT_DS_RAG_REGION}")
    print(f"  Files: catalog.md, trend_report.md")
    print(f"{'=' * 60}")