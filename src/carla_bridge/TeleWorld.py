import random
import sys
import threading

import carla
from carla import libcarla

from src.actor.TeleCarlaSensor import TeleCarlaRenderingSensor
from src.utils.carla_utils import find_weather_presets
from carla.libcarla import World


class TeleWorld:
    """ Class representing the surrounding environment """

    def __init__(self, client: libcarla.Client, sync):
        """Constructor method"""

        self.client = client
        self.sim_world: World = self.client.get_world()
        self._sync = sync
        self._last_snapshot: carla.WorldSnapshot = self.sim_world.get_snapshot()

        builds = self.sim_world.get_environment_objects(carla.CityObjectLabel.Buildings)
        objects_to_toggle = {build.id for build in builds}
        self.sim_world.enable_environment_objects(objects_to_toggle, False)

        # if self._sync:
        #     self.sync = True
        #     # settings = self.sim_world.get_settings()
        #     # settings.synchronous_mode = True
        #     # settings.fixed_delta_seconds = float(self._carla_conf['time_step'] / 1000)
        #     # self.sim_world.apply_settings(settings)
        #     # traffic_manager.set_synchronous_mode(True)
        # else:
        #     self.sync = False
        try:
            self.carla_map = self.sim_world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)

        # for spawn_point in self.carla_map.get_spawn_points():
        #     if abs(396.984039 - spawn_point.location.x) < 6:
        #         print(spawn_point)

        self.vehicles = []

        self._tick_callbacks = set()

        def call_on_tick(timestamp):
            for callback in self._tick_callbacks:
                callback(timestamp)

        self.sim_world.on_tick(call_on_tick)
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0

        self.recording_enabled = False
        self.recording_start = 0
        self.constant_velocity_enabled = False
        self.show_vehicle_telemetry = False
        self.doors_are_open = False
        self.current_map_layer = 0
        self.map_layer_names = [
            carla.MapLayer.NONE,
            carla.MapLayer.Buildings,
            carla.MapLayer.Decals,
            carla.MapLayer.Foliage,
            carla.MapLayer.Ground,
            carla.MapLayer.ParkedVehicles,
            carla.MapLayer.Particles,
            carla.MapLayer.Props,
            carla.MapLayer.StreetLights,
            carla.MapLayer.Walls,
            carla.MapLayer.All
        ]

        self._sensors = []

    def start(self):
        if self._sync:
            self.sim_world.tick()
        else:
            self.sim_world.wait_for_tick()

    def add_tick_listener(self, callback):
        self._tick_callbacks.add(callback)

    # def add_sensor(self, sensor: TeleSensor, parent):
    #     sensor.spawn_in_world(parent)
    #     self._sensors.append(sensor)

    def tick(self, clock):  # TODO change here, put NetworkNode
        """Method for every tick"""
        if self._sync:
            self.sim_world.tick()
        else:
            self.sim_world.wait_for_tick()

        self._last_snapshot = self.sim_world.get_snapshot()
        # command = self._controller.do_action(clock)
        # if command is None:
        #     return -1
        # network_delay_manager.schedule(lambda: self.player.apply_control(command),
        #                                0.01)  # TODO change delay hardcoded here
        # self.player.apply_control(command)

    def quit(self):
        self._tick_callbacks.clear()

    @property
    def timestamp(self):
        if self._last_snapshot is None:
            self._last_snapshot = self.sim_world.get_snapshot()
        return self._last_snapshot.timestamp

    def get_snapshot(self):
        return self.sim_world.get_snapshot()

    def apply_sync_command(self, *commands):
        return self.client.apply_batch_sync(commands)
