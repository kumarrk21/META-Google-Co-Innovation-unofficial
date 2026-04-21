import os
from dotenv import load_dotenv

#---------------------------------------------------#
# Get Backend Config
#---------------------------------------------------#
def get_backend_config():
    load_dotenv()

    return {
        "PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "BUCKET_NAME": os.getenv("BUCKET_NAME"),
        "IMAGE_FOLDER": os.getenv("IMAGE_FOLDER"),
        "DATA_FOLDER": os.getenv("DATA_FOLDER"),
        "PRODUCT_DATA_FILE": os.getenv("PRODUCT_DATA_FILE"),
        "CLOUD_RUN_SA": os.getenv("CLOUD_RUN_SA"),
        "IS_AGENT_LOCAL": os.getenv("LOCAL_AGENT", "False").lower() == "true",
        "APP_NAME": os.getenv("APP_NAME", "vogue_concierge_agent"),
        "LOCAL_PORT": int(os.getenv("LOCAL_PORT", 8000)),
        "AGENT_ENGINE_REGION": os.getenv("AGENT_ENGINE_REGION"),
        "AGENT_ENGINE_ID": os.getenv("AGENT_ENGINE_ID"),
    }
