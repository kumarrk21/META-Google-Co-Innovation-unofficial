import os
from pathlib import Path
import yaml


CONFIG_FILE = 'config.yml'
# LOCAL_CONFIG_FILE = 'local/config.yml'

# ----------------------------------------------------- #
# YAML parser
# ----------------------------------------------------- #
class YAMLParser:
    def __init__(self):

        self.DEPLOY_FOLDER = "deploy"
        self.LOCAL_FOLDER = "local"
        self.DEPLOYED_RESOURCES_FILE = "deployed_resources.yml"
        self.REQUIRED_AUTH_FILE = "required_auth.yml"
        self.REQUIRED_APIS_FILE = "required_apis.yml"

        self.DEPLOY_RESULTS_FOLDER = "local/deploy_results"
        self.AE_DEPLOY_RESULTS_FILE = "ae_deployment_result.txt"
        self.CR_DEPLOY_RESULTS_FILE = "cr_deployment_result.txt"
        
        self.LOCAL_DATA_FOLDER = "data"
        self.LOCAL_IMAGE_FOLDER = "images"
        self.LOCAL_CATALOG_FILE = "products.json"
        self.LOCAL_CATALOG_FILE_FOR_RAG = "catalog_for_rag.md"
        self.LOCAL_TREND_REPORT_FILE = "trend_report.md"


        self.config_file_path = Path(self._get_config_file())
        self.config = self._load_yaml(self.config_file_path)

        self.deployed_resources_file_path = Path(self._get_resources_file())
        self.deployed_resources = self._load_yaml(self.deployed_resources_file_path)

        self.required_auth_file_path = Path(self._get_auth_file())    
        self.required_auth = self._load_yaml(self.required_auth_file_path)

        self.required_apis_file_path = Path(self._get_apis_file())
        self.required_apis = self._load_yaml(self.required_apis_file_path)

        # Store config values as variables for centralized access
        self.PROJECT_ID = self._getConfig('global.project_id')
        self.PROJECT_NUMBER = self._getConfig('global.project_number')
        self.REGION = self._getConfig('global.region')
        self.VERTEXAI_REGION = self._getConfig('vertexai.region')
        self.CLOUDRUN_REGION = self._getConfig('cloud_run.region')
        self.AGENT_ENGINE_REGION = self._getConfig('agent_engine.region')
        self.AGENT_NAME = self._getConfig('agent.name')
        self.AGENT_USE_VERTEXAI = self._getConfig('agent.use_vertexai')
        self.AGENT_GOOGLE_API_KEY = self._getConfig('agent..google_api_key')
        self.AGENT_FOLDER = self._getConfig('agent.folder')
        self.AGENT_LOCAL_PORT = self._getConfig('agent.local_port')
        self.AGENT_DS_BQ_DATASET_ID = self._getConfig('agent.datastores.bq.dataset_id')
        self.AGENT_DS_DATASET_DESC = self._getConfig('agent.datastores.bq.dataset_desc')
        self.AGENT_DS_DATASET_LOC = self._getConfig('agent.datastores.bq.dataset_location')
        self.AGENT_DS_INVENTORY_TABLE_NAME = self._getConfig('agent.datastores.bq.inventory_table_name')
        self.AGENT_DS_LOYALTY_TABLE_NAME = self._getConfig('agent.datastores.bq.loyalty_table_name')
        self.AGENT_DS_IMAGEGEN_MODEL_ID = self._getConfig('agent.datastores.imagegen.model_id')
        self.AGENT_DS_IMAGEGEN_REGION = self._getConfig('agent.datastores.imagegen.region')
        self.AGENT_DS_STORAGE_BUCKET_NAME = f"{self.PROJECT_NUMBER}-{self._getConfig('agent.datastores.storage.bucket_name')}"
        self.AGENT_DS_STORAGE_BUCKET_LOC = self._getConfig('agent.datastores.storage.bucket_location')
        self.AGENT_DS_STORAGE_IMAGE_FOLDER = self._getConfig('agent.datastores.storage.image_folder')
        self.AGENT_DS_STORAGE_DATA_FOLDER = self._getConfig('agent.datastores.storage.data_folder')
        self.AGENT_DS_STORAGE_RAG_FOLDER = self._getConfig('agent.datastores.storage.rag_folder')
        self.AGENT_DS_STORAGE_PRODUCT_DATA_FILE = self._getConfig('agent.datastores.storage.product_data_file')
        self.AGENT_DS_STORAGE_TREND_REPORT_FILE = self._getConfig('agent.datastores.storage.trend_report_file')
        self.AGENT_DS_STORAGE_CATALOG_FILE_FOR_RAG = self._getConfig('agent.datastores.storage.catalog_file')
        self.AGENT_DS_RAG_REGION = self._getConfig('agent.datastores.rag.region')
        self.AGENT_DS_RAG_CORPUS_NAME = self._getConfig('agent.datastores.rag.corpus_name')
        self.AGENT_DS_RAG_CORPUS_DESC = self._getConfig('agent.datastores.rag.corpus_desc')
        self.API_NAME = self._getConfig('api.name')
        self.API_FOLDER = self._getConfig('api.folder')
        self.API_LOCAL_PORT = self._getConfig('api.local_port')
        self.API_REMOTE_PORT = self._getConfig('api.remote_port')
        self.UI_FOLDER = self._getConfig('ui.folder')

        self.AGENT_ENGINE_SA = f"service-{self.PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
        # self.AGENT_ENGINE_SA = self._getConfig('global.agent_engine_sa')
        self.CLOUD_RUN_SA = self._getConfig('global.cloud_run_sa')
        self.CLOUD_RUN_USE_IAP = self._getConfig('cloud_run.use_iap')
    
        
    def _get_config_file(self) -> str:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        local_config_file = f"{dir_path}/{self.LOCAL_FOLDER}/{CONFIG_FILE}"
        config_file = f"{dir_path}/{CONFIG_FILE}"
        
        if Path(local_config_file).exists():
            return local_config_file
        return config_file
    
    def _get_resources_file(self) -> str:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return f"{dir_path}/{self.LOCAL_FOLDER}/{self.DEPLOYED_RESOURCES_FILE}"
    
    def _get_auth_file(self) -> str:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return f"{dir_path}/{self.DEPLOY_FOLDER}/{self.REQUIRED_AUTH_FILE}"
    
    def _get_apis_file(self) -> str:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return f"{dir_path}/{self.DEPLOY_FOLDER}/{self.REQUIRED_APIS_FILE}"
        

    def _load_yaml(self, file_path) -> dict:
        if not file_path.exists():
            raise FileNotFoundError(f"Yaml file not found: {file_path}")
        
        with file_path.open('r') as file:
            return yaml.safe_load(file) or {}

    def _get(self, data: dict, key_path: str, default):
        keys = key_path.split('.')
        value = data
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default 

    def _getConfig(self, key_path: str, default=None):
        return self._get(self.config, key_path, default)
    
    def initConfig(self, new_config:dict):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config_file = f"{dir_path}/{CONFIG_FILE}"
        with open(config_file, 'w') as f:
            yaml.dump(new_config,f,default_flow_style=False,sort_keys=False)

    def getResources(self, key_path: str, default=None):
        return self._get(self.deployed_resources, key_path, default)
   
    def setResources(self):
        with open(self.deployed_resources_file_path, 'w') as f:
            yaml.dump(self.deployed_resources,f,default_flow_style=False)

    
    
