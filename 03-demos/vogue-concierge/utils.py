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
from pathlib import Path
from yaml_parser import YAMLParser
from lib import file_utils, shell_utils

SPA_BUILD_RESULTS_FILE = 'spa_build_result.txt'
APIS_ENABLE_RESULTS_FILE = 'apis_enable_result.txt'

#---------------------------------------------------#
# Initialize project
#---------------------------------------------------#
def init(parser: YAMLParser)-> None:
    """Initializes the project by creating necessary folders and files.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """
    # Create target folders if not available
    deploy_result_path = Path(parser.DEPLOY_RESULTS_FOLDER)
    deploy_result_path.mkdir(parents=True, exist_ok=True)

    # Build front end SPA and copy the out folder to backend
    build_next_spa(
        ui_folder=parser.UI_FOLDER,
        api_folder=parser.API_FOLDER,
        deploy_results_folder=parser.DEPLOY_RESULTS_FOLDER,
    )

    # Update Procfile for Honcho
    update_procfile(
        agent_port=parser.AGENT_LOCAL_PORT,
        api_port=parser.API_LOCAL_PORT,
        api_folder=parser.API_FOLDER,
    )

    # Update environment file for API
    api_env_vars = {
        "APP_NAME": parser.AGENT_FOLDER,
        "LOCAL_PORT": parser.AGENT_LOCAL_PORT,
        "GOOGLE_CLOUD_PROJECT": parser.PROJECT_ID,
        "GOOGLE_CLOUD_PROJECT_NUMBER": parser.PROJECT_NUMBER,
        "GOOGLE_CLOUD_LOCATION": parser.REGION,
        "AGENT_ENGINE_REGION": parser.AGENT_ENGINE_REGION,
        "AGENT_ENGINE_ID": parser.deployed_resources.get('agent_engine_id', ""),
        "BUCKET_NAME": parser.AGENT_DS_STORAGE_BUCKET_NAME,
        "IMAGE_FOLDER": parser.AGENT_DS_STORAGE_IMAGE_FOLDER,
        "DATA_FOLDER": parser.AGENT_DS_STORAGE_DATA_FOLDER,
        "PRODUCT_DATA_FILE": parser.AGENT_DS_STORAGE_PRODUCT_DATA_FILE,
        "CLOUD_RUN_SA": parser.CLOUD_RUN_SA,
    }
    write_api_env_file(
        api_folder=parser.API_FOLDER,
        env_vars=api_env_vars,
    )

    # Update environment file for Agent
    agent_env_vars = {
        "GOOGLE_GENAI_USE_VERTEXAI": parser.AGENT_USE_VERTEXAI,
        "GOOGLE_API_KEY": parser.AGENT_GOOGLE_API_KEY,
        "GOOGLE_CLOUD_PROJECT": parser.PROJECT_ID,
        "GOOGLE_CLOUD_PROJECT_NUMBER": parser.PROJECT_NUMBER,
        "GOOGLE_CLOUD_LOCATION": parser.REGION,
        "VERTEXAI_LOCATION": parser.VERTEXAI_REGION,
        "BQ_DATASET_ID": parser.AGENT_DS_BQ_DATASET_ID,
        "BQ_DATASET_LOCATION": parser.AGENT_DS_DATASET_LOC,
        "BQ_INVENTORY_TABLE": parser.AGENT_DS_INVENTORY_TABLE_NAME,
        "BQ_LOYALTY_TABLE": parser.AGENT_DS_LOYALTY_TABLE_NAME,
        "RAG_REGION": parser.AGENT_DS_RAG_REGION,
        "RAG_CORPUS_NAME": parser.AGENT_DS_RAG_CORPUS_NAME,
    }
    write_agent_env_file(
        agent_folder=parser.AGENT_FOLDER,
        env_vars=agent_env_vars,
    )

    # Enable required APIs
    enable_required_apis(
        project_id=parser.PROJECT_ID,
        required_apis=parser.required_apis,
        deploy_results_folder=parser.DEPLOY_RESULTS_FOLDER,
    )


#---------------------------------------------------#
# Deploy reuired APIs
#---------------------------------------------------#
def enable_required_apis(project_id: str, required_apis: list, deploy_results_folder: str) -> None:
    """Enables the required Google Cloud APIs for the project.

    :param project_id: The Google Cloud project ID.
    :type project_id: str
    :param required_apis: A list of the required Google Cloud APIs.
    :type required_apis: list
    :param deploy_results_folder: The folder where the deployment results are stored.
    :type deploy_results_folder: str
    """
    command = f"gcloud services enable {" ".join([f'{api}' for api in required_apis])} --project={project_id}"
    shell_utils.call_cli(command, f"{deploy_results_folder}/{APIS_ENABLE_RESULTS_FILE}", "Enabling required APIs" )


