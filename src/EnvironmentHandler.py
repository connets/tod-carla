import math
import os
import shutil
import sys

from carla import libcarla, Transform, Location, Rotation
import carla
from numpy import random

from src.FolderPath import FolderPath
from src.TeleOutputWriter import DataCollector
from src.TeleWorldController import BehaviorAgentTeleWorldAdapterController
from src.actor.carla_actor.TeleCarlaActor import TeleCarlaVehicle
from src.actor.carla_actor.TeleCarlaSensor import TeleCarlaCollisionSensor, TeleCarlaLidarSensor, TeleCarlaCameraSensor
from src.actor.external_active_actor.TeleOperator import TeleOperator
from src.actor.external_passive_actor.InfoSimulationActor import PeriodicDataCollectorActor, SimulationRatioActor
from src.actor.external_passive_actor.MovingBackgroundVehicle import MovingBackgroundVehicle
from src.args_parse.TeleConfiguration import TeleConfiguration
from src.carla_bridge.TeleWorld import TeleWorld
from src.utils import utils
from src.utils.Hud import HUD
import pygame
import zerorpc


class CarlaTimeoutError(RuntimeError):
    ...


class EnvironmentHandler:
    class Logger(object):
        def __init__(self, log_file_path):
            self.terminal = sys.stdout
            self.log = open(log_file_path, "a")

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()

        def flush(self):
            # this flush method is needed for python 3 compatibility.
            # this handles the flush command by doing nothing.
            # you might want to specify some extra behavior here.
            self.log.flush()

    def __init__(self):
        self.tele_configuration = TeleConfiguration.instance
        self._simulator_conf = self.tele_configuration['carla_server_configuration']

        self._carla_handler = zerorpc.Client()
        self._carla_handler.connect(
            f"tcp://{self._simulator_conf['carla_server']['host']}:{self._simulator_conf['carla_server']['carla_handler_port']}")


        self.carla_actors = dict()
        self.external_active_actors = dict()
        self.external_passive_actors = set()
        self.obstacle_actors = list()
        self.sudden_obstacle = {
            'main_actor_id': None,
            'max_spawn_distance': None,
            'spawned': False,
            'blueprint': None,
            'transform': None
        }

        self.carla_map = self.tele_world = None

    def launch_carla_server(self):
        while not self._carla_handler.reload_simulator():
            ...

    def add_carla_scenario_config(self, carla_configuration, custom_parameters, run_id):
        self.tele_configuration.parse('carla_configuration', carla_configuration)
        self.tele_configuration.parse('custom_init_parameters', custom_parameters)
        self.tele_configuration['actors'] = []

        self.seed = carla_configuration['seed']
        self.timestep = carla_configuration['carla_timestep']
        # self._actors_settings = carla_configuration['actors']
        self.sim_time_limit = carla_configuration["sim_time_limit"]
        self.sim_time_limit = self.sim_time_limit - 10
        self.run_id = run_id


        carla_world_path = FolderPath.CONFIGURATION_WORLD + custom_parameters['carla_world_configuration'] + '.yaml'
        self._carla_world_conf = self.tele_configuration.parse_conf(carla_world_path)

        self.render = self._simulator_conf['render']

        self._simulation_out_dir = self._simulator_conf['output']['result']['directory'] + self.run_id + '/'
        if os.path.exists(self._simulation_out_dir):
            shutil.rmtree(self._simulation_out_dir)
        os.makedirs(self._simulation_out_dir)
        sys.stdout = sys.stderr = self.Logger(self._simulation_out_dir + 'log.txt')

        self.clock = pygame.time.Clock()



    def world_init_completed(self):
        self.tele_configuration.save_config(self._simulation_out_dir + 'configuration.yaml')
        if 'output' in self._simulator_conf:
            self._create_passive_actors()

    def tick(self):
        self.sudden_obstacle_tick()

        #TODO move to own class
        #self.moving_background.append({'agent': tele_operator, 'actor': vehicle})

    def finish_simulation(self, operator_status):
        finished_file_path = self._simulation_out_dir + 'FINISH_STATUS.txt'
        with open(finished_file_path, 'w') as f:
            f.write(operator_status.name)
        pygame.quit()
        if self.tele_world.is_alive():
            self.tele_world.quit()
            for actor in self.carla_actors.values(): actor.quit()
            for actor in self.external_active_actors.values(): actor.quit()
            for actor in self.external_passive_actors: actor.quit()
            for actor in self.obstacle_actors: actor.destroy()
            settings = self.sim_world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            self.sim_world.apply_settings(settings)
            traffic_manager = self.client.get_trafficmanager()
            traffic_manager.set_synchronous_mode(False)
            self.client.reload_world(False)  # reload map keeping the world settings
            self.client = None

    def close(self):
        self._carla_handler.close_simulator()
        self._carla_handler.close()



    def build_world(self):
        host = self._simulator_conf['carla_server']['host']
        port = self._simulator_conf['carla_server']['carla_simulator_port']
        timeout = self._simulator_conf['carla_server']['timeout']
        world = self._carla_world_conf['world']

        retry_number = self._simulator_conf['carla_server']['retry_count']
        sim_world: carla.World = None
        while sim_world is None and retry_number > 0:
            try:
                client: libcarla.Client = carla.Client(host, port)
                client.set_timeout(timeout)
                sim_world = client.load_world(world, carla.MapLayer.NONE)

            except RuntimeError as e:
                retry_number -= 1

        if sim_world is None:
            raise CarlaTimeoutError()
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

    def create_active_actors(self, actor_id, actor_type, actor_setting):
        #print(actor_setting)
        self.tele_configuration.parse('actors', actor_setting)
        file_path = FolderPath.CONFIGURATION_ACTOR + actor_setting['configuration_id'] + '.yaml'

        actor_conf = self.tele_configuration.parse_conf(file_path)

        route_conf = self.tele_configuration.parse_conf(
            FolderPath.CONFIGURATION_ROUTE + actor_setting['route'] + '.yaml') if 'route' in actor_setting else None
        start_position, end_locations, time_limit = self._create_route(route_conf)

        # TODO change here to allows multiple routes for different agents
        #self.sim_time_limit = self.sim_time_limit - 10 if self.sim_time_limit > 0 else time_limit
        
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
        if self.render and 'camera' in actor_conf:
            display_conf = actor_conf['camera']
            self._create_display(vehicle, display_conf['width'], display_conf['height'], camera_sensor)
        vehicle.attach_sensor(camera_sensor)

        lidar_sensor = TeleCarlaLidarSensor()
        vehicle.attach_sensor(lidar_sensor)
        vehicle.spawn_in_the_world(self.tele_world)

        agent_id = actor_setting['agent_id']

        agent_conf_path = FolderPath.CONFIGURATION_AGENT + actor_setting['agent_configuration'] + '.yaml'
        agent_conf = self.tele_configuration.parse_conf(agent_conf_path)

        # TODO change here to allow different agents
        controller = BehaviorAgentTeleWorldAdapterController(agent_conf['behavior'],
                                                             agent_conf['sampling_resolution'],
                                                             start_position.location, end_locations)
        
        controller.add_player_in_world(vehicle)
        anchor_points = controller.get_trajectory()

        optimal_trajectory_collector = DataCollector(
            f"{self._simulation_out_dir}optimal_trajectory_{agent_id}.csv")
        optimal_trajectory_collector.write('location_x', 'location_y', 'location_z')
        for point in anchor_points:
            optimal_trajectory_collector.write(point['x'], point['y'], point['z'])

        if actor_conf['mode'] == 'active':
            tele_operator = TeleOperator(controller)
            self.external_active_actors[agent_id] = tele_operator
            self.carla_actors[actor_id] = vehicle
        elif actor_conf['mode'] == 'passive':
            self.external_passive_actors.add(MovingBackgroundVehicle(self.timestep, controller, vehicle))
        else:
            raise RuntimeError()

        
        return vehicle

    def _create_passive_actors(self):
        tele_world = self.tele_world

        for actor_id, carla_actor in self.carla_actors.items():
            actor = PeriodicDataCollectorActor(
                self._simulator_conf['output']['result']['interval'],
                self._simulation_out_dir + 'sensor_' + actor_id + '.csv',
                {'timestamp': lambda: utils.format_number(tele_world.timestamp.elapsed_seconds, 5),
                 'velocity_x': lambda: utils.format_number(carla_actor.get_velocity().x, 8),
                 'velocity_y': lambda: utils.format_number(carla_actor.get_velocity().y, 8),
                 'velocity_z': lambda: utils.format_number(carla_actor.get_velocity().z, 8),
                 'acceleration_x': lambda: utils.format_number(carla_actor.get_acceleration().x, 5),
                 'acceleration_y': lambda: utils.format_number(carla_actor.get_acceleration().y, 5),
                 'acceleration_z': lambda: utils.format_number(carla_actor.get_acceleration().z, 5),
                 'location_x': lambda: utils.format_number(carla_actor.get_location().x, 8),
                 'location_y': lambda: utils.format_number(carla_actor.get_location().y, 8),
                 'location_z': lambda: utils.format_number(carla_actor.get_location().z, 8),
                 'rotation_pitch': lambda: utils.format_number(carla_actor.get_transform().rotation.pitch, 8),
                 'rotation_yaw': lambda: utils.format_number(carla_actor.get_transform().rotation.yaw, 8),
                 'rotation_roll': lambda: utils.format_number(carla_actor.get_transform().rotation.roll, 8),
                 # 'altitude': lambda: round(gnss_sensor.altitude, 5),
                 # 'longitude': lambda: round(gnss_sensor.longitude, 5),
                 # 'latitude': lambda: round(gnss_sensor.latitude, 5),
                 'throttle': lambda: utils.format_number(carla_actor.get_control().throttle, 5),
                 'steer': lambda: utils.format_number(carla_actor.get_control().steer, 5),
                 'brake': lambda: utils.format_number(carla_actor.get_control().brake, 5),
                 #'visible_vehicles': lambda: len(carla_actor.generate_status().visible_vehicles)
                 'visible_vehicles': lambda: carla_actor.get_number_visible_vehicles(),
                 'obstacle_distance': lambda: utils.format_number(carla_actor.get_location().distance(self.obstacle_actors[0].get_location()), 3) if len(self.obstacle_actors) > 0 else ''
                 })
            self.external_passive_actors.add(actor)
        simulation_ratio_actor = SimulationRatioActor(1, self._simulation_out_dir + 'simulation_ratio.txt',
                                                      lambda: tele_world.timestamp.elapsed_seconds)
        self.external_passive_actors.add(simulation_ratio_actor)

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
            #mandatory part
            origin = route_conf.pop('origin')
            destinations = route_conf.pop('destinations')
            start_transform = Transform(
                Location(x=origin['x'], y=origin['y'], z=origin['z']),
                Rotation(pitch=origin['pitch'], yaw=origin['yaw'],
                         roll=origin['roll']))
            destination_locations = []
            for destination in destinations:
                destination_locations.append(Location(x=destination['x'], y=destination['y'],
                                                      z=destination['z']))

            time_limit = route_conf.pop('time_limit')

            #optional part
            for key in route_conf:
                name = f'_route_handle_{key}'
                if hasattr(self, name):
                    getattr(self, name)(route_conf[key])
        else:
            carla_map = self.tele_world.carla_map
            spawn_points = carla_map.get_spawn_points()
            start_transform = random.choice(spawn_points) if spawn_points else carla.Transform()
            destination_locations = [random.choice(spawn_points).location]
            time_limit = sys.maxsize
        return start_transform, destination_locations, time_limit
    
    def _route_handle_obstacles(self, obstacles):
        sim_world = self.sim_world
        for obstacle in obstacles:
            blueprint: carla.ActorBlueprint = random.choice(sim_world.get_blueprint_library().filter(obstacle['filter']))
            transform = carla.Transform(Location(x=obstacle['spawn']['x'], y=obstacle['spawn']['y'], z=obstacle['spawn']['z']), Rotation(pitch=obstacle['spawn']['pitch'], yaw=obstacle['spawn']['yaw'], roll=obstacle['spawn']['roll']))
            actor: carla.Actor = sim_world.spawn_actor(blueprint, transform)
            if 'autopilot' in obstacle:
                actor.set_autopilot(obstacle['autopilot'])
            
            self.obstacle_actors.append(actor)
            #print(actor)

    #adds sudden obstacle to self config
    def _route_handle_sudden_obstacle(self, sudden_obstacle):
        sim_world = self.sim_world

        self.sudden_obstacle['blueprint']: carla.ActorBlueprint = random.choice(sim_world.get_blueprint_library().filter(sudden_obstacle['filter']))
        self.sudden_obstacle['transform'] = carla.Transform(Location(x=sudden_obstacle['spawn']['x'], y=sudden_obstacle['spawn']['y'], z=sudden_obstacle['spawn']['z']), Rotation(pitch=sudden_obstacle['spawn']['pitch'], yaw=sudden_obstacle['spawn']['yaw'], roll=sudden_obstacle['spawn']['roll']))
        self.sudden_obstacle['main_actor_id'] = sudden_obstacle['main_actor_id']
        self.sudden_obstacle['max_spawn_distance'] = sudden_obstacle['max_spawn_distance']
        
    # Spawns sudden obstacle if main actor's location is close enough to spawn point
    def sudden_obstacle_tick(self):
        #TODO move to own class without relying on a dict
        if self.sudden_obstacle['spawned'] == False and self.sudden_obstacle['main_actor_id'] is not None and self.carla_actors[self.sudden_obstacle['main_actor_id']].get_location().distance(self.sudden_obstacle['transform'].location) < self.sudden_obstacle['max_spawn_distance']:
            actor: carla.Actor = self.sim_world.spawn_actor(self.sudden_obstacle['blueprint'], self.sudden_obstacle['transform'])
        
            self.obstacle_actors.append(actor)
            self.sudden_obstacle['spawned'] = True
            #print(actor)

    def _route_handle_spectator(self, spectator_coords):
        sim_world = self.sim_world
        # Retrieve the spectator object
        spectator = sim_world.get_spectator()
        # Get the location and rotation of the spectator from conf
        transform = carla.Transform(Location(x=spectator_coords['x'], y=spectator_coords['y'], z=spectator_coords['z']), Rotation(pitch=spectator_coords['pitch'], yaw=spectator_coords['yaw'], roll=spectator_coords['roll']))
        spectator.set_transform(transform)
