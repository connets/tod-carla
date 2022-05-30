import carla
import pytest
from carla import libcarla

from src.args_parse import TeleConfiguration


def established_connection():
    conf_files = my_parser.parse_configuration_files(args=[])
    carla_conf = my_parser.parse_carla_args(conf_files.carla_server_file, [])
    client : libcarla.Client = carla.Client(carla_conf.host, carla_conf.port)
    client.set_timeout(1.0)
    return client


def test_connection_server():
    client = established_connection()
    try:
        client.get_server_version()
    except Exception:
        raise pytest.fail("Client is not connected")


def test_same_versions():
    client = established_connection()
    assert client.get_client_version() == client.get_server_version()
