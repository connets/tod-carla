import abc

from carla import libcarla, Transform, Location, Rotation
import carla
from numpy import random

from lib.carla_omnet.CarlaOmnetManager import CarlaOmnetManager
from src.FolderPath import FolderPath
from src.TeleOutputWriter import DataCollector
from src.TeleWorldController import BehaviorAgentTeleWorldAdapterController, KeyboardTeleWorldAdapterController
from src.actor.InfoSimulationActor import PeriodicDataCollectorActor
from src.carla_bridge.TeleWorld import TeleWorld
from src.communication.NetworkChannel import TODNetworkChannel, CarlaOmnetNetworkChannel
import src.utils as utils
from src.core.Simulator import TODSimulator, CarlaOmnetSimulator
from src.utils.Hud import HUD
import pygame


class EnvironmentBuilder:

    def __init__(self, simulation_conf, scenario_conf):
        self.simulation_conf = simulation_conf
        self.scenario_conf = scenario_conf

        self.clock = pygame.time.Clock()
        self.render = simulation_conf['render'] or scenario_conf['controller']['type'] == 'manual'
        self.carla_map = self.tele_world = self.start_transform = self.destination_location = None

    def build(self):
        self._create_tele_world()

        route_factory = EnvironmentBuilder.PreDefinedRouteFactory(
            self.scenario_conf['route']) if 'route' in self.scenario_conf else EnvironmentBuilder.RandomlyRouteFactory(
            self.carla_map)
        self.start_transform, self.destination_location = route_factory.create_route()

        ...

    def _create_tele_world(self):

        host, port, timeout, world, seed, time_step = self.simulation_conf['host'], self.simulation_conf['port'], \
                                                      self.simulation_conf['timeout'], self.scenario_conf['world'], \
                                                      self.simulation_conf['seed'], \
                                                      self.simulation_conf['simulation_time_step']

        client: libcarla.Client = carla.Client(host, port)
        client.set_timeout(timeout)
        sim_world: carla.World = client.load_world(world)

        settings = sim_world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = time_step
        settings.no_rendering_mode = not self.render
        sim_world.apply_settings(settings)
        traffic_manager = client.get_trafficmanager()
        traffic_manager.set_synchronous_mode(True)
        traffic_manager.set_random_device_seed(seed)

        client.reload_world(False)  # reload map keeping the world settings
        sim_world.set_weather(carla.WeatherParameters.ClearSunset)

        sim_world.tick()
        self.client, self.sim_world = client, sim_world
        self.carla_map = self.sim_world.get_map()
        self.tele_world = TeleWorld(client)

    def _create_route(self, tele_world, scenario_conf):
        carla_map = tele_world.carla_map
        if 'route' in scenario_conf:

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

    def create_tele_world(self):
        ...

    def create_controller(self):
        ...

    class RouteFactory(abc.ABC):
        @abc.abstractmethod
        def create_route(self):
            ...

    class PreDefinedRouteFactory(RouteFactory):

        def __init__(self, route_conf):
            self._route_conf = route_conf

        def create_route(self):
            start_transform = Transform(
                Location(x=self._route_conf['start']['x'], y=self._route_conf['start']['y'],
                         z=self._route_conf['start']['z']),
                Rotation(pitch=self._route_conf['start']['pitch'],
                         yaw=self._route_conf['start']['yaw'],
                         roll=self._route_conf['start']['roll']))
            destination_location = Location(x=self._route_conf['end']['x'],
                                            y=self._route_conf['end']['y'],
                                            z=self._route_conf['end']['z'])

            return start_transform, destination_location

    class RandomlyRouteFactory(RouteFactory):
        def __init__(self, carla_map):
            self._carla_map = carla_map

        def create_route(self):
            spawn_points = self._carla_map.get_spawn_points()
            start_transform = random.choice(spawn_points) if spawn_points else carla.Transform()
            destination_location = random.choice(spawn_points).location
            return start_transform, destination_location


