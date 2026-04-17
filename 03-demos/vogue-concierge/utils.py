import sys
import re
import subprocess
import os
from typing import Any, LiteralString
from numpy import full
import yaml
from pathlib import Path
from regex import P
from yaml_parser import YAMLParser

SPA_BUILD_RESULTS_FILE = 'spa_build_result.txt'
APIS_ENABLE_RESULTS_FILE = 'apis_enable_result.txt'

#---------------------------------------------------#
# Initialize project
#---------------------------------------------------#
def init(parser: YAMLParser)-> None:
    # Create target folders if not available
    deploy_result_path = Path(parser.DEPLOY_RESULTS_FOLDER)
    deploy_result_path.mkdir(parents=True, exist_ok=True)

    # Build front end SPA and copy the out folder to backend
    build_next_spa(parser=parser)

    # Update Procfile for Honcho
    update_procfile(parser=parser)

    # Update environment file for API
    write_api_env_file(parser=parser)

    # Update environment file for Agent
    write_agent_env_file(parser)

    # Enable required APIs
    enable_required_apis(parser)


#---------------------------------------------------#
# Deploy reuired APIs
#---------------------------------------------------#
def enable_required_apis(parser: YAMLParser) -> None:
    command = f"gcloud services enable {" ".join([f"{api}" for api in parser.required_apis])}"
    call_cli(command, f"{parser.DEPLOY_RESULTS_FOLDER}/{APIS_ENABLE_RESULTS_FILE}", "Enabling required APIs" )
    

#---------------------------------------------------#
# Update environment file for API
#---------------------------------------------------#
def write_api_env_file(parser: YAMLParser) -> None:
    # Write .env file for the API
    dir_path = os.path.dirname(os.path.realpath(__file__))
    env_file = f"{dir_path}/{parser.API_FOLDER}/.env"     
    ae_id = get_agent_engine_id(parser)
    
    with open(env_file, 'w') as f:
        write_variable(f,"APP_NAME",parser.AGENT_FOLDER)
        write_variable(f,"LOCAL_PORT",parser.AGENT_LOCAL_PORT)
        write_variable(f,"GOOGLE_CLOUD_PROJECT",parser.PROJECT_ID)
        write_variable(f,"GOOGLE_CLOUD_PROJECT_NUMBER",parser.PROJECT_NUMBER)
        write_variable(f,"GOOGLE_CLOUD_LOCATION",parser.REGION)
        write_variable(f,"AGENT_ENGINE_REGION",parser.AGENT_ENGINE_REGION)
        write_variable(f,"AGENT_ENGINE_ID",ae_id)
        write_variable(f,"BUCKET_NAME",parser.AGENT_DS_STORAGE_BUCKET_NAME)
        write_variable(f,"IMAGE_FOLDER",parser.AGENT_DS_STORAGE_IMAGE_FOLDER)
        write_variable(f,"DATA_FOLDER",parser.AGENT_DS_STORAGE_DATA_FOLDER)
        write_variable(f,"PRODUCT_DATA_FILE",parser.AGENT_DS_STORAGE_PRODUCT_DATA_FILE)
        write_variable(f,"CLOUD_RUN_SA",parser.CLOUD_RUN_SA)


#---------------------------------------------------#
# Update Procfile for Honcho
#---------------------------------------------------#
def update_procfile(parser: YAMLParser) -> None:
    agent_port = parser.AGENT_LOCAL_PORT
    api_port = parser.API_LOCAL_PORT
    api_folder = parser.API_FOLDER

    content = f"""agent: adk api_server --port {agent_port}
api: cd {api_folder} && uvicorn main:app --reload --port {api_port}
"""
    
    write_files_to_local("Procfile", content, "txt")


#---------------------------------------------------#
# Build UI Out folder
#---------------------------------------------------#
def build_next_spa(parser: YAMLParser) -> None:
    ui_folder = parser.UI_FOLDER
    api_folder = parser.API_FOLDER
    command = f"""
        cd {ui_folder}
        npm install
        npx next build
        cp -R out/ ../../{api_folder}/out
    """

    call_cli(command, f"{parser.DEPLOY_RESULTS_FOLDER}/{SPA_BUILD_RESULTS_FILE}", "Building SPA out folder" )

#---------------------------------------------------#
# Write environment files for agent deployment
#---------------------------------------------------#
def write_agent_env_file(parser: YAMLParser) -> None:

    # Write .env file for the agent
    dir_path = os.path.dirname(os.path.realpath(__file__))
    env_file = f"{dir_path}/{parser.AGENT_FOLDER}/.env" 

    with open(env_file, 'w') as f:
        write_variable(f,"GOOGLE_GENAI_USE_VERTEXAI",parser.AGENT_USE_VERTEXAI)
        write_variable(f,"GOOGLE_API_KEY",parser.AGENT_GOOGLE_API_KEY)
        write_variable(f,"GOOGLE_CLOUD_PROJECT",parser.PROJECT_ID)
        write_variable(f,"GOOGLE_CLOUD_PROJECT_NUMBER",parser.PROJECT_NUMBER)
        write_variable(f,"GOOGLE_CLOUD_LOCATION",parser.REGION)
        write_variable(f,"VERTEXAI_LOCATION",parser.VERTEXAI_REGION)

        write_variable(f,"BQ_DATASET_ID",parser.AGENT_DS_BQ_DATASET_ID)
        write_variable(f,"BQ_DATASET_LOCATION",parser.AGENT_DS_DATASET_LOC)
        write_variable(f,"BQ_INVENTORY_TABLE",parser.AGENT_DS_INVENTORY_TABLE_NAME)
        write_variable(f,"BQ_LOYALTY_TABLE",parser.AGENT_DS_LOYALTY_TABLE_NAME)
        
        write_variable(f,"RAG_REGION",parser.AGENT_DS_RAG_REGION)
        write_variable(f,"RAG_CORPUS_NAME",parser.AGENT_DS_RAG_CORPUS_NAME)

