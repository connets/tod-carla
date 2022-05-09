import random
from copy import deepcopy

import carla
import pygame
from carla import libcarla, Transform, Location, Rotation

from src.TeleLogger import TeleLogger
from src.TeleContext import TeleContext
from src.TeleSimulator import TeleSimulator
from src.actor.TeleMEC import TeleMEC
from src.actor.TeleOperator import TeleOperator
from src.actor.TeleCarlaVehicle import TeleCarlaVehicle
from src.actor.TeleCarlaSensor import TeleCarlaCameraSensor, TeleGnssSensor
from src.args_parse import my_parser
from src.carla_bridge.TeleWorld import TeleWorld
from src.folder_path import OUT_PATH
from src.network.NetworkChannel import TcNetworkInterface, DiscreteNetworkChannel
from src.utils.PeriodicDataCollector import PeriodicDataCollector
from src.utils.Hud import HUD
from src.TeleWorldController import BehaviorAgentTeleWorldController, KeyboardTeleWorldController, \
    BasicAgentTeleWorldController
from src.utils.distribution_utils import delay_family_to_func
from src.utils.utils import find_free_port


def parse_configurations():
    res = dict()
    conf_files = my_parser.parse_configuration_files()
    res['carla_simulation_file'] = my_parser.parse_carla_server_args(conf_files['carla_simulation_file'])
    res['carla_scenario_file'] = my_parser.parse_carla_simulation_args(conf_files['carla_scenario_file'])
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


def create_sim_world(host, port, timeout, world, sync, time_step=None):
    client: libcarla.Client = carla.Client(host, port)
    client.set_timeout(timeout)
    sim_world: carla.World = client.load_world(world)
    sim_world.set_weather(carla.WeatherParameters.ClearSunset)

    if sync:
        traffic_manager = client.get_trafficmanager()
        traffic_manager.set_synchronous_mode(sync)  # TODO move from here, check if sync is active or not

        settings = sim_world.get_settings()
        settings.synchronous_mode = sync
        settings.fixed_delta_seconds = time_step
        sim_world.apply_settings(settings)
    # traffic_manager.set_synchronous_mode(True)

    return sim_world


