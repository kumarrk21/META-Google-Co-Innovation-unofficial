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
from lib import shell_utils, file_utils
from yaml_parser import YAMLParser


AUTH_RESULT_FILE = 'cr_auth_result.txt'
AUTH_PROCESS = 'Giving cloud run service account required roles'

CE_AUTH_RESULT_FILE = 'ce_auth_result.txt'
CE_AUTH_PROCESS = 'Giving compute engine service account required roles'


# ----------------------------------------------------- #
# Deploy to the App (API + UI) to CloudRun
# ----------------------------------------------------- #
def deploy(parser: YAMLParser) -> None:
    """Deploys the application to Cloud Run.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """

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

    shell_utils.call_cli(command,deployment_result_file,DEPLOYMENT_PROCESS)

    url = file_utils.get_cloud_run_url(deployment_result_file)

    if url:
        parser.deployed_resources["cloud_run_service"] = f"{parser.API_NAME}"
        parser.deployed_resources["cloud_run_url"] = url
        parser.setResources()

# ----------------------------------------------------- #
# Update auth for the cloud run service accuont
# ----------------------------------------------------- #
def update_cr_sa_auth(parser: YAMLParser) -> None:
    """Updates the IAM policy for the Cloud Run service account.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """

    project_id = parser.PROJECT_ID
    cloud_run_sa = parser.CLOUD_RUN_SA
    required_auth = parser.required_auth['cloud_run_sa']

    commands = []
    for role in required_auth:
        commands.append(f'gcloud projects add-iam-policy-binding {project_id} --member="serviceAccount:{cloud_run_sa}" --role="{role}" --no-user-output-enabled')

    command = format("\n".join(commands))
    
    auth_result_file = f"{parser.DEPLOY_RESULTS_FOLDER}/{AUTH_RESULT_FILE}"

    shell_utils.call_cli(command,auth_result_file,AUTH_PROCESS)

# ----------------------------------------------------- #
# Update auth for the compute service accuont
# ----------------------------------------------------- #
def update_ce_sa_auth(parser: YAMLParser) -> None:
    """Updates the IAM policy for the Compute Engine service account.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    """

    project_id = parser.PROJECT_ID
    compute_engine_sa = parser.COMPUTE_ENGINE_SA
    required_auth = parser.required_auth['compute_engine_sa']

    commands = []
    for role in required_auth:
        commands.append(f'gcloud projects add-iam-policy-binding {project_id} --member="serviceAccount:{compute_engine_sa}" --role="{role}" --no-user-output-enabled')

    command = format("\n".join(commands))

    auth_result_file = f"{parser.DEPLOY_RESULTS_FOLDER}/{AUTH_RESULT_FILE}"
    
    shell_utils.call_cli(command,CE_AUTH_RESULT_FILE,CE_AUTH_PROCESS)



