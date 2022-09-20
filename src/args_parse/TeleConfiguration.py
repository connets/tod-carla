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
            self['carla_server_configuration_readable'] = self._parse_carla_server_args(
                self['carla_server_configuration_path'])
            self['carla_server_configuration'] = parser_utils.parse_unit_measurement(
                self['carla_server_configuration_readable'])

            self.a = 'a'

    def parse(self, key, config):
        self[key] = parser_utils.parse_unit_measurement(config)

    def save_config(self, simulation_file_out_path, readable=True):
        # if readable:
        #     server_config = self['carla_server_configuration_readable']
        # else:
        print(self)
        with open(simulation_file_out_path, 'w') as outfile:
            yaml.dump(dict(self), outfile, default_flow_style=False)

    @staticmethod
    def _parse_carla_server_args(configuration_path, args=None):
        parser = ConfigurationParser(configuration_path)
        parser.add('--tag', metavar='H', help='Tag of current simulation', required=True)

        parser.add('--carla_server.host', metavar='H', help='IP of the host server', required=True)
        parser.add('--carla_server.carla_handler_port', metavar='P', type=int,
                   help='TCP port to listen to Carla Handler', required=True)
        parser.add('--carla_server.carla_simulator_port', metavar='P', type=int,
                   help='TCP port to listen to Carla simulator', required=True)
        parser.add('--carla_server.timeout', metavar='T', help='Timeout of connection', required=True)
        parser.add('--carla_server.retry_count', metavar='T',
                   help='Number of times Carla client try to reconnect to server', required=True)
        parser.add('--render', help='Show display', default=False, action='store_true')
        parser.add('--results_output_interval', help='Interval of output results sampling', default=False,
                   action='store_true')

        # parser.add('--carla_api_zmq.host', metavar='H', help='IP of the ZMQ server', required=True)
        parser.add('--carla_api_zmq.protocol', metavar='P', type=str, help='ZMQ protocol to use for the communication',
                   required=True)
        parser.add('--carla_api_zmq.port', metavar='P', type=int, help='ZMQ port to listen to', required=True)
        parser.add('--carla_api_zmq.connection_timeout', metavar='T', type=int, help='ZMQ Timeout of listen connection',
                   required=True)
        parser.add('--carla_api_zmq.data_transfer_timeout', metavar='T', type=int,
                   help='ZMQ Timeout of trasmission communication', required=True)

        parser.add('--output.log.directory', type=str, help='Log output directory')
        parser.add('--output.result.directory', type=str, help='Result output directory')
        parser.add('--output.result.interval', help='Interval of results storage')
        parser.add('--output.images', type=str, help='Images output directory')
        return parser.parse(args=args, description=__doc__, argument_default=argparse.SUPPRESS)

    @staticmethod
    def _parse_yaml_file(file_path):
        with open(file_path, 'r') as stream:
            config_vars_complete = yaml.load(stream, Loader=yaml.FullLoader)
            return parser_utils.parse_unit_measurement(config_vars_complete)

    @classmethod
    def parse_conf(cls, file_path):
        return cls._parse_yaml_file(file_path)


    def parse_route_conf(self, configuration_name):
        file_path = FolderPath.CONFIGURATION_ROUTE + configuration_name + '.yaml'

        return self._parse_yaml_file(file_path)


if __name__ == '__main__':
    # TeleConfiguration('configuration/server/default_simulation.yaml')
    # print(TeleConfiguration.instance['carla_server_configuration_readable'])
    ...
