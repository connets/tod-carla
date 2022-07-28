import abc

from carla import libcarla, Transform, Location, Rotation
import carla
from numpy import random

from src.TeleWorldController import BehaviorAgentTeleWorldAdapterController
from src.actor.TeleCarlaActor import TeleCarlaVehicle
from src.actor.TeleCarlaSensor import TeleCarlaCollisionSensor, TeleCarlaLidarSensor, TeleCarlaCameraSensor
from src.actor.TeleOperator import TeleOperator
from src.args_parse.TeleConfiguration import TeleConfiguration
from src.carla_bridge.TeleWorld import TeleWorld
from src.utils.Hud import HUD
import pygame

from src.utils.decorators import preconditions


class EnvironmentBuilder:

    def __init__(self, seed, carla_world_conf, timestep, actors_conf):
        self.seed = seed

        configuration = TeleConfiguration.instance
        self._carla_server_conf = configuration['carla_server_configuration']
        self._carla_world_conf = configuration.parse_world_conf(carla_world_conf)
        self._carla_actors_conf = configuration.parse_actor_conf(carla_world_conf)
        self.render = self._carla_server_conf['render']

        self.clock = pygame.time.Clock()
        self.timestep = timestep

        self.vehicles = dict()
        self.operators = dict()
        self.other_actors = dict()
        self.tick_listeners = set()

        self.carla_map = self.tele_world = None

    def build(self):
        self._create_tele_world()
        self._create_carla_actors()

        ...

    def _create_tele_world(self):
        host, port, timeout = self._carla_server_conf['host'], self._carla_server_conf['port'], \
                              self._carla_server_conf['timeout']
        world = self._carla_world_conf['world']

        client: libcarla.Client = carla.Client(host, port)
        client.set_timeout(timeout)
        sim_world: carla.World = client.load_world(world)

        settings = sim_world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = self.timestep
        settings.no_rendering_mode = not self.render
        sim_world.apply_settings(settings)
        traffic_manager = client.get_trafficmanager()
        traffic_manager.set_synchronous_mode(True)
        traffic_manager.set_random_device_seed(self.seed)

        client.reload_world(False)  # reload map keeping the world settings
        sim_world.set_weather(carla.WeatherParameters.ClearSunset)

        sim_world.tick()
        self.client, self.sim_world = client, sim_world
        self.carla_map = self.sim_world.get_map()
        self.tele_world = TeleWorld(client)

    def _create_carla_actors(self):
        for vehicle_conf in self._vehicles_conf:
            vehicle_id = vehicle_conf['vehicle_id']
            vehicle_type = vehicle_conf['vehicle_type']
            start_position = self._create_start(vehicle_type.get('start_position'))
            end_location = self._create_destination(vehicle_type.get('end_location'))

            vehicle_attrs = vehicle_type['attrs']
            vehicle = TeleCarlaVehicle(vehicle_type['speed_limit'],
                                       vehicle_type['model'],
                                       vehicle_attrs,
                                       start_transform=start_position,
                                       modify_vehicle_physics=True)
            collisions_sensor = TeleCarlaCollisionSensor()
            vehicle.attach_sensor(collisions_sensor)
            lidar_sensor = TeleCarlaLidarSensor()
            vehicle.attach_sensor(lidar_sensor)
            vehicle.spawn_in_the_world(self.tele_world)
            camera_sensor = TeleCarlaCameraSensor(2.2)
            # TODO change here to attach camera to different actor
            if 'display' in vehicle_conf:
                display_conf = vehicle_conf['display']
                self._create_display(vehicle, display_conf['camera_width'], display_conf['camera_height'],
                                     camera_sensor)

            # TODO handle the situation in which one vehicle has multiple agents
            if 'agents' in vehicle_conf and vehicle['agents']:
                agent_conf = vehicle_conf['agents'][0]
                agent_type = agent_conf['agent_type']
                agent_id = agent_conf['agent_id']

                # TODO change here to allow different agents
                controller = BehaviorAgentTeleWorldAdapterController(agent_type['behavior'],
                                                                     agent_type['sampling_resolution'],
                                                                     start_position, end_location)
                tele_operator = TeleOperator(controller, self._carla_world_conf['time_limit'])
                controller.add_player_in_world(vehicle)
                self.operators[agent_id] = tele_operator

            self.vehicles[vehicle_id] = vehicle

    @preconditions('_vehicle_conf', valid=lambda v: 'display' in v)
    def _create_display(self, player, camera_width, camera_height, camera_sensor):
        pygame.init()
        pygame.font.init()
        display = pygame.display.set_mode((camera_width, camera_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        # display.fill((0, 0, 0))
        pygame.display.flip()

        hud = HUD(player, self.clock, display)
        camera_sensor.add_display(display)

        def render(_):
            camera_sensor.render()
            hud.render()
            pygame.display.flip()

        self.tick_listeners.add(render)
        self.tick_listeners.add(hud.tick)

    def _create_start(self, start_coordinates=None):
        if start_coordinates is not None:
            start_transform = Transform(
                Location(x=start_coordinates['x'], y=start_coordinates['y'], z=start_coordinates['z']),
                Rotation(pitch=start_coordinates['pitch'], yaw=start_coordinates['yaw'],
                         roll=start_coordinates['roll']))
        else:
            carla_map = self.tele_world.carla_map
            spawn_points = carla_map.get_spawn_points()
            start_transform = random.choice(spawn_points) if spawn_points else carla.Transform()
        return start_transform

    def _create_destination(self, end_coordinates=None):
        if end_coordinates is not None:
            destination_location = Location(x=end_coordinates['x'], y=end_coordinates['y'], z=end_coordinates['z'])
        else:
            carla_map = self.tele_world.carla_map
            spawn_points = carla_map.get_spawn_points()
            destination_location = random.choice(spawn_points).location

        return destination_location

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
