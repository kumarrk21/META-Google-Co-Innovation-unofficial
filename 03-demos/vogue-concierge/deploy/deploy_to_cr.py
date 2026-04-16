import os
import utils
from yaml_parser import YAMLParser


AUTH_RESULT_FILE = 'cr_auth_result.txt'
AUTH_PROCESS = 'Giving cloud run service account required roles'


# ----------------------------------------------------- #
# Deploy to the App (API + UI) to CloudRun
# ----------------------------------------------------- #
def deploy(parser: YAMLParser) -> None:

    use_iap:str = parser.CLOUD_RUN_USE_IAP
    iap = "no-iap"
    if use_iap.lower() == "true":
        iap = "iap"

    command = f"""
    uv pip freeze > ./{parser.API_FOLDER}/requirements.txt
    gcloud run deploy {parser.API_NAME} --source ./{parser.API_FOLDER} --region {parser.CLOUDRUN_REGION} --no-allow-unauthenticated --{iap} --service-account={parser.CLOUD_RUN_SA}
    """


    deployment_result_file = f"{parser.DEPLOY_RESULTS_FOLDER}/{parser.CR_DEPLOY_RESULTS_FILE}"
    DEPLOYMENT_PROCESS = 'Cloud Run Deployment for the App'

    utils.call_cli(command,deployment_result_file,DEPLOYMENT_PROCESS)

    url = utils.get_cloud_run_url(deployment_result_file)

    if url:
        parser.deployed_resources["cloud_run_url"] = url
        parser.setResources()

# ----------------------------------------------------- #
# Update auth for the cloud run service accuont
# ----------------------------------------------------- #
def update_cr_sa_auth(parser: YAMLParser) -> None:

    project_id = parser.PROJECT_ID
    cloud_run_sa = parser.CLOUD_RUN_SA
    required_auth = parser.required_auth['cloud_run_sa']

    commands = []
    for role in required_auth:
        commands.append(f'gcloud projects add-iam-policy-binding {project_id} --member="serviceAccount:{cloud_run_sa}" --role="{role}" --no-user-output-enabled')

    command = format("\n".join(commands))
    
    utils.call_cli(command,AUTH_RESULT_FILE,AUTH_PROCESS)



