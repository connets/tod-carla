import abc
import random
import sys
from abc import abstractmethod

import carla
from carla import ActorBlueprint, VehicleControl

from src.actor.TeleCarlaSensor import TeleCarlaCameraSensor, TeleCarlaLidarSensor
from src.core.TeleEvent import tele_event
from src.communication.TeleVehicleState import TeleVehicleState
from src.communication.NetworkMessage import InfoUpdateMessage
import lib.camera_visibility.carla_vehicle_annotator as cva

from src.utils.decorators import preconditions


class TeleCarlaActor(abc.ABC):

    def __init__(self):
        self.model = None

    @abstractmethod
    def spawn_in_the_world(self, tele_world):
        ...

    @abstractmethod
    def generate_status(self):
        ...

    @preconditions('model')
    def __getattr__(self, *args):
        return self.model.__getattribute__(*args)


class TeleCarlaVehicle(TeleCarlaActor):
    def __init__(self, speed_limit, actor_filter='vehicle.tesla.model3', attrs=None, start_transform=None,
                 modify_vehicle_physics=False):

        super().__init__()
        self._tele_world = None
        self._speed_limit = speed_limit if speed_limit != 'auto' else None
        if attrs is None:
            attrs = dict()
        self._actor_filter = actor_filter
        self._attrs = attrs
        self._start_transform = start_transform
        self._show_vehicle_telemetry = False
        self._modify_vehicle_physics = modify_vehicle_physics
        self.sensors = set()

    def get_speed_limit(self):
        return self._speed_limit if self._speed_limit is not None else self.model.get_speed_limit() / 3.6

    def generate_status(self):
        camera_sensor = self.get_sensor_by_class(TeleCarlaCameraSensor)
        lidar_sensor = self.get_sensor_by_class(TeleCarlaLidarSensor)
        lidar_image = lidar_sensor.image if lidar_sensor is not None else None
        visible_vehicles, visible_pedestrians = [], []
        snapshot = self._tele_world.get_snapshot()
        if lidar_image and camera_sensor:
            vehicles_raw = [v for v in self._tele_world.sim_world.get_actors().filter('vehicle.*') if
                            v.id != self.id]
            # does it need snap_processing filter?
            # vehicles = cva.snap_processing(vehicles_raw, snap)
            if vehicles_raw:
                vehicles_res, _ = cva.auto_annotate_lidar(vehicles_raw, camera_sensor.sensor, lidar_image)
                visible_vehicles = vehicles_res['vehicles']
            pedestrian_raw = self._tele_world.sim_world.get_actors().filter('*walker.pedestrian*')
            if pedestrian_raw:
                pedestrians_res, _ = cva.auto_annotate_lidar(pedestrian_raw, camera_sensor.sensor, lidar_image)
                visible_pedestrians = pedestrians_res['vehicles']
        return TeleVehicleState.generate_vehicle_state(snapshot.timestamp, self, visible_vehicles, visible_pedestrians)

    def get_sensor_by_class(self, cls):
        return next(iter([s for s in self.sensors if isinstance(s, cls)]), None)

    def attach_sensor(self, tele_carla_sensor):
        self.sensors.add(tele_carla_sensor)

    def spawn_in_the_world(self, tele_world):
        self._tele_world = tele_world
        sim_world = tele_world.sim_world
        carla_map = tele_world.carla_map
        blueprint: ActorBlueprint = random.choice(sim_world.get_blueprint_library().filter(self._actor_filter))
        # if blueprint.has_attribute('color'):
        #     color = random.choice(blueprint.get_attribute('color').recommended_values)
        #     blueprint.set_attribute('color', color)

        if blueprint.has_attribute('speed'):
            self.player_max_speed = float(blueprint.get_attribute('speed').recommended_values[1])
            self.player_max_speed_fast = float(blueprint.get_attribute('speed').recommended_values[2])

        for key, value in self._attrs.items():
            blueprint.set_attribute(key, value)

        self.model = None
        if self._start_transform is not None:
            response = tele_world.apply_sync_command(carla.command.SpawnActor(blueprint, self._start_transform))[0]
            self.model = sim_world.get_actor(response.actor_id)
            if self.model is None:
                print("Error in spawning car in:", self._start_transform)

        while self.model is None:
            if not carla_map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)
            spawn_points = carla_map.get_spawn_points()
            spawn_point = spawn_points[1]
            # spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            # x=29.911945, y=-2.026154, z=0.000000
            # spawn_point = Transform(Location(x=299.399994, y=133.240036, z=0.300000), Rotation(pitch=0.000000, yaw=-0.000092, roll=0.000000))
            response = tele_world.apply_sync_command(carla.command.SpawnActor(blueprint, spawn_point))[0]

            self.model = sim_world.get_actor(response.actor_id)

            if self._modify_vehicle_physics:
                physics_control = self.get_physics_control()
                physics_control.use_sweep_wheel_collision = True
                self._tele_world.apply_sync_command(carla.command.ApplyVehiclePhysicsControl(self.id, physics_control))
        self._tele_world.apply_sync_command(
            carla.command.SetVehicleLightState(self.id, carla.VehicleLightState.Position))
        # Per far si che si parta da una stessa situazione, necessario?
        self._tele_world.apply_sync_command(carla.command.ApplyVehicleControl(self.id, VehicleControl()))
        sim_world.tick()

        for sensor in self.sensors:
            sensor.attach_to_actor(tele_world, self)

    @preconditions('_tele_world')
    def receive_instruction_network_message(self, command):
        self._tele_world.apply_sync_command(carla.command.ApplyVehicleControl(self.id, command))

    def quit(self):
        for sensor in self.sensors:
            sensor.destroy()
        self._tele_world.apply_sync_command(carla.command.DestroyActor(self.id))

    def done(self, timestamp):
        return all(sensor.done(timestamp) for sensor in self.sensors)


class CarlaOmnetTeleCarlaVehicle(TeleCarlaVehicle):
    ...


class TeleCarlaPedestrian(TeleCarlaActor):

    def __init__(self, initial_location):
        super().__init__()
        self._initial_location = initial_location
        self._tele_world = None

    def spawn_in_the_world(self, tele_world):
        self._tele_world = tele_world
        sim_world = tele_world.sim_world
        blueprint = random.choice(sim_world.get_blueprint_library().filter('*walker.pedestrian*'))
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'false')
        spawn_point = carla.Transform(self._initial_location)

        response = tele_world.apply_sync_command(carla.command.SpawnActor(blueprint, spawn_point))[0]

        self.model = sim_world.get_actor(response.actor_id)

    def generate_status(self):
        pass
