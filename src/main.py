import carla
import pygame
from carla import libcarla, Transform, Location, Rotation

from src.TeleLogger import TeleLogger
from src.TeleScheduler import TeleScheduler
from src.actor.TeleMEC import TeleMEC
from src.actor.TeleOperator import TeleOperator
from src.actor.TeleVehicle import TeleVehicle
from src.actor.TeleSensor import TeleCameraSensor, TeleGnssSensor
from src.args_parse import my_parser
from src.carla_bridge.TeleWorld import TeleWorld
from src.folder_path import OUT_PATH
from src.network.NetworkChannel import TcNetworkInterface, DiscreteNetworkChannel
from src.utils.PeriodicDataCollector import PeriodicDataCollector
from src.utils.Hud import HUD
from src.TeleWorldController import BehaviorAgentTeleWorldController, BasicAgentTeleWorldController
from src.utils.distribution_utils import delay_family_to_func
from src.utils.utils import find_free_port


def parse_configurations():
    res = dict()
    conf_files = my_parser.parse_configuration_files()
    res['carla_server_conf'] = my_parser.parse_carla_server_args(conf_files['carla_server_file'])
    res['carla_simulation_conf'] = my_parser.parse_carla_simulation_args(conf_files['carla_simulation_file'])
    return res


def create_display(carla_simulation_conf):
    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode((carla_simulation_conf['camera.width'], carla_simulation_conf['camera.height']),
                                      pygame.HWSURFACE | pygame.DOUBLEBUF)
    display.fill((0, 0, 0))
    pygame.display.flip()
    return display


def create_sim_world(carla_server_conf, carla_simulation_conf):
    client: libcarla.Client = carla.Client(carla_server_conf['host'], carla_server_conf['port'])
    client.set_timeout(carla_server_conf['timeout'])
    sim_world: carla.World = client.load_world(carla_simulation_conf['world'])
    return sim_world


def main():
    """
    get configurations for simulation:
    - carla_server_file (default: configuration/default_server.yaml),
    - carla_simulation_file(default: configuration/default_simulation_curve.yaml)
    """

    TeleLogger()
    configurations = parse_configurations()
    carla_server_conf = configurations['carla_server_conf']
    carla_simulation_conf = configurations['carla_simulation_conf']

    display = create_display(carla_simulation_conf)

    sim_world = create_sim_world(carla_server_conf, carla_simulation_conf)

    def elapsed_seconds():
        return sim_world.get_snapshot().timestamp.elapsed_seconds * 1000

    TeleScheduler(elapsed_seconds)

    start_position = Transform(
        Location(x=carla_simulation_conf['route.start.x'], y=carla_simulation_conf['route.start.y'],
                 z=carla_simulation_conf['route.start.z']),
        Rotation(pitch=carla_simulation_conf['route.start.pitch'], yaw=carla_simulation_conf['route.start.yaw'],
                 roll=carla_simulation_conf['route.start.roll']))
    destination_position = Location(x=carla_simulation_conf['route.end.x'], y=carla_simulation_conf['route.end.y'],
                                    z=carla_simulation_conf['route.end.z'])

    # traffic_manager = client.get_trafficmanager()

    hud = HUD(carla_simulation_conf['camera.width'], carla_simulation_conf['camera.height'])
    tele_world: TeleWorld = TeleWorld(sim_world, carla_simulation_conf, hud)

    player_attrs = {'role_name': 'hero'}
    player = TeleVehicle('localhost', 28007, tele_world, carla_simulation_conf['vehicle_player'], '1', player_attrs,
                         start_position=start_position,
                         modify_vehicle_physics=True)

    camera_sensor = TeleCameraSensor('localhost', find_free_port(), player, hud, 2.2, 1280, 720)

    # controller = BehaviorAgentTeleWorldController()  # TODO change here
    controller = BehaviorAgentTeleWorldController('normal', destination_position)  # TODO change here
    controller.add_player_in_world(player)
    tele_operator = TeleOperator('localhost', find_free_port(), tele_world, controller)
    mec = TeleMEC('localhost', find_free_port(), tele_world)
    vehicle_operator_channel = DiscreteNetworkChannel(tele_operator, elapsed_seconds,
                                                      delay_family_to_func['uniform'](1, 2), 1000)
    player.add_channel(vehicle_operator_channel)
    operator_vehicle_channel = DiscreteNetworkChannel(player, elapsed_seconds,
                                                      delay_family_to_func['uniform'](1, 2), 1000)
    tele_operator.add_channel(operator_vehicle_channel)
    player.start(1000, True)
    # tele_world.add_sensor(camera_manager, player)

    # controller = KeyboardTeleWorldController(camera_manager)  # TODO change here
    # tele_world.add_controller(controller)

    # gnss_sensor = TeleGnssSensor()
    # tele_world.add_sensor(gnss_sensor, player)

    tele_world.start()
    clock = pygame.time.Clock()

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

    data_collector.add_interval_logging(lambda: tele_world.timestamp.elapsed_seconds, 0.1)
    # network_delay = TcNetworkInterface(delay_family_to_func['constant'](5), lambda: round(tele_world.timestamp.elapsed_seconds, 5),
    #                                    1, 'valecislavale')

    exit = False
    # network_delay.start()

    try:
        while not exit:
            ...
            # network_delay.tick()
            clock.tick()
            exit = tele_world.tick(clock) != 0
            player.tick()
            tele_operator.tick()
            mec.tick()

            TeleScheduler.instance.tick()
            camera_sensor.render(display)
            pygame.display.flip()
            # data_collector.tick()
            # print(tele_world.timestamp)
    # exit = i == 1000 | exit

    # TODO destroy everything
    finally:
        # network_delay.finish()
        pygame.quit()
        tele_world.destroy()


if __name__ == '__main__':
    main()
