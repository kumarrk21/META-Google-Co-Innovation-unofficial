from logging import config

from yaml_parser import YAMLParser

parser = YAMLParser()
config = parser.config
config['global']['project_id'] = "[CHANGE THIS] -- Your Project ID"
config['global']['project_number'] = "[CHANGE THIS] -- Your Project Number"
config['global']['cloud_run_sa'] ="[CHANGE THIS] -- Service account for CloudRun e.g. my-service-account@my-projectid.iam.gserviceaccount.com"

parser.initConfig(config)