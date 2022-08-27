import sys

import carla
from carla import libcarla

from src.utils.carla_utils import find_weather_presets
from carla.libcarla import World


class TeleWorld:
    """ Class representing the surrounding environment """

    def __init__(self, client: libcarla.Client, clock):
        """Constructor method"""

        self.client = client
        self.clock = clock
        self.sim_world: World = self.client.get_world()
        self._last_snapshot: carla.WorldSnapshot = self.sim_world.get_snapshot()
        # builds = self.sim_world.get_environment_objects(carla.CityObjectLabel.Buildings)
        # objects_to_toggle = {build.id for build in builds}
        # self.sim_world.enable_environment_objects(objects_to_toggle, True)

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
        # useful to synchronize timestamp

    # def add_sensor(self, sensor: TeleSensor, parent):
    #     sensor.spawn_in_world(parent)
    #     self._sensors.append(sensor)

    def add_tick_callback(self, callback):
        self._tick_callbacks.add(callback)

    def tick(self):  # TODO change here, put NetworkNode
        """Method for every tick"""
        elapsed_seconds_old = self.timestamp.elapsed_seconds
        self.clock.tick()
        before = self.sim_world.get_snapshot().frame
        frame = self.sim_world.tick()
        while elapsed_seconds_old == self.timestamp.elapsed_seconds:
            ...
        self._last_snapshot = self.sim_world.get_snapshot()
        for callback in self._tick_callbacks: callback(self.timestamp)

        # command = self._controller.do_action(clock)
        # if command is None:
        #     return -1
        # network_delay_manager.schedule(lambda: self.player.apply_control(command),
        #                                0.01)  # TODO change delay hardcoded here
        # self.player.apply_control(command)

    def quit(self):
        self._tick_callbacks.clear()

    def is_alive(self):
        try:
            self.get_snapshot()
            return True
        except Exception as _:
            return False

    @property
    def timestamp(self):
        """ TODO
        don't call every time this method, but saves every tick,
        now this instruction is mandatory for the change from async mode to sync
        """
        return self.get_snapshot().timestamp

    def get_snapshot(self):
        return self.sim_world.get_snapshot()

    def apply_sync_command(self, *commands):
        results = self.client.apply_batch_sync(commands)
        return results
