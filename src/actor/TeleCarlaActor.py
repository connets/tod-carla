from src.network.NetworkNode import NetworkNode


class TeleCarlaActor(NetworkNode):
    def __init__(self, host, port):
        super().__init__(host, port)

    def spawn_in_the_world(self, tele_world):
        ...


import random
import sys
from abc import ABC, abstractmethod
from time import sleep

import carla
from carla import ActorBlueprint, Transform, Location, Rotation, VehicleControl

from src.TeleContext import TeleContext
from src.TeleEvent import tele_event
from src.TeleVehicleState import TeleVehicleState
from src.network.NetworkMessage import InfoUpdateNetworkMessage
from threading import Thread

from src.utils.decorators import needs_member


class TeleCarlaVehicle(TeleCarlaActor):
    def __init__(self, host, port, sync, sending_interval,
                 actor_filter='vehicle.tesla.model3', attrs=None, start_transform=None, modify_vehicle_physics=False):
        super().__init__(host, port)
        self._tele_world = None
        self._sync = sync
        self._sending_interval = sending_interval
        if attrs is None:
            attrs = dict()
        self._actor_filter = actor_filter
        self._attrs = attrs
        self._start_transform = start_transform
        self.model = None
        self._show_vehicle_telemetry = False
        self._modify_vehicle_physics = modify_vehicle_physics
        self.sensors = set()

        self._sending_info_thread = None

    def run(self):
        # self._spawn_in_world(tele_world)
        # self._controller.add_player_in_world(self)
        @tele_event('sending_info_state')
        def daemon_state():

            self.send_message(InfoUpdateNetworkMessage(TeleVehicleState.generate_current_state(self),
                                                       timestamp=self._tele_context.timestamp))
            self._tele_context.schedule(daemon_state, self._sending_interval)

        daemon_state()
        # else:
        #     @tele_event('sending_info_state')
        #     def send_info_state():
        #         while True:
        #             self.send_message(InfoUpdateNetworkMessage(TeleVehicleState.generate_current_state(self),
        #                                                        timestamp=self._tele_context.timestamp))
        #             sleep(self._sending_interval)
        #
        #     self._sending_info_thread = Thread(target=send_info_state)  # non mi piace per nulla :(
        #     self._sending_info_thread.start()

    def attach_sensor(self, tele_carla_sensor):
        self.sensors.add(tele_carla_sensor)

    @needs_member('model')
    def __getattr__(self, *args):
        return self.model.__getattribute__(*args)

    def spawn_in_the_world(self, tele_world):
        self._tele_world = tele_world
        sim_world = tele_world.sim_world
        carla_map = tele_world.carla_map
        blueprint: ActorBlueprint = random.choice(sim_world.get_blueprint_library().filter(self._actor_filter))
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)

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

    @needs_member('_tele_world')
    def receive_instruction_network_message(self, command):
        self._tele_world.apply_sync_command(carla.command.ApplyVehicleControl(self.id, command))

    def quit(self):
        if self._sending_info_thread is not None:
            self._sending_info_thread.exit()
        for sensor in self.sensors:
            sensor.destroy()
        self._tele_world.apply_sync_command(carla.command.DestroyActor(self.id))


class TeleCarlaPedestrian(TeleCarlaActor):

    def __init__(self, host, port, initial_location):
        super().__init__(host, port)
        self._initial_location = initial_location
        self._tele_world = None
        self.model = None

    def spawn_in_the_world(self, tele_world):
        self._tele_world = tele_world
        sim_world = tele_world.sim_world
        blueprint = random.choice(sim_world.get_blueprint_library().filter('*walker.pedestrian*'))
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'false')
        spawn_point = carla.Transform(self._initial_location)

        response = tele_world.apply_sync_command(carla.command.SpawnActor(blueprint, spawn_point))[0]

        self.model = sim_world.get_actor(response.actor_id)
