import argparse
import time
from typing import Any

from src.args_parse.ConfigurationParser import ConfigurationParser
from src.utils import parser_utils
from src.utils.decorators import DecoratorSingleton


@DecoratorSingleton
class TeleConfiguration(dict):

    def __init__(self, carla_simulation_config_path, carla_scenario_config_path) -> None:
        super().__init__()
        self._carla_simulation_config_path = carla_simulation_config_path
        self._carla_scenario_config_path = carla_scenario_config_path
        self._parse()

    def _parse(self):
        conf_files = self._parse_configuration_files()
        self['carla_simulation_file'] = self._parse_carla_server_args(conf_files['carla_simulation_file'])
        self['carla_scenario_file'] = self._parse_carla_simulation_args(conf_files['carla_scenario_file'])

    def _parse_configuration_files(self, args=None):
        parser = ConfigurationParser()
        parser.add('--carla_simulation_file', metavar='CF', help='Configuration file path for Carla server',
                   default=self._carla_simulation_config_path)
        parser.add('--carla_scenario_file', metavar='CF', help='Configuration file path for simulation',
                   default=self._carla_scenario_config_path)
        # parser.add('--sudo_pw', metavar='CF', help='privileged password of current user',
        #            required=True)
        return parser_utils.parse_unit_measurement(parser.parse(args=args))

    def _parse_carla_server_args(self, configuration_path, args=None):
        parser = ConfigurationParser(configuration_path)
        parser.add('--host', metavar='H', help='IP of the host server', required=True)
        parser.add('-p', '--port', metavar='P', type=int, help='TCP port to listen to', required=True)
        parser.add('--timeout', metavar='T', help='Timeout of connection', required=True)
        parser.add('--render', help='show display', default=False, action='store_true')
        parser.add('--camera.width', metavar='V', type=int, help='model of other vehicles', default=1280)
        parser.add('--camera.height', metavar='V', type=int, help='model of other vehicles', default=720)
        parser.add('--timing.time_step', metavar='T', help='time-step, mandatory for synchronicity simulation')
        parser.add('--seed', metavar='S', type=int, default=int(time.time()), help='simulation seed')
        parser.add('--controller.type', metavar='S', type=str, help='controller type', required=True)
        parser.add('--controller.behavior', metavar='S', type=str, help='controller behavior if auto')
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

        parser.add('--pedestrians', metavar='P', type=list, help='Pedestrians list', default=[])

        parser.add('--no-rendering', help='Activate no rendering mode')

        parser.add('--output.log', type=str, help='Log output directory', required=True)
        parser.add('--output.results', type=str, help='Result output directory', required=True)
        parser.add('--output.images', type=str, help='Images output directory')
        return parser_utils.parse_unit_measurement(
            parser.parse(args=args, description=__doc__, argument_default=argparse.SUPPRESS))


if __name__ == '__main__':
    import os

    PROJECT_PATH = ''.join(map(lambda x: x + '/', os.path.abspath(__file__).split('/')[:-3]))
    res = TeleConfiguration(PROJECT_PATH + 'configuration/default_simulation.yaml',
                            PROJECT_PATH + 'configuration/scenario/dangerous_curve_with_pedestrian.yaml')

    print(res['carla_scenario_file']['pedestrians'][0]['x'])
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
