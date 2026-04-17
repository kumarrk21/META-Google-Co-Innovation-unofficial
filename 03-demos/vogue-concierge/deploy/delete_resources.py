import vertexai
import utils
from yaml_parser import YAMLParser
from colorama import init, Fore, Style

# ----------------------------------------------------- #
# Delete agent engine agent
# ----------------------------------------------------- #
def delete_agent_engine_agent(parser: YAMLParser) -> None:
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
    CR_SERVICE = "cloud_run_service"
    CR_URL = "cloud_run_url"
    cr_service = parser.deployed_resources.get(CR_SERVICE, None)
    cr_url = parser.deployed_resources.get(CR_URL, None)
    if cr_service:
        command = f"gcloud run services delete {cr_service} --async --region={parser.CLOUDRUN_REGION}"
        utils.call_cli(command,"",f"Deleting Cloudrun service {cr_service}", False)
    
        parser.deployed_resources.pop(CR_SERVICE, None)    
        parser.deployed_resources.pop(CR_URL, None)    

    return parser
        
# ----------------------------------------------------- #
# Main Entry
# ----------------------------------------------------- #
def main(parser: YAMLParser ) -> None:
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
    
    
