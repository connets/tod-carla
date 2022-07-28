import argparse
import time

import yaml

from src.FolderPath import FolderPath
from src.args_parse.ConfigurationParser import ConfigurationParser
from src.args_parse import parser_utils
from src.utils.decorators import DecoratorSingleton


@DecoratorSingleton
class TeleConfiguration(dict):

    def __init__(self, carla_simulation_config_path=None):
        super().__init__()
        if carla_simulation_config_path is not None:
            self['carla_server_configuration_path'] = carla_simulation_config_path
            self._parse()

    def _parse(self):
        self['carla_server_configuration_readable'] = self._parse_carla_server_args(
            self['carla_server_configuration_path'])
        self['carla_server_configuration'] = parser_utils.parse_unit_measurement(
            self['carla_server_configuration_readable'])

    def save_config(self, simulation_file_out_path, scenario_file_out_path, readable=True):
        if readable:
            server_config = self['carla_server_configuration_readable']
        else:
            server_config = self['carla_server_configuration']

        with open(simulation_file_out_path, 'w') as outfile:
            yaml.dump(server_config, outfile, default_flow_style=False)

    @staticmethod
    def _parse_carla_server_args(configuration_path, args=None):
        parser = ConfigurationParser(configuration_path)
        parser.add('--host', metavar='H', help='IP of the host server', required=True)
        parser.add('-p', '--port', metavar='P', type=int, help='TCP port to listen to', required=True)
        parser.add('--timeout', metavar='T', help='Timeout of connection', required=True)
        parser.add('--render', help='show display', default=False, action='store_true')

        parser.add('--output.log', type=str, help='Log output directory')
        parser.add('--output.results', type=str, help='Result output directory')
        parser.add('--output.images', type=str, help='Images output directory')
        return parser.parse(args=args, description=__doc__, argument_default=argparse.SUPPRESS)

    @staticmethod
    def _parse_yaml_file(file_path):
        with open(file_path, 'r') as stream:
            config_vars_complete = yaml.load(stream, Loader=yaml.FullLoader)

            return parser_utils.parse_unit_measurement(config_vars_complete)

    def parse_actor_conf(self, configuration_name):
        file_path = FolderPath.CONFIGURATION_ACTOR + configuration_name + '.yaml'
        return self._parse_yaml_file(file_path)

    def parse_world_conf(self, configuration_name):
        file_path = FolderPath.CONFIGURATION_WORLD + configuration_name + '.yaml'
        return self._parse_yaml_file(file_path)

    def parse_agent_conf(self, configuration_name):
        file_path = FolderPath.CONFIGURATION_AGENT + configuration_name + '.yaml'
        return self._parse_yaml_file(file_path)

    def parse_route_conf(self, configuration_name):
        file_path = FolderPath.CONFIGURATION_ROUTE + configuration_name + '.yaml'
        return self._parse_yaml_file(file_path)


if __name__ == '__main__':
    # TeleConfiguration('configuration/server/default_simulation.yaml')
    # print(TeleConfiguration.instance['carla_server_configuration_readable'])
    ...