def create_route(tele_world, scenario_conf):
    carla_map = tele_world.carla_map
    if 'route' in scenario_conf:
        for spawn_point in carla_map.get_spawn_points():
            if abs(72.794968 - spawn_point.location.x) < 6:
                print(spawn_point)
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

    TeleLogger()
    configurations = parse_configurations()
    simulation_conf = configurations['carla_simulation_file']
    scenario_conf = configurations['carla_scenario_file']

    display = create_display(simulation_conf)

    sim_world = create_sim_world(simulation_conf['host'], simulation_conf['port'], simulation_conf['timeout'],
                                 scenario_conf['world'], simulation_conf['synchronicity'],
                                 simulation_conf['time_step'] if 'time_step' in simulation_conf else None)

    def elapsed_seconds():
        return round(sim_world.get_snapshot().timestamp.elapsed_seconds * 1000, 3)

    TeleContext(elapsed_seconds)

    # traffic_manager = client.get_trafficmanager()

    tele_world: TeleWorld = TeleWorld(sim_world, simulation_conf['synchronicity'])

    start_transform, destination_location = create_route(tele_world, scenario_conf)
    player_attrs = {'role_name': 'hero'}
    player = TeleCarlaVehicle('127.0.0.1', 28007, simulation_conf['synchronicity'], 0.03,
                              scenario_conf['vehicle_player'],
                              player_attrs,
                              start_transform=start_transform,
                              modify_vehicle_physics=True)

    # controller = BasicAgentTeleWorldController()  # TODO change here
    controller = BehaviorAgentTeleWorldController('normal', start_transform.location, destination_location)
    # controller = BasicAgentTeleWorldController()
    clock = pygame.time.Clock()

    hud = HUD(tele_world, player, clock, simulation_conf['camera']['width'],
              simulation_conf['camera']['height'])
    camera_sensor = TeleCarlaCameraSensor(hud, 2.2, 1280, 720)
    player.attach_sensor(camera_sensor)
    # controller = KeyboardTeleWorldController(camera_sensor, clock)
    tele_operator = TeleOperator('127.0.0.1', find_free_port(), controller)
    mec = TeleMEC('127.0.0.1', find_free_port())

    if simulation_conf['synchronicity']:
        vehicle_operator_channel = DiscreteNetworkChannel(tele_operator, delay_family_to_func['constant'](0.0), 0.1)
        operator_vehicle_channel = DiscreteNetworkChannel(player, delay_family_to_func['constant'](0.0), 0.1)
    else:
        vehicle_operator_channel = TcNetworkInterface(tele_operator, delay_family_to_func['constant'](0.1), 0.1, 'lo')
        operator_vehicle_channel = TcNetworkInterface(player, delay_family_to_func['constant'](0.1), 0.1, 'lo')

    player.add_channel(vehicle_operator_channel)
    tele_operator.add_channel(operator_vehicle_channel)

    tele_context = TeleContext(tele_world.timestamp.elapsed_seconds)

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

    data_collector = PeriodicDataCollector(OUT_PATH + "tmp.csv",
                                           {'timestamp': lambda: round(tele_world.timestamp.elapsed_seconds, 5),
                                            'velocity_x': lambda: round(player.get_velocity().x, 5),
                                            'velocity_y': lambda: round(player.get_velocity().y, 5),
                                            'velocity_z': lambda: round(player.get_velocity().z, 5),
                                            'acceleration_x': lambda: round(player.get_acceleration().x, 5),
                                            'acceleration_y': lambda: round(player.get_acceleration().y, 5),
                                            'acceleration_z': lambda: round(player.get_acceleration().z, 5),
                                            # 'altitude': lambda: round(gnss_sensor.altitude, 5),
                                            # 'longitude': lambda: round(gnss_sensor.longitude, 5),
                                            # 'latitude': lambda: round(gnss_sensor.latitude, 5),
                                            'Throttle': lambda: round(player.get_control().throttle, 5),
                                            'Steer': lambda: round(player.get_control().steer, 5),
                                            'Brake': lambda: round(player.get_control().brake, 5)
                                            })

    # data_collector.add_interval_logging(lambda: tele_world.timestamp.elapsed_seconds, 0.1)
    #
    tele_sim = TeleSimulator(tele_world, tele_context, clock)
    tele_sim.add_network_node(player)
    tele_sim.add_network_node(mec)
    tele_sim.add_network_node(tele_operator)

    # camera_sensor.spawn_in_the_world(sim_world)

    def render(_):
        print(player.get_transform())
        camera_sensor.render(display)
        hud.render(display)
        pygame.display.flip()

    tele_sim.start()
    tele_sim.add_tick_listener(render)
    tele_sim.add_tick_listener(hud.tick)
    controller.add_player_in_world(player)

    tele_sim.do_simulation(simulation_conf['synchronicity'])

    # exit = False
    # try:
    #     while not exit:
    #         ...
    #         # network_delay.tick()
    #         clock.tick()
    #         exit = tele_world.tick(clock) != 0
    #         # hud.tick(tele_world, player, clock)
    #
    #         camera_sensor.render(display)
    #         hud.render(display)
    #         pygame.display.flip()
    #
    #         # player.tick()
    #         # tele_operator.tick()
    #         # mec.tick()
    #
    #         # command = controller.do_action()
    #         # if command is None:
    #         #     return -1
    #         # player.apply_control(command)
    #
    #         # TeleContext.instance.tick()
    #         # data_collector.tick()
    #         print(player.get_location())
    # # exit = i == 1000 | exit
    #
    # # TODO destroy everything
    # finally:
    #     # network_delay.finish()
    #     pygame.quit()
    #     tele_world.destroy()


if __name__ == '__main__':
    main()
