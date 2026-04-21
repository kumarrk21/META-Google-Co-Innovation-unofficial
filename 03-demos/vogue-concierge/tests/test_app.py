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

from yaml_parser import YAMLParser
from lib import shell_utils

#---------------------------------------------------#
# Test App
#---------------------------------------------------#
def main(target:str) -> None:
    """Tests the application.

    :param target: The target to test, either "local" or "remote".
    :type target: str
    """
    match target:
        case "local":
            command = f"""
            export LOCAL_AGENT=True
            honcho start
            """
            shell_utils.call_cli(command,"","Testing app with local agent", False)
            
        case _:
            command = f"""
            export LOCAL_AGENT=False
            cd vogue_concierge_app/backend && uvicorn main:app --reload --port 8080
            """
            shell_utils.call_cli(command,"","Testing App with Agent Engine Agent", False)