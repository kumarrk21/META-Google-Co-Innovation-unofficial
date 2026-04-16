from yaml_parser import YAMLParser
from . import load_data_bigquery, load_data_catalog, load_data_rag

def load(parser: YAMLParser) -> None:
    load_data_bigquery.load(parser)  
    load_data_catalog.load(parser)
    load_data_rag.load(parser)


