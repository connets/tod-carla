from src.args_parsing.ConfigurationParser import ConfigurationParser


def test_configuration_server():
    config_parser = ConfigurationParser()
    host = 'ubiquity'

    config_parser.add('--host', metavar='H', help='IP of the host server', required=True)
    args = config_parser.parse(args=['--host', host])
    assert args.host == host
