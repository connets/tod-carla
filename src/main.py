import argparse

from src.args_parse import my_parser
from src.TeleWorld import TeleWorld

tele = TeleWorld("prova", 100)



def main():
    conf_files = my_parser.parse_configuration_files()
    carla_conf = my_parser.parse_carla_args(conf_files.carla_server_file)
    print(carla_conf.host)

if __name__ == '__main__':
    main()
