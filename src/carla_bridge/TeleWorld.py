import sys

import carla

from src.actor.TeleSensor import TeleSensor, TeleRenderingSensor
from src.utils.carla_utils import find_weather_presets
from src.utils.utils import need_member
from carla.libcarla import World


class TeleWorld:

    def __init__(self, world_name):
        self._world_name = world_name
        self._scheduler = None
        self._events = set()

    @property
    def world_name(self):
        return self._world_name

    @need_member("_scheduler")
    def schedule_event(self, event, ms: int):
        self._events.add(event)
        self._scheduler.schedule(self.callback_event(event), ms)

    def callback_event(self, event):
        def call_event():
            event(self)

        return call_event


class TeleActuatorWorld(TeleWorld):
    """ Class representing the surrounding environment """

    def __init__(self, carla_world: World, vehicle, carla_conf, hud):
        """Constructor method"""
        super().__init__("Actuator_World")
        self._carla_conf = carla_conf
        self._controller = None
        self._last_snapshot: carla.WorldSnapshot = carla_world.get_snapshot()

        self.sim_world: World = carla_world

        if carla_conf['synchronicity']:
            self.sync = True
            settings = self.sim_world.get_settings()
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = float(self._carla_conf['time_step'])
            self.sim_world.apply_settings(settings)
            # traffic_manager.set_synchronous_mode(True)
        else:
            self.sync = False
        try:
            self.map = self.sim_world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)

        # for spawn_point in self.map.get_spawn_points():
        #     if abs(396.984039 - spawn_point.location.x) < 6:
        #         print(spawn_point)

        self.player = vehicle
        self.player.spawn_in_world(self.map, self.sim_world)

        self.hud = hud
        self.vehicles = []

        self.sim_world.on_tick(self.hud.on_world_tick)

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
        if self.sync:
            self.sim_world.tick()
        else:
            self.sim_world.wait_for_tick()

    def add_controller(self, controller):
        self._controller = controller
        self._controller.add_player_in_world(self.player)

    def add_sensor(self, sensor: TeleSensor, parent):
        sensor.spawn_in_world(parent)
        self._sensors.append(sensor)

    @need_member('player', '_controller')
    def tick(self, clock):  # TODO change here, put NetworkNode
        """Method for every tick"""
        if self.sync:
            self.sim_world.tick()
        else:
            self.sim_world.wait_for_tick()

        self._last_snapshot = self.sim_world.get_snapshot()
        command = self._controller.do_action(clock)
        if command is None:
            return -1
        # network_delay_manager.schedule(lambda: self.player.apply_control(command),
        #                                0.01)  # TODO change delay hardcoded here
        self.player.apply_control(command)

        self.hud.tick(self, clock)
        return 0

    def render(self, display):
        """Render world"""
        for sensor in self._sensors:
            if isinstance(sensor, TeleRenderingSensor):
                sensor.render(display)

        # self.camera_manager.render(display)
        # self.hud.render(display)

    def destroy(self):
        for sensor in self._sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
        if self.player is not None:
            self.player.destroy()

    @property
    def timestamp(self):
        return self._last_snapshot.timestamp
