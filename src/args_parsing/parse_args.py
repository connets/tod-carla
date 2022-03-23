from src.args_parsing.ConfigurationParser import ConfigurationParser
from src.folder_path import CONFIGURATION_FILE_PATH


def parse_configuration_files():
    parser = ConfigurationParser()
    parser.add('--carla_server_file', metavar='CF', help='Configuration file path for Carla server',
               default=CONFIGURATION_FILE_PATH + '/default_server.yaml')
    return parser.parse()


def parse_carla_args():
    return


if __name__ == '__main__':
    configuration_files = parse_configuration_files()
    print("*** =>", configuration_files)
