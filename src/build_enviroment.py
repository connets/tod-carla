import abc
import sys

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

    def __init__(self, seed, carla_world_conf_path, timestep, actors_settings):
        self.seed = seed

        self.tele_configuration = TeleConfiguration.instance
        self._carla_server_conf = self.tele_configuration['carla_server_configuration']
        self._carla_world_conf = self.tele_configuration.parse_world_conf(carla_world_conf_path)
        self._actors_settings = actors_settings
        self.render = self._carla_server_conf['render']

        self.clock = pygame.time.Clock()
        self.timestep = timestep

        self.actors = dict()
        self.operators = dict()

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
        self.tele_world = TeleWorld(client, self.clock)

    def _create_carla_actors(self):
        for actor_setting in self._actors_settings:
            actor_id = actor_setting['actor_id']
            actor_conf = self.tele_configuration.parse_actor_conf(actor_setting['actor_configuration'])
            start_position, end_location, time_limit = self._create_route(actor_setting.get('route'))

            vehicle_attrs = actor_setting.get('attrs')
            vehicle = TeleCarlaVehicle(actor_conf['speed_limit'],
                                       actor_conf['model'],
                                       vehicle_attrs,
                                       start_transform=start_position,
                                       modify_vehicle_physics=True)
            collisions_sensor = TeleCarlaCollisionSensor()
            vehicle.attach_sensor(collisions_sensor)
            camera_sensor = TeleCarlaCameraSensor(2.2)
            # TODO change here to attach camera to different actor
            if 'camera' in actor_conf:
                display_conf = actor_conf['camera']
                self._create_display(vehicle, display_conf['width'], display_conf['height'], camera_sensor)
            vehicle.attach_sensor(camera_sensor)

            lidar_sensor = TeleCarlaLidarSensor()
            vehicle.attach_sensor(lidar_sensor)
            vehicle.spawn_in_the_world(self.tele_world)

            # TODO handle the situation in which one vehicle has multiple agents
            if 'agents' in actor_setting and actor_setting['agents']:
                print("****"*7)
                agent_settings = actor_setting['agents'][0]
                agent_id = agent_settings['agent_id']
                agent_conf = self.tele_configuration.parse_agent_conf(agent_settings['agent_configuration'])

                # TODO change here to allow different agents
                controller = BehaviorAgentTeleWorldAdapterController(agent_conf['behavior'],
                                                                     agent_conf['sampling_resolution'],
                                                                     start_position.location, end_location)
                tele_operator = TeleOperator(controller, time_limit)
                controller.add_player_in_world(vehicle)
                self.operators[agent_id] = tele_operator

            self.actors[actor_id] = vehicle

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

        self.tele_world.add_tick_callback(render)
        self.tele_world.add_tick_callback(hud.tick)

    def _create_route(self, route_conf=None):
        if route_conf is not None:
            route_conf = self.tele_configuration.parse_route_conf(route_conf)
            start_transform = Transform(
                Location(x=route_conf['origin']['x'], y=route_conf['origin']['y'], z=route_conf['origin']['z']),
                Rotation(pitch=route_conf['origin']['pitch'], yaw=route_conf['origin']['yaw'],
                         roll=route_conf['origin']['roll']))
            destination_location = Location(x=route_conf['destination']['x'], y=route_conf['destination']['y'],
                                            z=route_conf['destination']['z'])
            time_limit = route_conf['time_limit']
        else:
            carla_map = self.tele_world.carla_map
            spawn_points = carla_map.get_spawn_points()
            start_transform = random.choice(spawn_points) if spawn_points else carla.Transform()
            destination_location = random.choice(spawn_points).location
            time_limit = sys.maxsize
        return start_transform, destination_location, time_limit
