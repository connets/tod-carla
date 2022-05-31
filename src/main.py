import os
import sys
import time
from copy import deepcopy
from datetime import datetime

import carla
import pygame
import yaml
from pathlib import Path

from src.FolderPath import FolderPath
from src.TeleConstant import FinishCode
from src.TeleContext import TeleContext
from src.TeleOutputWriter import DataCollector
from src.TeleSimulator import TeleSimulator
from src.actor.InfoSimulationActor import SimulationRatioActor, PeriodicDataCollectorActor
from src.actor.TeleCarlaActor import TeleCarlaVehicle, TeleCarlaPedestrian
from src.actor.TeleMEC import TeleMEC
from src.actor.TeleOperator import TeleOperator
from src.actor.TeleCarlaSensor import TeleCarlaCameraSensor, TeleCarlaGnssSensor, TeleCarlaCollisionSensor
from src.args_parse import TeleConfiguration
from src.args_parse.TeleConfiguration import TeleConfiguration
from src.build_world import create_sim_world, create_route, destroy_sim_world
from src.carla_bridge.TeleWorld import TeleWorld
from src.network.NetworkChannel import TcNetworkInterface, DiscreteNetworkChannel
from src.utils.Hud import HUD
from src.TeleWorldController import BehaviorAgentTeleWorldController, KeyboardTeleWorldController, \
    BasicAgentTeleWorldController
import src.utils as utils


def create_display(carla_simulation_conf):
    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode(
        (carla_simulation_conf['camera']['width'], carla_simulation_conf['camera']['height']),
        pygame.HWSURFACE | pygame.DOUBLEBUF)
    # display.fill((0, 0, 0))
    pygame.display.flip()
    return display


def main(simulation_conf, scenario_conf):
    """
    get configurations for simulation:
    - carla_server_file (default: configuration/default_server.yaml),
    - carla_simulation_file(default: configuration/default_simulation_curve.yaml)
    """

    client, sim_world = create_sim_world(simulation_conf['host'], simulation_conf['port'], simulation_conf['timeout'],
                                         scenario_conf['world'],
                                         simulation_conf['seed'],
                                         simulation_conf['synchronicity'],
                                         simulation_conf['timing'][
                                             'time_step'] if 'timing' in simulation_conf and 'time_step' in
                                                             simulation_conf['timing'] else None)

    # traffic_manager = client.get_trafficmanager()

    tele_world: TeleWorld = TeleWorld(client, simulation_conf['synchronicity'])

    pedestrian = TeleCarlaPedestrian('127.0.0.1', utils.find_free_port(),
                                     carla.Location(x=376, y=-1.990084, z=0.001838))

    start_transform, destination_location = create_route(tele_world, scenario_conf)
    player_attrs = {'role_name': 'hero'}
    player = TeleCarlaVehicle('127.0.0.1', utils.find_free_port(), simulation_conf['synchronicity'], 0.05,
                              scenario_conf['vehicle_player'],
                              player_attrs,
                              start_transform=start_transform,
                              modify_vehicle_physics=True)

    # controller = BasicAgentTeleWorldController()  # TODO change here
    # controller = BasicAgentTeleWorldController()
    clock = pygame.time.Clock()

    show_camera = simulation_conf['render'] or simulation_conf['controller']['type'] == 'manual'
    if show_camera:
        display = create_display(simulation_conf)
        hud = HUD(tele_world, player, clock, simulation_conf['camera']['width'],
                  simulation_conf['camera']['height'])
        camera_sensor = TeleCarlaCameraSensor(hud, 2.2, 1280, 720)
        player.attach_sensor(camera_sensor)
    collisions_sensor = TeleCarlaCollisionSensor()
    player.attach_sensor(collisions_sensor)

    # controller = KeyboardTeleWorldController(clock)

    controller = BehaviorAgentTeleWorldController('normal', start_transform.location, destination_location)

    tele_operator = TeleOperator('127.0.0.1', utils.find_free_port(), controller)
    mec = TeleMEC('127.0.0.1', utils.find_free_port())

    backhaul_uplink_delay = scenario_conf['delay']['backhaul']['uplink_extra_delay']
    backhaul_downlink_delay = scenario_conf['delay']['backhaul']['downlink_extra_delay']

    if simulation_conf['synchronicity']:
        vehicle_operator_channel = DiscreteNetworkChannel(tele_operator,
                                                          utils.delay_family_to_func[backhaul_uplink_delay['family']](
                                                              **backhaul_uplink_delay['parameters']), 0.1)
        operator_vehicle_channel = DiscreteNetworkChannel(player,
                                                          utils.delay_family_to_func[backhaul_downlink_delay['family']](
                                                              **backhaul_downlink_delay['parameters']), 0.1)
    else:
        vehicle_operator_channel = TcNetworkInterface(tele_operator, utils.delay_family_to_func['constant'](0.1), 0.1,
                                                      'lo')
        operator_vehicle_channel = TcNetworkInterface(player, utils.delay_family_to_func['constant'](0.1), 0.1, 'lo')

    player.add_channel(vehicle_operator_channel)
    tele_operator.add_channel(operator_vehicle_channel)

    # player.set_context(tele_context)
    # player.start(tele_world)
    # tele_operator.set_context(tele_context)
    # tele_operator.start(tele_world)
    # mec.set_context(tele_context)
    # mec.start(tele_world)

    # tele_world.add_sensor(camera_manager, player)

    # controller = KeyboardTeleWorldController(camera_manager)  # TODO change here
    # tele_world.add_controller(controller)

    # gnss_sensor = TeleGnssSensor()
    # tele_world.add_sensor(gnss_sensor, player)

    # tele_world.start()

    data_collector = PeriodicDataCollectorActor(FolderPath.OUTPUT_RESULTS_PATH + "sensors.csv",
                                                {'timestamp': lambda: utils.format_number(
                                                    tele_world.timestamp.elapsed_seconds, 5),
                                                 'velocity_x': lambda: utils.format_number(player.get_velocity().x, 5),
                                                 'velocity_y': lambda: utils.format_number(player.get_velocity().y, 5),
                                                 'velocity_z': lambda: utils.format_number(player.get_velocity().z, 5),
                                                 'acceleration_x': lambda: utils.format_number(
                                                     player.get_acceleration().x, 5),
                                                 'acceleration_y': lambda: utils.format_number(
                                                     player.get_acceleration().y, 5),
                                                 'acceleration_z': lambda: utils.format_number(
                                                     player.get_acceleration().z, 5),
                                                 'location_x': lambda: utils.format_number(player.get_location().x, 5),
                                                 'location_y': lambda: utils.format_number(player.get_location().y, 5),
                                                 'location_z': lambda: utils.format_number(player.get_location().z, 5),
                                                 # 'altitude': lambda: round(gnss_sensor.altitude, 5),
                                                 # 'longitude': lambda: round(gnss_sensor.longitude, 5),
                                                 # 'latitude': lambda: round(gnss_sensor.latitude, 5),
                                                 # 'throttle': lambda: round(player.get_control().throttle, 5),
                                                 # 'steer': lambda: round(player.get_control().steer, 5),
                                                 # 'brake': lambda: round(player.get_control().brake, 5)
                                                 }, 0.005)

    # data_collector.add_interval_logging(lambda: tele_world.timestamp.elapsed_seconds, 0.1)
    #
    # here the order is important

    tele_sim = TeleSimulator(tele_world, clock)
    tele_sim.add_actor(player)
    tele_sim.add_actor(mec)
    tele_sim.add_actor(tele_operator)
    tele_sim.add_actor(data_collector)
    tele_sim.add_actor(SimulationRatioActor(1))
    tele_sim.add_actor(pedestrian)
    # camera_sensor.spawn_in_the_world(sim_world)
    # tele_sim.start()

    if show_camera:
        def render():
            camera_sensor.render(display)
            hud.render(display)
            pygame.display.flip()

        tele_sim.add_sync_tick_listener(render)
        tele_sim.add_async_tick_listener(hud.tick)

    # tele_sim.ad_sync_tick_listener(lambda: print(player.get_location()))
    controller.add_player_in_world(player)
    anchor_points = controller.get_trajectory()

    optimal_trajectory_collector = DataCollector(FolderPath.OUTPUT_RESULTS_PATH + 'optimal_trajectory.csv')
    optimal_trajectory_collector.write('location_x', 'location_y', 'location_z')
    # for point in anchor_points:
    #     optimal_trajectory_collector.write(point['x'], point['y'], point['z'])

    try:
        status_code = tele_sim.do_simulation(simulation_conf['synchronicity'])

        finished_status_sim = {
            FinishCode.ACCIDENT: 'ACCIDENT',
            FinishCode.OK: 'FINISH',
        }[status_code]
    except Exception as e:
        finished_status_sim = 'ERROR'
        raise e
    finally:
        destroy_sim_world(client, sim_world)
        pygame.quit()
        with open(FolderPath.OUTPUT_RESULTS_PATH + 'finish_status.txt', 'w') as f:
            f.write(finished_status_sim)