# ----------------------------------------------------- #
# Get Agent Engine ID
# ----------------------------------------------------- #
def get_agent_engine_id(parser: YAMLParser) -> str|None:
    ae_id = ""
    try:
        project_number = parser.PROJECT_NUMBER
        region = parser.AGENT_ENGINE_REGION
        deployment_result_file = f"{parser.DEPLOY_RESULTS_FOLDER}/{parser.AE_DEPLOY_RESULTS_FILE}"

        pattern = f"Created agent engine: projects/{project_number}/locations/{region}/reasoningEngines/"
        ae_id = get_data_from_output(deployment_result_file, pattern)
        if not ae_id:
            pattern = f"Updated agent engine: projects/{project_number}/locations/{region}/reasoningEngines/"
            ae_id = get_data_from_output(deployment_result_file, pattern)
        if not ae_id:
            return None
        ae_id = ae_id.replace(pattern, "")
        ae_id = ae_id.replace("')","")
    except Exception as e:
        print(f"Error while trying to get the agent ID {e}")
        ae_id = ""

    return ae_id

# ----------------------------------------------------- #
# Get CloudRun Url
# ----------------------------------------------------- #
def get_cloud_run_url(deployment_result_file:str) -> str|None:
    url = ""
    try:
        pattern = f"Service URL: "
        url = get_data_from_output(deployment_result_file, pattern)
        url = url.replace(pattern, "")
        url = url.replace("')","")
    except Exception as e:
        print(f"Error while trying to get the Cloud Run service url {e}")
        url = ""

    return url

# ----------------------------------------------------- #
# Proxy CloudRun locally
# ----------------------------------------------------- #
def proxy_cloud_run_locally(parser: YAMLParser) -> None:
    command = f"gcloud run services proxy {parser.API_NAME} --port={parser.API_LOCAL_PORT} --region {parser.CLOUDRUN_REGION}"
    call_cli(command,"","Establishing a proxy for cloud run locally", False)

# ----------------------------------------------------- #
# List deployed recsources
# ----------------------------------------------------- #
def list_deployed_resources(parser: YAMLParser) -> None:
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
    if value:
        f.write(f"{variable}={value}\n")

#---------------------------------------------------#
# Strip all unwanted ANSI codes
#---------------------------------------------------#
def strip_non_text_codes(text):
    ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_regex.sub('', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text.strip()


#---------------------------------------------------#
# Run CLI command live
#---------------------------------------------------#
def run_command_live(command:str, store_result: bool = True) -> LiteralString:
    
    output_accumulator = []
    process = None

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
            text=True,
            shell=True,
            bufsize=1,                
            universal_newlines=True
        )

        # Read the output as it arrives
        for line in process.stdout:
            # 1. Print to the terminal immediately
            sys.stdout.write(line)
            sys.stdout.flush()
            
            # 2. Save to our variable
            if store_result:
                output_accumulator.append(line)
        
        return_code = process.wait()

    except KeyboardInterrupt:
        print("\n\n[!] User interrupted. Cleaning up...")
        if process:
            process.terminate()
            process.wait()

        return "".join(output_accumulator)
    
    except Exception as e:
        print(f"\n[!] An unexpected error occurred: {e}")
        if process:
            process.kill()
        raise


    full_output = "".join(output_accumulator)
    
    if return_code != 0:
        print(f"\n[!] Command failed with exit code {return_code}")
    
    full_output = strip_non_text_codes(full_output)

    return full_output

#---------------------------------------------------#
# Call CLI
#---------------------------------------------------#
def call_cli(command: str, output_file: str, process: str, store_result: bool = True) -> None:
    print('---------------------------')
    print(f'{process} begins...')
    print('Executing Command...')
    print(command)
    print('---------------------------')

    output = run_command_live(command, store_result)

    if store_result:
        write_files_to_local(output_file, output, "txt")
        print(f'{process} complete. Check {output_file} for result')
        print('---------------------------')
    

# ----------------------------------------------------- #
# Write files to local store
# ----------------------------------------------------- #
def write_files_to_local(file_path: str, content: Any, type: str):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    full_file_path = dir_path + "/" + file_path 
    with open(full_file_path, 'w') as f:
        if type == "yaml":
            yaml.dump(content, f, default_flow_style=False)
        else:
            f.write(content)


# ----------------------------------------------------- #
# Find and return pattern from file
# ----------------------------------------------------- #
def get_data_from_output(file_path: str, pattern: str):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    full_file_path = dir_path + "/" + file_path
    try:
        with open(full_file_path, 'r') as f:
            for line in f:
                if pattern in line:
                    return line.strip()
    except:
        return None