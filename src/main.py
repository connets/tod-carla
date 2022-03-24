import argparse

import carla

from src.args_parse import my_parser
from src.TeleWorld import TeleWorld


def main():
    conf_files = my_parser.parse_configuration_files()
    carla_conf = my_parser.parse_carla_args(conf_files.carla_server_file)
    client = carla.Client(carla_conf.host, carla_conf.port)
    print(client.get_available_maps())
    world = client.load_world('Town01')


if __name__ == '__main__':
    main()
