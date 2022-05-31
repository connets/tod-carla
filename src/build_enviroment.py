from carla import libcarla, Transform, Location, Rotation
import carla
from numpy import random

from src.FolderPath import FolderPath
from src.actor.InfoSimulationActor import PeriodicDataCollectorActor
from src.actor.TeleCarlaSensor import TeleCarlaCameraSensor
from src.network.NetworkChannel import DiscreteNetworkChannel, TcNetworkInterface
import src.utils as utils
from src.utils.Hud import HUD
import pygame


def create_display(player, clock, tele_sim, camera_width, camera_height):
    print("***")
    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode((camera_width, camera_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
    # display.fill((0, 0, 0))
    pygame.display.flip()

    hud = HUD(player, clock, camera_width, camera_height)
    camera_sensor = TeleCarlaCameraSensor(hud, 2.2, camera_width, camera_height)
    player.attach_sensor(camera_sensor)

    def render():
        camera_sensor.render(display)
        hud.render(display)
        pygame.display.flip()

    tele_sim.add_sync_tick_listener(render)
    tele_sim.add_async_tick_listener(hud.tick)

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


def create_data_collector(tele_world, player):
    return PeriodicDataCollectorActor(FolderPath.OUTPUT_RESULTS_PATH + "sensors.csv",
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


def create_network_topology(sync, scenario_conf, player, mec_server, tele_operator):
    backhaul_uplink_delay = scenario_conf['delay']['backhaul']['uplink_extra_delay']
    backhaul_downlink_delay = scenario_conf['delay']['backhaul']['downlink_extra_delay']

    if sync:
        channel_class = DiscreteNetworkChannel
        args = []
    else:
        channel_class = TcNetworkInterface
        args = ['lo']
    vehicle_operator_channel = channel_class(tele_operator,
                                             utils.delay_family_to_func[backhaul_uplink_delay['family']](
                                                 **backhaul_uplink_delay['parameters']), 0.1, *args)
    player.add_channel(vehicle_operator_channel)

    operator_vehicle_channel = channel_class(player,
                                             utils.delay_family_to_func[backhaul_downlink_delay['family']](
                                                 **backhaul_downlink_delay['parameters']), 0.1, *args)
    tele_operator.add_channel(operator_vehicle_channel)
