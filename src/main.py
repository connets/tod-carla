import random
import time
from copy import deepcopy

import carla
import pygame
import yaml
from carla import libcarla, Transform, Location, Rotation

from src.TeleContext import TeleContext
from src.TeleOutputWriter import DataCollector, CURRENT_OUT_PATH
from src.TeleSimulator import TeleSimulator
from src.actor.InfoSimulationActor import SimulationRatioActor, PeriodicDataCollectorActor
from src.actor.TeleMEC import TeleMEC
from src.actor.TeleOperator import TeleOperator
from src.actor.TeleCarlaVehicle import TeleCarlaVehicle
from src.actor.TeleCarlaSensor import TeleCarlaCameraSensor, TeleGnssSensor
from src.args_parse import TeleConfiguration
from src.args_parse.TeleConfiguration import TeleConfiguration
from src.carla_bridge.TeleWorld import TeleWorld
from src.network.NetworkChannel import TcNetworkInterface, DiscreteNetworkChannel
from src.utils.Hud import HUD
from src.TeleWorldController import BehaviorAgentTeleWorldController, KeyboardTeleWorldController, \
    BasicAgentTeleWorldController
import src.utils as utils


def parse_configurations():
    res = TeleConfiguration()
    # conf_files = my_parser.parse_configuration_files()
    # res['carla_simulation_file'] = my_parser.parse_carla_server_args(conf_files['carla_simulation_file'])
    # res['carla_scenario_file'] = my_parser.parse_carla_simulation_args(conf_files['carla_scenario_file'])
    with open(CURRENT_OUT_PATH + 'carla_simulation_file.yaml', 'w') as outfile:
        yaml.dump(res['carla_simulation_file'], outfile, default_flow_style=False)
    with open(CURRENT_OUT_PATH + 'carla_scenario_file.yaml', 'w') as outfile:
        yaml.dump(res['carla_scenario_file'], outfile, default_flow_style=False)
    return res


def create_display(carla_simulation_conf):
    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode(
        (carla_simulation_conf['camera']['width'], carla_simulation_conf['camera']['height']),
        pygame.HWSURFACE | pygame.DOUBLEBUF)
    # display.fill((0, 0, 0))
    pygame.display.flip()
    return display

def create_sim_world(host, port, timeout, world, seed, sync, time_step=None):
    client: libcarla.Client = carla.Client(host, port)
    client.set_timeout(timeout)
    sim_world: carla.World = client.load_world(world)
    sim_world.set_weather(carla.WeatherParameters.ClearSunset)

    random.seed(seed)

    if sync:
        settings = sim_world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = time_step
        sim_world.apply_settings(settings)
        traffic_manager = client.get_trafficmanager()
        traffic_manager.set_synchronous_mode(True)  # TODO move from here, check if sync is active or not
        traffic_manager.set_random_device_seed(seed)
    client.reload_world(False)  # reload map keeping the world settings
    sim_world.tick()

    # traffic_manager.set_synchronous_mode(True)

    return client, sim_world


def destroy_sim_world(client, sim_world):
    settings = sim_world.get_settings()
    settings.synchronous_mode = False
    settings.fixed_delta_seconds = None
    sim_world.apply_settings(settings)
    traffic_manager = client.get_trafficmanager()
    traffic_manager.set_synchronous_mode(False)
    client.reload_world(False)  # reload map keeping the world settings


def create_route(tele_world, scenario_conf):
    carla_map = tele_world.carla_map
    if 'route' in scenario_conf:
        # for spawn_point in carla_map.get_spawn_points():
        #     if abs(367.227295 - spawn_point.location.x) < 6:
        #         print(spawn_point)
        start_transform = Transform(
            Location(x=scenario_conf['route']['start']['x'], y=scenario_conf['route']['start']['y'],
                     z=scenario_conf['route']['start']['z']),
            Rotation(pitch=scenario_conf['route']['start']['pitch'],
                     yaw=scenario_conf['route']['start']['yaw'],
                     roll=scenario_conf['route']['start']['roll']))
        destination_location = Location(x=scenario_conf['route']['end']['x'],
                                        y=scenario_conf['route']['end']['y'],
                                        z=scenario_conf['route']['end']['z'])
    else:
        spawn_points = carla_map.get_spawn_points()
        start_transform = random.choice(spawn_points) if spawn_points else carla.Transform()
        destination_location = random.choice(spawn_points).location

    return start_transform, destination_location


