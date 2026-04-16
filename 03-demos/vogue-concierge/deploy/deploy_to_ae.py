from vogue_concierge_agent import agent
from yaml_parser import YAMLParser
import utils
import vertexai
from vertexai.preview import reasoning_engines


AUTH_RESULT_FILE = 'ae_auth_result.txt'
AUTH_PROCESS = 'Giving agent service account required roles'


# ----------------------------------------------------- #
# Deploy to Agent Engine
# ----------------------------------------------------- #
def deploy(parser: YAMLParser) -> None:
    project_number = parser.PROJECT_NUMBER
    region =  parser.AGENT_ENGINE_REGION
    agent_folder = parser.AGENT_FOLDER
    agent_name = parser.AGENT_NAME
    agent_engine_id = parser.getResources("agent_engine_id")
    if agent_engine_id:
        agent_engine_id = f'--agent_engine_id={agent_engine_id}'
    else:
        agent_engine_id = ''

    
    deploy_command = (
        'adk deploy agent_engine '
        f'{agent_engine_id} '
        f'--project={project_number} '
        f'--region={region} '
        f'--display_name={agent_name} '
        f'./{agent_folder}'
    )

    command = f"""
    uv pip freeze > ./{agent_folder}/requirements.txt
    {deploy_command}
    """

    deployment_result_file = f"{parser.DEPLOY_RESULTS_FOLDER}/{parser.AE_DEPLOY_RESULTS_FILE}"
    DEPLOYMENT_PROCESS = 'Agent Engine Deployment'

    utils.call_cli(command,deployment_result_file,DEPLOYMENT_PROCESS)

    ae_id = utils.get_agent_engine_id(project_number, region, deployment_result_file)
    

    if ae_id:
        parser.deployed_resources["agent_engine_id"] = ae_id
        parser.setResources()
        utils.write_api_env_file(parser)
        

# ----------------------------------------------------- #
# Update auth for the agent engine service accuont
# ----------------------------------------------------- #
def update_ae_sa_auth(parser: YAMLParser) -> None:

    project_id = parser.PROJECT_ID
    agent_engine_sa = parser.AGENT_ENGINE_SA
    required_auth = parser.required_auth['agent_engine_sa']

    commands = []
    for role in required_auth:
        commands.append(f'gcloud projects add-iam-policy-binding {project_id} --member="serviceAccount:{agent_engine_sa}" --role="{role}" --no-user-output-enabled')

    command = format("\n".join(commands))
    
    utils.call_cli(command,AUTH_RESULT_FILE,AUTH_PROCESS)


