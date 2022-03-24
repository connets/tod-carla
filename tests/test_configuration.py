import carla

from src.args_parse import my_parser
from src.args_parse.ConfigurationParser import ConfigurationParser


def test_configuration_server():
    config_parser = ConfigurationParser()
    host = 'ubiquity'

    config_parser.add('--host', metavar='H', help='IP of the host server', required=True)
    args = config_parser.parse(args=['--host', host])
    assert args.host == host

