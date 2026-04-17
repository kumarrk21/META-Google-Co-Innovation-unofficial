import os
import argparse

from regex import P
import utils
from yaml_parser import YAMLParser
from deploy import load_data, deploy_to_ae, deploy_to_cr, delete_resources
from tests import test_agent, test_app


# ----------------------------------------------------- #
# Process the options
# ----------------------------------------------------- #
def process(option:str) -> None:

    parser = YAMLParser()
    
    match option:
        case "1":
            utils.init(parser)
            pass        
        case "2":  # Load all data
            load_data.load(parser)
        case "3":  # Deploy Agent to Agent Engine
            utils.write_agent_env_file(parser)
            deploy_to_ae.update_ae_sa_auth(parser)
            deploy_to_ae.deploy(parser)
        case "4":  # Deploy app to CloudRun
            deploy_to_cr.update_cr_sa_auth(parser=parser)
            deploy_to_cr.update_ce_sa_auth(parser=parser)
            deploy_to_cr.deploy(parser=parser)
            pass
        case "5":  # Test just the agent locally
            test_agent.main(parser=parser,target='local')
            pass
        case "6": # Test the agent deployed to agent engine
            test_agent.main(parser=parser,target='ae')
            pass
        case "7": # Test the app + agent locally
            test_app.main(parser=parser,target='local')
            pass
        case "8": # Test the app + agent remote
            test_app.main(parser=parser,target='remote')
            pass
        case "9": # List deployed resources
            utils.list_deployed_resources(parser=parser)
            pass
        case "10": # Proxy Cloud run local
            utils.proxy_cloud_run_locally(parser=parser)
            pass
        case "98": # debug purposes
            print(parser.API_NAME)
            pass
        case "99": # Delete deployed resources
            delete_resources.main(parser=parser)
            pass    
        case _:
            print("You have chosen an option that is not available. Please choose from available options")
            pass    

# ----------------------------------------------------- #
# Main function
# ----------------------------------------------------- #
def main() -> None:
    # Arg Parser
    parser = argparse.ArgumentParser(description = "Demo Deployment helper")
    available_options = ["1","2","3","4","5","6","7","8","9","10","98","99"]

    parser.add_argument(
        "-o", "--option", help="What do you want to deploy",
        choices = available_options
        )

    args = parser.parse_args()

    option = args.option
    if str(option) not in available_options :
        while True:
            option = input(
                "What do you want to do?:\n"
                "   1 - initialize\n"
                "   2 - load data\n"
                "   3 - deploy agent to agent engine\n"
                "   4 - deploy app to cloud run\n"
                "   5 - test agent locally\n"
                "   6 - test agent deployed to agent engine\n"
                "   7 - test app locally with local agent\n"
                "   8 - test app locally with agent engine agent\n"
                "   9 - list deployed resources\n"
                "   10 - proxy to Cloudrun app locally\n"
                "   99 - delete deployed resource\n"
                "Selection: "
            ).strip()
            
            if option in available_options:
                break
            print("\n[!] Choose a valid option from the list (1-10)")

    print(f"Proceeding with option: {option}")

    process(option)


# ----------------------------------------------------- #
# Main Entry
# ----------------------------------------------------- #
if __name__ == "__main__":
    main()
    
    