def create_display(player, clock, tele_sim, camera_width, camera_height, camera_sensor, output_path=None):
    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode((camera_width, camera_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
    # display.fill((0, 0, 0))
    pygame.display.flip()

    hud = HUD(player, clock, display)
    camera_sensor.add_display(display, output_path)

    def render(_):
        camera_sensor.render()
        hud.render()
        pygame.display.flip()

    tele_sim.add_tick_listener(render)
    tele_sim.add_tick_listener(hud.tick)

    return display


def create_sim_world(host, port, timeout, world, seed, render, time_step):
    client: libcarla.Client = carla.Client(host, port)
    client.set_timeout(timeout)
    sim_world: carla.World = client.load_world(world)

    settings = sim_world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = time_step
    settings.no_rendering_mode = not render
    sim_world.apply_settings(settings)
    traffic_manager = client.get_trafficmanager()
    traffic_manager.set_synchronous_mode(True)
    traffic_manager.set_random_device_seed(seed)

    client.reload_world(False)  # reload map keeping the world settings
    sim_world.set_weather(carla.WeatherParameters.ClearSunset)

    sim_world.tick()
    # env_objs = sim_world.get_environment_objects(carla.CityObjectLabel.Any)
    # building_01 = env_objs[0]
    # building_02 = env_objs[1]
    # objects_to_toggle = {building_01.id, building_02.id}
    #
    # # Toggle buildings off
    # sim_world.enable_environment_objects([o.id for o in env_objs], True)

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
                                       'velocity_x': lambda: utils.format_number(player.get_velocity().x, 8),
                                       'velocity_y': lambda: utils.format_number(player.get_velocity().y, 8),
                                       'velocity_z': lambda: utils.format_number(player.get_velocity().z, 8),
                                       'acceleration_x': lambda: utils.format_number(
                                           player.get_acceleration().x, 5),
                                       'acceleration_y': lambda: utils.format_number(
                                           player.get_acceleration().y, 5),
                                       'acceleration_z': lambda: utils.format_number(
                                           player.get_acceleration().z, 5),
                                       'location_x': lambda: utils.format_number(player.get_location().x, 8),
                                       'location_y': lambda: utils.format_number(player.get_location().y, 8),
                                       'location_z': lambda: utils.format_number(player.get_location().z, 8),
                                       # 'altitude': lambda: round(gnss_sensor.altitude, 5),
                                       # 'longitude': lambda: round(gnss_sensor.longitude, 5),
                                       # 'latitude': lambda: round(gnss_sensor.latitude, 5),
                                       # 'throttle': lambda: round(player.get_control().throttle, 5),
                                       # 'steer': lambda: round(player.get_control().steer, 5),
                                       # 'brake': lambda: round(player.get_control().brake, 5)
                                       }, 0.005)


def create_simulator_and_network_topology(network_conf, tele_world, clock, player, mec_server, tele_operator):
    if network_conf['type'] == 'tod':
        tele_sim = TODSimulator(tele_world, clock)

        backhaul_uplink_delay = network_conf['backhaul']['uplink_extra_delay']
        backhaul_downlink_delay = network_conf['backhaul']['downlink_extra_delay']

        vehicle_operator_channel = TODNetworkChannel(tele_operator,
                                                     utils.delay_family_to_func[backhaul_uplink_delay['family']](
                                                         **backhaul_uplink_delay['parameters']), 0.1)
        operator_vehicle_channel = TODNetworkChannel(player,
                                                     utils.delay_family_to_func[backhaul_downlink_delay['family']](
                                                         **backhaul_downlink_delay['parameters']), 0.1)
    elif network_conf['type'] == 'carla_omnet':
        vehicle_operator_channel = CarlaOmnetNetworkChannel(tele_operator)
        operator_vehicle_channel = CarlaOmnetNetworkChannel(player)
        carla_omnet_manager = CarlaOmnetManager(network_conf['protocol'], network_conf['port'],
                                                network_conf['connection_timeout'], network_conf['timeout'],
                                                lambda: "2")  # player.get_location())
        tele_sim = CarlaOmnetSimulator(tele_world, clock, carla_omnet_manager)
        carla_omnet_manager.add_default_action(1, player._send_message)  # TODO sucks!

    else:
        raise RuntimeError("Network type not valid")

    player.add_channel(vehicle_operator_channel)
    tele_operator.add_channel(operator_vehicle_channel)

    return tele_sim


def apply_god_changes(tele_world, player, controller):
    optimal_trajectory_collector = DataCollector(FolderPath.OUTPUT_LOG_PATH + 'commands.csv')

    optimal_trajectory_collector.write('current_timestamp', 'timestamp_state',
                                       'current_location_x', 'current_location_y',
                                       'state_location_x', 'state_location_y',
                                       'current_velocity_x', 'current_velocity_y', 'current_velocity_z',
                                       'state_velocity_x', 'state_velocity_y', 'state_velocity_z',
                                       )

    def on_calc_instruction(run_step):
        def on_calc_aux(*args, **kwargs):
            last_available_state = controller.carla_agent._last_vehicle_state
            optimal_trajectory_collector.write(tele_world.timestamp.elapsed_seconds,
                                               last_available_state.timestamp.elapsed_seconds,
                                               player.get_location().x, player.get_location().y,
                                               last_available_state.get_location().x,
                                               last_available_state.get_location().y,
                                               utils.format_number(player.get_velocity().x, 8),
                                               utils.format_number(player.get_velocity().y, 8),
                                               utils.format_number(player.get_velocity().z, 8),
                                               utils.format_number(last_available_state.get_velocity().x, 8),
                                               utils.format_number(last_available_state.get_velocity().y, 8),
                                               utils.format_number(last_available_state.get_velocity().z, 8),
                                               )
            return run_step(*args, **kwargs)

        return on_calc_aux

    controller.carla_agent.run_step = on_calc_instruction(controller.carla_agent.run_step)
