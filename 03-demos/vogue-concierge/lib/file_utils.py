# file_utils.py
import os
import yaml
from typing import Any
from pathlib import Path

#---------------------------------------------------#
# Write files to local store
#---------------------------------------------------#
def write_files_to_local(file_path: str, content: Any, type: str):
    """Writes content to a specified local file.

    :param file_path: The path to the file to write to, relative to the project root.
    :type file_path: str
    :param content: The content to write to the file.
    :type content: Any
    :param type: The type of the content, either "yaml" or "txt".
                 If "yaml", content will be YAML dumped. Otherwise, it's written as plain text.
    :type type: str
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    full_file_path = dir_path + "/../" + file_path
    with open(full_file_path, 'w') as f:
        if type == "yaml":
            yaml.dump(content, f, default_flow_style=False)
        else:
            f.write(content)

#---------------------------------------------------#
# Find and return pattern from file
#---------------------------------------------------#
def get_data_from_output(file_path: str, pattern: str):
    """Finds and returns the first line in a file that contains a given pattern.

    :param file_path: The path to the file to read.
    :type file_path: str
    :param pattern: The pattern to search for.
    :type pattern: str
    :return: The line containing the pattern, or None if not found.
    :rtype: str | None
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    full_file_path = dir_path + "/../" + file_path
    try:
        with open(full_file_path, 'r') as f:
            for line in f:
                if pattern in line:
                    return line.strip()
    except:
        return None

#---------------------------------------------------#
# Get Agent Engine ID
#---------------------------------------------------#
def get_agent_engine_id(parser, deployment_result_file: str) -> str|None:
    """Gets the Agent Engine ID from the deployment result file.

    :param parser: The YAMLParser object containing the project configuration.
    :type parser: YAMLParser
    :param deployment_result_file: The path to the deployment result file.
    :type deployment_result_file: str
    :return: The Agent Engine ID, or None if not found.
    :rtype: str | None
    """
    ae_id = ""
    try:
        project_number = parser.PROJECT_NUMBER
        region = parser.AGENT_ENGINE_REGION

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

#---------------------------------------------------#
# Get CloudRun Url
#---------------------------------------------------#
def get_cloud_run_url(deployment_result_file:str) -> str|None:
    """Gets the Cloud Run URL from the deployment result file.

    :param deployment_result_file: The path to the deployment result file.
    :type deployment_result_file: str
    :return: The Cloud Run URL, or None if not found.
    :rtype: str | None
    """
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
