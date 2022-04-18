import argparse

from src.args_parse.ConfigurationParser import ConfigurationParser
from src.folder_path import CONFIGURATION_FILE_PATH, CONFIGURATION_ROUTE_PATH


def parse_configuration_files(args=None):
    parser = ConfigurationParser()
    parser.add('--carla_server_file', metavar='CF', help='Configuration file path for Carla server',
               default=CONFIGURATION_FILE_PATH + 'default_server.yaml')
    parser.add('--carla_simulation_file', metavar='CF', help='Configuration file path for simulation',
               default=CONFIGURATION_ROUTE_PATH + 'default_simulation_curve.yaml')
    parser.add('--sudo_pw', metavar='CF', help='privileged password of current user',
               required=True)
    return vars(parser.parse(args=args))


def parse_carla_server_args(configuration_path, args=None):
    parser = ConfigurationParser(configuration_path)
    parser.add('--host', metavar='H', help='IP of the host server', required=True)
    parser.add('-p', '--port', metavar='P', type=int, help='TCP port to listen to', required=True)
    parser.add('--timeout', metavar='T', type=int, help='Timeout of connection', required=True)

    return vars(parser.parse(args=args, description=__doc__, argument_default=argparse.SUPPRESS))


def parse_carla_simulation_args(configuration_path, args=None):
    parser = ConfigurationParser(configuration_path)
    parser.add('--world', metavar='W', help='Using world')
    parser.add('--vehicle_player', metavar='V', help='model vehicle to drive', required=True)

    parser.add('--synchronicity', metavar='S', type=bool, help='synchronicity of simulation',
               required=True)
    parser.add('--time_step', metavar='T', type=float, help='time-step, mandatory for synchronicity simulation')

    parser.add('--bot.vehicle_model', metavar='V', help='model of other vehicles', required=True)
    parser.add('--camera.width', metavar='V', type=int, help='model of other vehicles')
    parser.add('--camera.height', metavar='V', type=int, help='model of other vehicles', required=True)

    parser.add('--route.start.x', metavar='X', type=float, help='x of starting position', required=True)
    parser.add('--route.start.y', metavar='Y', type=float, help='y of starting position', required=True)
    parser.add('--route.start.z', metavar='Z', type=float, help='z of starting position', required=True)

    parser.add('--route.start.pitch', metavar='P', type=float, help='pitch of starting rotation', required=True)
    parser.add('--route.start.yaw', metavar='Y', type=float, help='yaw of starting rotation', required=True)
    parser.add('--route.start.roll', metavar='R', type=float, help='roll of starting rotation', required=True)

    parser.add('--route.end.x', metavar='X', type=float, help='x of ending position', required=True)
    parser.add('--route.end.y', metavar='Y', type=float, help='y of ending position', required=True)
    parser.add('--route.end.z', metavar='Z', type=float, help='z of ending position', required=True)

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

    return vars(parser.parse(args=args, description=__doc__, argument_default=argparse.SUPPRESS))


if __name__ == '__main__':
    conf_files = parse_configuration_files()
    # carla_conf = parse_carla_args(conf_files.carla_server_file)
