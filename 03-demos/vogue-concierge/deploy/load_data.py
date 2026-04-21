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

from yaml_parser import YAMLParser
from . import load_data_bigquery, load_data_catalog, load_data_rag

#---------------------------------------------------#
# Load all data
#---------------------------------------------------#
def load(parser: YAMLParser) -> None:
    """Loads all the data for the demo.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """
    load_data_bigquery.load(
        project_id=parser.PROJECT_ID,
        dataset_id=parser.AGENT_DS_BQ_DATASET_ID,
        dataset_location=parser.AGENT_DS_DATASET_LOC,
        dataset_desc=parser.AGENT_DS_DATASET_DESC,
        inventory_table_name=parser.AGENT_DS_INVENTORY_TABLE_NAME,
        loyalty_table_name=parser.AGENT_DS_LOYALTY_TABLE_NAME,
        products_file_path=f"{parser.DEPLOY_FOLDER}/{parser.LOCAL_DATA_FOLDER}/{parser.LOCAL_CATALOG_FILE}",
    )
    load_data_catalog.load(
        project_id=parser.PROJECT_ID,
        agent_ds_storage_bucket_name=parser.AGENT_DS_STORAGE_BUCKET_NAME,
        agent_ds_storage_bucket_loc=parser.AGENT_DS_STORAGE_BUCKET_LOC,
        agent_ds_imagegen_region=parser.AGENT_DS_IMAGEGEN_REGION,
        agent_ds_imagegen_model_id=parser.AGENT_DS_IMAGEGEN_MODEL_ID,
        agent_ds_imagegen_use=parser.AGENT_DS_IMAGEGEN_USE,
        local_data_folder=f"{parser.DEPLOY_FOLDER}/{parser.LOCAL_DATA_FOLDER}",
        local_image_folder=parser.LOCAL_IMAGE_FOLDER,
        local_catalog_file=parser.LOCAL_CATALOG_FILE,
        local_trend_report_file=parser.LOCAL_TREND_REPORT_FILE,
        agent_ds_storage_image_folder=parser.AGENT_DS_STORAGE_IMAGE_FOLDER,
        agent_ds_storage_data_folder=parser.AGENT_DS_STORAGE_DATA_FOLDER,
        agent_ds_storage_product_data_file=parser.AGENT_DS_STORAGE_PRODUCT_DATA_FILE,
    )
    load_data_rag.load(
        project_id=parser.PROJECT_ID,
        agent_ds_rag_region=parser.AGENT_DS_RAG_REGION,
        agent_ds_rag_corpus_name=parser.AGENT_DS_RAG_CORPUS_NAME,
        agent_ds_rag_corpus_desc=parser.AGENT_DS_RAG_CORPUS_DESC,
        agent_ds_storage_bucket_name=parser.AGENT_DS_STORAGE_BUCKET_NAME,
        local_data_folder=f"{parser.DEPLOY_FOLDER}/{parser.LOCAL_DATA_FOLDER}",
        local_catalog_file=parser.LOCAL_CATALOG_FILE,
        local_catalog_file_for_rag=parser.LOCAL_CATALOG_FILE_FOR_RAG,
        agent_ds_storage_rag_folder=parser.AGENT_DS_STORAGE_RAG_FOLDER,
        agent_ds_storage_catalog_file_for_rag=parser.AGENT_DS_STORAGE_CATALOG_FILE_FOR_RAG,
        local_trend_report_file=parser.LOCAL_TREND_REPORT_FILE,
        agent_ds_storage_trend_report_file=parser.AGENT_DS_STORAGE_TREND_REPORT_FILE,
    )