def parse_configurations(carla_simulation_config_path, carla_scenario_config_path):
    res = TeleConfiguration(carla_simulation_config_path, carla_scenario_config_path)

    return res


if __name__ == '__main__':
    configuration = TeleConfiguration(sys.argv[1], sys.argv[2])

    simulation_conf = configuration['carla_simulation_file']
    scenario_conf = configuration['carla_scenario_file']

    FolderPath.CURRENT_SIMULATION_DIRECTORY_PATH = scenario_conf['delay']['backhaul']['uplink_extra_delay'][
                                                       'family'] + '_' + '_'.join(
        str(v) for v in
        scenario_conf['delay']['backhaul']['uplink_extra_delay']['parameters'] \
            .values()) + '|' + datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    Path(scenario_conf['output']['results']).mkdir(parents=True, exist_ok=True)
    Path(scenario_conf['output']['log']).mkdir(parents=True, exist_ok=True)

    FolderPath.OUTPUT_RESULTS_PATH = scenario_conf['output'][
                                         'results'] + FolderPath.CURRENT_SIMULATION_DIRECTORY_PATH + '/'
    FolderPath.OUTPUT_LOG_PATH = scenario_conf['output']['log'] + FolderPath.CURRENT_SIMULATION_DIRECTORY_PATH + '/'

    os.mkdir(FolderPath.OUTPUT_RESULTS_PATH)
    os.mkdir(FolderPath.OUTPUT_LOG_PATH)
    os.mkdir(FolderPath.OUTPUT_RESULTS_PATH + 'configurations/')

    with open(FolderPath.OUTPUT_RESULTS_PATH + 'configurations/carla_simulation_file.yaml', 'w') as outfile:
        yaml.dump(simulation_conf, outfile, default_flow_style=False)
    with open(FolderPath.OUTPUT_RESULTS_PATH + 'configurations/carla_scenario_file.yaml', 'w') as outfile:
        yaml.dump(scenario_conf, outfile, default_flow_style=False)

    main(simulation_conf, scenario_conf)
