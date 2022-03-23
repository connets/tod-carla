import argparse

from src.args_parse.ConfigurationParser import ConfigurationParser
from src.folder_path import CONFIGURATION_FILE_PATH


def parse_configuration_files():
    parser = ConfigurationParser()
    parser.add('--carla_server_file', metavar='CF', help='Configuration file path for Carla server',
               default=CONFIGURATION_FILE_PATH + 'default_server.yaml')
    return parser.parse()


def parse_carla_args(configuration_path):
    parser = ConfigurationParser(configuration_path)
    parser.add('--host', metavar='H', help='IP of the host server', required=True)
    parser.add('-p', '--port', metavar='P', type=int, help='TCP port to listen to')
    parser.add('-n', '--number-of-vehicles', metavar='N', type=int, help='Number of vehicles')
    parser.add('-w', '--number-of-walkers', metavar='W', type=int, help='Number of walkers (default: 10)')
    parser.add('--safe', help='Avoid spawning vehicles prone to accidents')
    parser.add('--filterv', metavar='PATTERN', help='Filter vehicle model')
    parser.add('--generationv', metavar='G',
               help='restrict to certain vehicle generation (values: "1","2","All"')
    parser.add('--filterw', metavar='PATTERN', help='Filter pedestrian type')
    parser.add('--generationw', metavar='G',
               help='restrict to certain pedestrian generation (values: "1","2","All"')
    parser.add('--tm-port', metavar='P', type=int, help='Port to communicate with TM')
    parser.add('--asynch', help='Activate asynchronous mode execution')
    parser.add('--hybrid', help='Activate hybrid mode for Traffic Manager')
    parser.add('-s', '--seed', metavar='S', type=int,
               help='Set random device seed and deterministic mode for Traffic Manager')
    parser.add('--seedw', metavar='S', type=int, help='Set the seed for pedestrians module')
    parser.add('--car-lights-on', action='store_true', help='Enable automatic car light management')
    parser.add('--hero', help='Set one of the vehicles as hero')
    parser.add('--respawn', help='Automatically respawn dormant vehicles (only in large maps)')
    parser.add('--no-rendering', help='Activate no rendering mode')

    return parser.parse(description=__doc__, argument_default=argparse.SUPPRESS)


if __name__ == '__main__':
    configuration_files = parse_configuration_files()
    print("*** =>", configuration_files)
