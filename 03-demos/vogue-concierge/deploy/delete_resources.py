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

import vertexai
from lib import shell_utils
import utils
from yaml_parser import YAMLParser
from colorama import init, Fore, Style

# ----------------------------------------------------- #
# Delete agent engine agent
# ----------------------------------------------------- #
def delete_agent_engine_agent(parser: YAMLParser) -> None:
    """Deletes the agent engine agent.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """
    AGENT_ENGINE_ID = "agent_engine_id"
    ae_id = parser.deployed_resources.get(AGENT_ENGINE_ID, None)
    if ae_id:
        try:
            client = vertexai.Client(project=parser.PROJECT_ID, location=parser.AGENT_ENGINE_REGION)
            name = f"projects/{parser.PROJECT_NUMBER}/locations/{parser.AGENT_ENGINE_REGION}/reasoningEngines/{ae_id}"
            remote_agent = client.agent_engines.get(name=name)
            if not remote_agent:
                print(f"Unable to get remote agent - {name}")
            remote_agent.delete(force=True)
        
        except Exception as e:
            print(f"Unable to delete the agent engine agent - {e}")
    
        deleted = parser.deployed_resources.pop(AGENT_ENGINE_ID, None)
        if not deleted:
            print(f"Agent engine agent was deleted successfully but the entry in the {parser.DEPLOYED_RESOURCES_FILE} was not removed. Please remove it manually")

    return parser

# ----------------------------------------------------- #
# Delete Cloud run service
# ----------------------------------------------------- #
def delete_cloud_run_service(parser: YAMLParser) -> None:
    """Deletes the Cloud Run service.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """
    CR_SERVICE = "cloud_run_service"
    CR_URL = "cloud_run_url"
    cr_service = parser.deployed_resources.get(CR_SERVICE, None)
    cr_url = parser.deployed_resources.get(CR_URL, None)
    if cr_service:
        command = f"gcloud run services delete {cr_service} --async --region={parser.CLOUDRUN_REGION}"
        shell_utils.call_cli(command,"",f"Deleting Cloudrun service {cr_service}", False)
    
        parser.deployed_resources.pop(CR_SERVICE, None)    
        parser.deployed_resources.pop(CR_URL, None)    

    return parser
        
# ----------------------------------------------------- #
# Main Entry
# ----------------------------------------------------- #
def main(parser: YAMLParser ) -> None:
    """The main entry point for deleting resources.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """
    init()
    print(Style.BRIGHT + Fore.RED + "**************************************************")
    print(Style.BRIGHT + Fore.RED + "DANAGER ZONE!!!")
    print(Style.BRIGHT + Fore.RED + "You are deleting the following deployed resources")
    utils.list_deployed_resources(parser)
    print(Style.BRIGHT + Fore.RED + "***************************************************")
    confirm = input("Do you want to continue? (y/N): ")
    print(Style.RESET_ALL)
    if confirm.lower() == 'y':
        parser = delete_agent_engine_agent(parser=parser)
        parser = delete_cloud_run_service(parser=parser)
    
    
    parser.setResources()
    
    