#---------------------------------------------------#
# Update environment file for API
#---------------------------------------------------#
def _write_env_file(env_file_path: str, env_vars: dict) -> None:
    """Writes a dictionary of environment variables to a file.

    :param env_file_path: The path to the .env file.
    :type env_file_path: str
    :param env_vars: A dictionary of environment variables.
    :type env_vars: dict
    """
    with open(env_file_path, 'w') as f:
        for key, value in env_vars.items():
            if value:
                f.write(f"{key}={value}\n")

#---------------------------------------------------#
# Update environment file for API
#---------------------------------------------------#
def write_api_env_file(api_folder: str, env_vars: dict) -> None:
    """Writes the environment variables for the API to a .env file.

    :param api_folder: The folder where the API code is located.
    :type api_folder: str
    :param env_vars: A dictionary of environment variables for the API.
    :type env_vars: dict
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    env_file = f"{dir_path}/{api_folder}/.env"
    _write_env_file(env_file, env_vars)

#---------------------------------------------------#
# Write environment files for agent deployment
#---------------------------------------------------#
def write_agent_env_file(agent_folder: str, env_vars: dict) -> None:
    """Writes the environment variables for the agent to a .env file.

    :param agent_folder: The folder where the agent code is located.
    :type agent_folder: str
    :param env_vars: A dictionary of environment variables for the agent.
    :type env_vars: dict
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    env_file = f"{dir_path}/{agent_folder}/.env"
    _write_env_file(env_file, env_vars)

#---------------------------------------------------#
# Update Procfile for Honcho
#---------------------------------------------------#
def update_procfile(agent_port: str, api_port: str, api_folder: str) -> None:
    """Updates the Procfile for Honcho.

    :param agent_port: The port for the agent.
    :type agent_port: str
    :param api_port: The port for the API.
    :type api_port: str
    :param api_folder: The folder where the API code is located.
    :type api_folder: str
    """
    content = f"""agent: adk api_server --port {agent_port}
api: cd {api_folder} && uvicorn main:app --reload --port {api_port}
"""

    file_utils.write_files_to_local("Procfile", content, "txt")


#---------------------------------------------------#
# Build UI Out folder
#---------------------------------------------------#
def build_next_spa(ui_folder: str, api_folder: str, deploy_results_folder: str) -> None:
    """Builds the Next.js single page application.

    :param ui_folder: The folder where the UI code is located.
    :type ui_folder: str
    :param api_folder: The folder where the API code is located.
    :type api_folder: str
    :param deploy_results_folder: The folder where the deployment results are stored.
    :type deploy_results_folder: str
    """
    command = f"""
        cd {ui_folder}
        npm install
        npx next build
        cp -R out/ ../../{api_folder}/out
    """

    shell_utils.call_cli(command, f"{deploy_results_folder}/{SPA_BUILD_RESULTS_FILE}", "Building SPA out folder" )


# ----------------------------------------------------- #
# Proxy CloudRun locally
# ----------------------------------------------------- #
def proxy_cloud_run_locally(parser: YAMLParser) -> None:
    """Establishes a proxy for the Cloud Run service locally.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """
    command = f"gcloud run services proxy {parser.API_NAME} --port={parser.API_LOCAL_PORT} --region {parser.CLOUDRUN_REGION}"
    shell_utils.call_cli(command,"","Establishing a proxy for cloud run locally", False)

# ----------------------------------------------------- #
# List deployed recsources
# ----------------------------------------------------- #
def list_deployed_resources(parser: YAMLParser) -> None:
    """Lists the deployed resources.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """
    print("---------------------------")
    print("***Deployed Resources*****")
    print("---------------------------")
    for key, value in parser.deployed_resources.items():
        print(f"{key} ====> {value}")
    print("---------------------------")

#---------------------------------------------------#
# Write  variable if available only
#---------------------------------------------------#
def write_variable(f,variable,value):
    """Writes a variable to a file if the value is not None.

    :param f: The file object.
    :param variable: The name of the variable.
    :type variable: str
    :param value: The value of the variable.
    """
    if value:
        f.write(f"{variable}={value}\n")