import random
import sys
from abc import ABC, abstractmethod
from time import sleep

import carla
from carla import ActorBlueprint, Transform, Location, Rotation

from src.TeleContext import TeleContext
from src.TeleVehicleState import TeleVehicleState
from src.actor.TeleCarlaActor import TeleCarlaActor
from src.network.NetworkMessage import InfoUpdateNetworkMessage
from threading import Thread

from src.utils.decorators import needs_member


class TeleCarlaVehicle(TeleCarlaActor):
    def __init__(self, host, port, sync, sending_interval,
                 actor_filter='vehicle.tesla.model3', attrs=None, start_transform=None, modify_vehicle_physics=False):
        super().__init__(host, port)
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
        self._sensors = set()

    def run(self, tele_world):
        # self._spawn_in_world(tele_world)
        # self._controller.add_player_in_world(self)
        if self._sync:
            def daemon_state():
                print("**********")

                self.send_message(InfoUpdateNetworkMessage(TeleVehicleState.generate_current_state(self),
                                                           timestamp=self._tele_context.timestamp))
                self._tele_context.schedule(daemon_state, self._sending_interval)

            daemon_state()
        else:
            def send_info_state():
                while True:
                    self.send_message(InfoUpdateNetworkMessage(TeleVehicleState.generate_current_state(self),
                                                               timestamp=self._tele_context.timestamp))
                    sleep(self._sending_interval)

            sending_info_thread = Thread(target=send_info_state)  # non mi piace per nulla :(
            sending_info_thread.start()

    def attach_sensor(self, tele_carla_sensor):
        self._sensors.add(tele_carla_sensor)

    @needs_member('model')
    def __getattr__(self, *args):
        return self.model.__getattribute__(*args)

    def spawn_in_the_world(self, tele_world):
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
            self.model = sim_world.try_spawn_actor(blueprint, self._start_transform)
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
            self.model = sim_world.try_spawn_actor(blueprint, spawn_point)
            if self._modify_vehicle_physics:
                self.modify_vehicle_physics()
        self.set_light_state(carla.VehicleLightState.Position)
        sim_world.tick()

        for sensor in self._sensors:
            sensor.spawn_in_the_world(self)

    def modify_vehicle_physics(self):
        try:
            physics_control = self.get_physics_control()
            physics_control.use_sweep_wheel_collision = True
            self.apply_physics_control(physics_control)
        except Exception:
            pass

    def receive_instruction_network_message(self, command):
        self.apply_control(command)
