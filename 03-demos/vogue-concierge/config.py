# config.py
from yaml_parser import YAMLParser

_parser = None

#---------------------------------------------------#
# Get YAML Parser
#---------------------------------------------------#
def get_parser():
    """Returns a singleton instance of the YAMLParser.

    :return: The YAMLParser instance.
    :rtype: YAMLParser
    """
    global _parser
    if _parser is None:
        _parser = YAMLParser()
    return _parser
