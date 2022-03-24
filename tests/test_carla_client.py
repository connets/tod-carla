import carla

from src.args_parse import my_parser


def established_connection():
    conf_files = my_parser.parse_configuration_files(args=[])
    carla_conf = my_parser.parse_carla_args(conf_files.carla_server_file, [])
    return carla.Client(carla_conf.host, carla_conf.port)


def test_connection_server():
    assert established_connection() is not None


def test_same_versions():
    client = established_connection()
    assert client.get_client_version() == client.get_server_version()
