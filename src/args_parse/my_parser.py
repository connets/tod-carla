import argparse
from typing import Any

from src.args_parse.ConfigurationParser import ConfigurationParser
from src.folder_path import CONFIGURATION_FILE_PATH, CONFIGURATION_SCENARIO_PATH
from src.utils import parser_utils
from src.utils.decorators import Singleton


class TeleConfiguration(dict, metaclass=Singleton):

    def __init__(self) -> None:
        super().__init__()
        self._parse()

    def _parse(self):
        conf_files = self._parse_configuration_files()
        self['carla_simulation_file'] = self._parse_carla_server_args(conf_files['carla_simulation_file'])
        self['carla_scenario_file'] = self._parse_carla_simulation_args(conf_files['carla_scenario_file'])

    def _parse_configuration_files(self, args=None):
        parser = ConfigurationParser()
        parser.add('--carla_simulation_file', metavar='CF', help='Configuration file path for Carla server',
                   default=CONFIGURATION_FILE_PATH + 'default_simulation.yaml')
        parser.add('--carla_scenario_file', metavar='CF', help='Configuration file path for simulation',
                   default=CONFIGURATION_SCENARIO_PATH + 'mountain_street.yaml')
        # parser.add('--sudo_pw', metavar='CF', help='privileged password of current user',
        #            required=True)
        return parser_utils.parse_unit_measurement(parser.parse(args=args))

    def _parse_carla_server_args(self, configuration_path, args=None):
        parser = ConfigurationParser(configuration_path)
        parser.add('--host', metavar='H', help='IP of the host server', required=True)
        parser.add('-p', '--port', metavar='P', type=int, help='TCP port to listen to', required=True)
        parser.add('--timeout', metavar='T', type=int, help='Timeout of connection', required=True)
        parser.add('--render', metavar='T', type=bool, help='Timeout of connection', default=False)
        parser.add('--camera.width', metavar='V', type=int, help='model of other vehicles')
        parser.add('--camera.height', metavar='V', type=int, help='model of other vehicles', required=True)
        parser.add('--synchronicity', metavar='S', type=bool, help='synchronicity of simulation',
                   required=True)
        parser.add('--time_step', metavar='T', help='time-step, mandatory for synchronicity simulation')
        parser.add('--seed', metavar='S', type=int, help='simulation seed')

        return parser_utils.parse_unit_measurement(
            parser.parse(args=args, description=__doc__, argument_default=argparse.SUPPRESS))

    def _parse_carla_simulation_args(self, configuration_path, args=None):
        parser = ConfigurationParser(configuration_path)
        parser.add('--world', metavar='W', help='Using world')
        parser.add('--vehicle_player', metavar='V', help='model vehicle to drive', required=True)

        parser.add('--delay.backhaul.uplink_extra_delay', help='backhaul uplink extra delay', required=True)
        parser.add('--delay.backhaul.downlink_extra_delay', help='backhaul downlink extra delay', required=True)

        parser.add('--bot.vehicle_model', metavar='V', help='model of other vehicles', required=True)

        parser.add('--route.start.x', metavar='X', type=float, help='x of starting position')
        parser.add('--route.start.y', metavar='Y', type=float, help='y of starting position')
        parser.add('--route.start.z', metavar='Z', type=float, help='z of starting position')

        parser.add('--route.start.pitch', metavar='P', type=float, help='pitch of starting rotation')
        parser.add('--route.start.yaw', metavar='Y', type=float, help='yaw of starting rotation')
        parser.add('--route.start.roll', metavar='R', type=float, help='roll of starting rotation')

        parser.add('--route.end.x', metavar='X', type=float, help='x of ending position')
        parser.add('--route.end.y', metavar='Y', type=float, help='y of ending position')
        parser.add('--route.end.z', metavar='Z', type=float, help='z of ending position')

        parser.add('-n', '--number-of-vehicles', metavar='N', type=int, help='Number of vehicles')
        parser.add('-w', '--number-of-walkers', metavar='W', type=int, help='Number of walkers (default: 10)')
        parser.add('-s', '--seed', metavar='S', type=int,
                   help='Set random device seed and deterministic mode for Traffic Manager')
        parser.add('--seedw', metavar='S', type=int, help='Set the seed for pedestrians module')
        parser.add('--no-rendering', help='Activate no rendering mode')

        return parser_utils.parse_unit_measurement(
            parser.parse(args=args, description=__doc__, argument_default=argparse.SUPPRESS))



if __name__ == '__main__':
    res = TeleConfiguration()
    print(res['carla_simulation_file'])
    # TeleConfiguration
    # res = dict()
    # conf_files = parse_configuration_files()
    # res['carla_simulation_file'] = parse_carla_server_args(conf_files['carla_simulation_file'])
    # res['carla_scenario_file'] = parse_carla_simulation_args(conf_files['carla_scenario_file'])
    # # carla_server_conf = {k: parser_utils._parse_single_unit_value(v) if isinstance(v, str) else v for k, v in
    # #                      carla_server_conf.items()}
    # # carla_simulation_conf = {k: parser_utils._parse_single_unit_value(v) if isinstance(v, str) else v for k, v in
    # #                          carla_simulation_conf.items()}
    # print(type(res['carla_simulation_file']['time_step']))
