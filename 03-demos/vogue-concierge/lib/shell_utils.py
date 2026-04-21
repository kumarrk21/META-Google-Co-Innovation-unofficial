# shell_utils.py
import sys
import re
import subprocess
from typing import LiteralString

from lib import file_utils

#---------------------------------------------------#
# Strip all unwanted ANSI codes
#---------------------------------------------------#
def strip_non_text_codes(text):
    """Strips all unwanted ANSI codes from a string.

    :param text: The text to strip.
    :type text: str
    :return: The stripped text.
    :rtype: str
    """
    ansi_regex = re.compile(r'\x1B(?:[@-Z\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_regex.sub('', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text.strip()

#---------------------------------------------------#
# Run CLI command live
#---------------------------------------------------#
def run_command_live(command:str, store_result: bool = True) -> LiteralString:
    """Runs a CLI command and prints the output live.

    :param command: The command to run.
    :type command: str
    :param store_result: Whether to store the result of the command.
    :type store_result: bool
    :return: The output of the command.
    :rtype: LiteralString
    """
    
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
    """Calls a CLI command and stores the output in a file.

    :param command: The command to run.
    :type command: str
    :param output_file: The file to store the output in.
    :type output_file: str
    :param process: The name of the process.
    :type process: str
    :param store_result: Whether to store the result of the command.
    :type store_result: bool
    """
    print('---------------------------')
    print(f'{process} begins...')
    print('Executing Command...')
    print(command)
    print('---------------------------')

    output = run_command_live(command, store_result)

    if store_result:
        file_utils.write_files_to_local(output_file, output, "txt")
        print(f'{process} complete. Check {output_file} for result')
        print('---------------------------')