def main():
    """
    get configurations for simulation:
    - carla_server_file (default: configuration/default_server.yaml),
    - carla_simulation_file(default: configuration/default_simulation_curve.yaml)
    """

    configurations = parse_configurations()
    simulation_conf = configurations['carla_simulation_file']
    scenario_conf = configurations['carla_scenario_file']
    seed = simulation_conf['seed'] if 'seed' in simulation_conf else int(time.time())

    client, sim_world = create_sim_world(simulation_conf['host'], simulation_conf['port'], simulation_conf['timeout'],
                                         scenario_conf['world'],
                                         seed,
                                         simulation_conf['synchronicity'],
                                         simulation_conf['time_step'] if 'time_step' in simulation_conf else None)

    # traffic_manager = client.get_trafficmanager()

    tele_world: TeleWorld = TeleWorld(client, simulation_conf['synchronicity'])

    start_transform, destination_location = create_route(tele_world, scenario_conf)
    player_attrs = {'role_name': 'hero'}
    player = TeleCarlaVehicle('127.0.0.1', 28007, simulation_conf['synchronicity'], 0.05,
                              scenario_conf['vehicle_player'],
                              player_attrs,
                              start_transform=start_transform,
                              modify_vehicle_physics=True)

    # controller = BasicAgentTeleWorldController()  # TODO change here
    controller = BehaviorAgentTeleWorldController('normal', start_transform.location, destination_location)
    # controller = BasicAgentTeleWorldController()
    clock = pygame.time.Clock()
    if simulation_conf['render']:
        display = create_display(simulation_conf)
        hud = HUD(tele_world, player, clock, simulation_conf['camera']['width'],
                  simulation_conf['camera']['height'])
        camera_sensor = TeleCarlaCameraSensor(hud, 2.2, 1280, 720, output_path=CURRENT_OUT_PATH )
        player.attach_sensor(camera_sensor)
    # controller = KeyboardTeleWorldController(camera_sensor, clock)
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

    data_collector = PeriodicDataCollectorActor(CURRENT_OUT_PATH + "sensors.csv",
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
    tele_sim = TeleSimulator(tele_world, clock)
    tele_sim.add_actor(player)
    tele_sim.add_actor(mec)
    tele_sim.add_actor(tele_operator)
    tele_sim.add_actor(data_collector)
    tele_sim.add_actor(SimulationRatioActor(1))
    # camera_sensor.spawn_in_the_world(sim_world)
    tele_sim.start()

    if simulation_conf['render']:
        def render(_):
            camera_sensor.render(display)
            hud.render(display)
            pygame.display.flip()

        tele_sim.add_tick_listener(render)
        tele_sim.add_tick_listener(hud.tick)
    controller.add_player_in_world(player)
    anchor_points = controller.get_trajectory()

    optimal_trajectory_collector = DataCollector(CURRENT_OUT_PATH + 'optimal_trajectory.csv')
    optimal_trajectory_collector.write('location_x', 'location_y', 'location_z')
    for point in anchor_points:
        optimal_trajectory_collector.write(point['x'], point['y'], point['z'])

    try:
        tele_sim.do_simulation(simulation_conf['synchronicity'])
        with open(CURRENT_OUT_PATH + 'finish', 'w') as f:
            f.write('*** FINISHED ***')
    except Exception as e:
        raise e
    finally:
        destroy_sim_world(client, sim_world)
        pygame.quit()


if __name__ == '__main__':
    main()
