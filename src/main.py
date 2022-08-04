import os
import sys

import carla
import pygame

from numpy import random

from src import utils
from src.FolderPath import FolderPath
from src.TeleOutputWriter import DataCollector, TeleLogger
from src.actor.external_passive_actors.InfoSimulationActor import SimulationRatioActor, PeriodicDataCollectorActor
from src.actor.carla_actor.TeleCarlaActor import TeleCarlaPedestrian, TODTeleCarlaVehicle, \
    CarlaOmnetTeleCarlaVehicle
from src.actor.external_active_actors.TeleMEC import TeleMEC
from src.actor.external_active_actors.TeleOperator import TeleOperator
from src.actor.carla_actor.TeleCarlaSensor import TeleCarlaCollisionSensor, TeleCarlaCameraSensor, TeleCarlaLidarSensor
from src.args_parse.TeleConfiguration import TeleConfiguration
import src.EnvironmentHandler as build_enviroment
from src.carla_bridge.TeleWorld import TeleWorld
from src.TeleWorldController import BehaviorAgentTeleWorldAdapterController, KeyboardTeleWorldAdapterController
from src.core.TeleSimulator import TeleSimulator


def main(simulation_conf, scenario_conf):
    """
    get configurations for simulation:
    - carla_server_file (default: configuration/default_server.yaml),
    - carla_simulation_file(default: configuration/default_simulation_curve.yaml)
    """

    global status_code
    random.seed(simulation_conf['seed'])
    clock = pygame.time.Clock()

    render = simulation_conf['render'] or scenario_conf['controller']['type'] == 'manual'
    client, sim_world = build_enviroment.create_sim_world(simulation_conf['host'], simulation_conf['port'],
                                                          simulation_conf['timeout'],
                                                          scenario_conf['world'],
                                                          simulation_conf['seed'],
                                                          render,
                                                          simulation_conf['simulation_time_step'])

    tele_world: TeleWorld = TeleWorld(client)

    start_transform, destination_location = build_enviroment.create_route(tele_world, scenario_conf)

    if scenario_conf['controller']['type'] == 'auto':
        controller = BehaviorAgentTeleWorldAdapterController(scenario_conf['controller']['behavior'],
                                                             scenario_conf['controller']['sampling_resolution'],
                                                             start_transform.location, destination_location)
    else:
        controller = KeyboardTeleWorldAdapterController(clock)

    # ACTORS

    player_attrs = {'role_name': 'hero'}
    # start_transform.location.x, start_transform.location.y, start_transform.location.z = 376.449982, 87.529510, 0.3

    vehicle_class = TODTeleCarlaVehicle if simulation_conf['network']['type'] == 'tod' else CarlaOmnetTeleCarlaVehicle
    player = vehicle_class(scenario_conf['player']['refresh_interval'],
                              scenario_conf['player']['speed_limit'],
                              scenario_conf['player']['model'],
                              player_attrs,
                              start_transform=start_transform,
                              # start_transform=carla.Transform(carla.Location(x=392.470001, y=68.860039, z=0.300000), carla.Rotation(pitch=0.000000, yaw=-90.000046, roll=0.000000)),
                              modify_vehicle_physics=True)

    collisions_sensor = TeleCarlaCollisionSensor()
    player.attach_sensor(collisions_sensor)

    tele_operator = TeleOperator(controller, scenario_conf['time_limit'])
    mec_server = TeleMEC()

    tele_sim = build_enviroment.create_simulator_and_network_topology(simulation_conf['network'], tele_world, clock, player,
                                                                      mec_server, tele_operator)

    camera_sensor = TeleCarlaCameraSensor(2.2)
    if render:
        build_enviroment.create_display(player, clock, tele_sim, simulation_conf['camera']['width'],
                                        simulation_conf['camera']['height'],
                                        camera_sensor, FolderPath.OUTPUT_IMAGES_PATH)

    player.attach_sensor(camera_sensor)
    lidar_sensor = TeleCarlaLidarSensor()
    player.attach_sensor(lidar_sensor)

    tele_sim.add_actor(PeriodicDataCollectorActor(FolderPath.OUTPUT_RESULTS_PATH + "vector.csv",
                                                  {'timestamp': lambda: utils.format_number(
                                                      tele_world.timestamp.elapsed_seconds, 5),
                                                   'location': lambda: player.get_transform().location,
                                                   'vector': lambda: player.get_transform().get_forward_vector()},
                                                  simulation_conf['output_results_sampling']))

    data_collector = build_enviroment.create_data_collector(tele_world, player)
    tele_sim.add_actor(mec_server)
    tele_sim.add_actor(tele_operator)
    tele_sim.add_actor(data_collector)
    tele_sim.add_actor(SimulationRatioActor(1))
    for pedestrian in scenario_conf['pedestrians']:
        pedestrian = TeleCarlaPedestrian(carla.Location(x=pedestrian['x'], y=pedestrian['y'], z=pedestrian['z']))
        tele_sim.add_actor(pedestrian)
    tele_sim.add_actor(player)

    controller.add_player_in_world(player)
    optimal_trajectory_collector = DataCollector(FolderPath.OUTPUT_RESULTS_PATH + 'optimal_trajectory.csv')
    optimal_trajectory_collector.write('location_x', 'location_y', 'location_z')
    anchor_points = controller.get_trajectory()
    for point in anchor_points:
        optimal_trajectory_collector.write(point['x'], point['y'], point['z'])

    # tele_sim.add_step_listener(
    #     lambda ts: print(player.get_location()))

    build_enviroment.apply_god_changes(tele_world, player, controller)
    try:
        status_code = tele_sim.do_simulation()
    except Exception as e:
        status_code = TeleSimulator.FinishCode.TIME_LIMIT
        raise e
    finally:
        build_enviroment.destroy_sim_world(client, sim_world)
        pygame.quit()
        with open(FolderPath.OUTPUT_RESULTS_PATH + 'finish_status.txt', 'w') as f:
            f.write(status_code.name)


if __name__ == '__main__':

    configuration = TeleConfiguration(sys.argv[1], sys.argv[2])

    #
    simulation_conf = configuration['carla_simulation_config']
    scenario_conf = configuration['carla_scenario_config']

    # Path(scenario_conf['output']['results']).mkdir(parents=True, exist_ok=True)
    # Path(scenario_conf['output']['log']).mkdir(parents=True, exist_ok=True)

    FolderPath.OUTPUT_RESULTS_PATH = simulation_conf['output']['results']
    os.makedirs(FolderPath.OUTPUT_RESULTS_PATH)

    FolderPath.OUTPUT_LOG_PATH = simulation_conf['output']['log']
    os.makedirs(FolderPath.OUTPUT_LOG_PATH)

    if 'images' in simulation_conf['output']:
        FolderPath.OUTPUT_IMAGES_PATH = simulation_conf['output']['images']
        os.makedirs(FolderPath.OUTPUT_IMAGES_PATH)

    os.mkdir(simulation_conf['output']['results'] + 'configurations/')

    configuration.save_config(FolderPath.OUTPUT_RESULTS_PATH + 'configurations/carla_simulation.yaml',
                              FolderPath.OUTPUT_RESULTS_PATH + 'configurations/carla_scenario.yaml')

    TeleLogger(FolderPath.OUTPUT_LOG_PATH)
    main(simulation_conf, scenario_conf)
