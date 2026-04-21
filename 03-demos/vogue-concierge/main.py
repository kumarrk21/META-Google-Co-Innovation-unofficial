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

"""Main script for deploying and managing the Vogue Concierge demo application.

This script provides command-line options to initialize the project,
load data, deploy agents to Agent Engine, deploy the web application to Cloud Run,
run various tests, list deployed resources, and delete resources.
"""
import os
import argparse

from regex import P
import utils
from config import get_parser
from deploy import load_data, deploy_to_ae, deploy_to_cr, delete_resources
from tests import test_agent, test_app


# ----------------------------------------------------- #
# Process the options
# ----------------------------------------------------- #
def process(option:str) -> None:
    """Processes the selected option.

    :param option: The selected option as a string.
    :type option: str
    """

    parser = get_parser()
    
    match option:
        case "init":
            utils.init(parser)
            pass        
        case "load-data":
            load_data.load(parser)
        case "deploy-agent":
            utils.write_agent_env_file(parser)
            deploy_to_ae.update_ae_sa_auth(parser)
            deploy_to_ae.deploy(parser)
        case "deploy-app":
            deploy_to_cr.update_cr_sa_auth(parser=parser)
            deploy_to_cr.update_ce_sa_auth(parser=parser)
            deploy_to_cr.deploy(parser=parser)
            pass
        case "test-agent-local":
            test_agent.main(
                project_id=parser.PROJECT_ID,
                agent_engine_region=parser.AGENT_ENGINE_REGION,
                agent_engine_id=parser.getResources("agent_engine_id"),
                target='local'
            )
            pass
        case "test-agent-remote":
            test_agent.main(
                project_id=parser.PROJECT_ID,
                agent_engine_region=parser.AGENT_ENGINE_REGION,
                agent_engine_id=parser.getResources("agent_engine_id"),
                target='ae'
            )
            pass
        case "test-app-local":
            test_app.main(target='local')
            pass
        case "test-app-remote":
            test_app.main(target='remote')
            pass
        case "list-resources":
            utils.list_deployed_resources(parser=parser)
            pass
        case "proxy-cloud-run":
            utils.proxy_cloud_run_locally(parser=parser)
            pass
        case "delete-resources":
            delete_resources.main(parser=parser)
            pass    
        case _:
            print("You have chosen an option that is not available. Please choose from available options")
            pass    

# ----------------------------------------------------- #
# Main function
# ----------------------------------------------------- #
def main() -> None:
    """Main function to parse arguments and execute the selected option."""
    # Arg Parser
    parser = argparse.ArgumentParser(description = "Demo Deployment helper")
    available_options = [
        "init",
        "load-data",
        "deploy-agent",
        "deploy-app",
        "test-agent-local",
        "test-agent-remote",
        "test-app-local",
        "test-app-remote",
        "list-resources",
        "proxy-cloud-run",
        "delete-resources",
    ]

    parser.add_argument(
        "-o", "--option", help="What do you want to do?",
        choices = available_options
        )

    args = parser.parse_args()

    option = args.option
    if option not in available_options :
        while True:
            option = input(
                "What do you want to do?:\n"
                "   init - initialize\n"
                "   load-data - load data\n"
                "   deploy-agent - deploy agent to agent engine\n"
                "   deploy-app - deploy app to cloud run\n"
                "   test-agent-local - test agent locally\n"
                "   test-agent-remote - test agent deployed to agent engine\n"
                "   test-app-local - test app locally with local agent\n"
                "   test-app-remote - test app locally with agent engine agent\n"
                "   list-resources - list deployed resources\n"
                "   proxy-cloud-run - proxy to Cloudrun app locally\n"
                "   delete-resources - delete deployed resource\n"
                "Selection: "
            ).strip()
            
            if option in available_options:
                break
            print("\n[!] Choose a valid option from the list")

    print(f"Proceeding with option: {option}")

    process(option)


# ----------------------------------------------------- #
# Main Entry
# ----------------------------------------------------- #
if __name__ == "__main__":
    main()
    
    