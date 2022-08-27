#  Socket to talk to server
import sys

from src.args_parse.TeleConfiguration import TeleConfiguration
from src.carla_omnet.CarlaOmnetSimulator import CarlaOMNeTManager

if __name__ == '__main__':
    configuration = TeleConfiguration(sys.argv[1])
    simulator_conf = simulation_conf = configuration['carla_server_configuration']
    # configuration = TeleConfiguration(sys.argv[1])
    manager = CarlaOMNeTManager(simulator_conf['carla_api_zmq']['protocol'], simulator_conf['carla_api_zmq']['port'],
                                simulator_conf['carla_api_zmq']['connection_timeout'],
                                simulator_conf['carla_api_zmq']['data_transfer_timeout'])
    manager.start_simulation()
