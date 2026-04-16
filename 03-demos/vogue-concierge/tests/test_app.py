from yaml_parser import YAMLParser
import utils

def main(parser: YAMLParser, target:str) -> None:
    match target:
        case "local":
            command = f"""
            export LOCAL_AGENT=True
            honcho start
            """
            utils.call_cli(command,"","Testing app with local agent", False)
            
        case _:
            command = f"""
            export LOCAL_AGENT=False
            cd vogue_concierge_app/backend && uvicorn main:app --reload --port 8080
            """
            utils.call_cli(command,"","Testing App with Agent Engine Agent", False)