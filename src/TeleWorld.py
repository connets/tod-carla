import sys

import carla

from src.TeleActor import TeleVehicle
from src.TeleSensor import TeleSensor, TeleRenderingSensor
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

    def start(self, scheduler):
        self._scheduler = scheduler

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



        self.world: World = carla_world
        try:
            self.map = self.world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)

        self.player = vehicle
        self.player.spawn_in_world(self.map, self.world)

        self.hud = hud
        self.vehicles = []

        self.world.on_tick(self.hud.on_world_tick)

        # self.collision_sensor = None
        # self.lane_invasion_sensor = None
        # self.gnss_sensor = None
        # self.imu_sensor = None
        # self.radar_sensor = None
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        # self._actor_filter = args.filter
        # self._actor_generation = args.generation

        self.restart()

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

    def add_controller(self, controller):
        self._controller = controller
        self._controller.add_player_in_world(self.player)

    def add_sensor(self, sensor: TeleSensor, parent):
        sensor.spawn_in_world(parent)
        self._sensors.append(sensor)

    def restart(self):
        ...
        """Restart the world"""
        # Keep same camera config if the camera manager exists.
        # cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        # cam_pos_id = self.camera_manager.transform_index if self.camera_manager is not None else 0

        # Get a random blueprint.
        # blueprint = random.choice(self.world.get_blueprint_library().filter(self._carla_conf.vehicle))
        # blueprint.set_attribute('role_name', 'hero')
        # if blueprint.has_attribute('color'):
        #     color = random.choice(blueprint.get_attribute('color').recommended_values)
        #     blueprint.set_attribute('color', color)

        # if blueprint.has_attribute('speed'):
        #     self.player_max_speed = float(blueprint.get_attribute('speed').recommended_values[1])
        #     self.player_max_speed_fast = float(blueprint.get_attribute('speed').recommended_values[2])

        # Spawn the player.
        # if self.player is not None:
        #     spawn_point = self.player.get_transform()
        #     spawn_point.location.z += 2.0
        #     spawn_point.rotation.roll = 0.0
        #     spawn_point.rotation.pitch = 0.0
        #     self.destroy()
        #     self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        #     self.show_vehicle_telemetry = False
        #
        #     self.modify_vehicle_physics(self.player)
        # while self.player is None:
        #     if not self.map.get_spawn_points():
        #         print('There are no spawn points available in your map/town.')
        #         print('Please add some Vehicle Spawn Point to your UE4 scene.')
        #         sys.exit(1)
        #     spawn_points = self.map.get_spawn_points()
        #     spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
        #     self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        #     self.show_vehicle_telemetry = False
        #     self.modify_vehicle_physics(self.player)

        # self.world.wait_for_tick() #TODO usefull

        # Set up the sensors.
        # self.collision_sensor = CollisionSensor(self.player, self.hud)
        # self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        # self.gnss_sensor = GnssSensor(self.player)
        # self.camera_manager = CameraManager(self.player, self.hud, self._gamma)

        # self.camera_manager.restart()
        # self.camera_manager.transform_index = cam_pos_id
        # self.camera_manager.set_sensor(cam_index, notify=False)
        # actor_type = get_actor_display_name(self.player)
        # self.hud.notification(actor_type)

    # def next_weather(self, reverse=False):
    #     """Get next weather setting"""
    #     self._weather_index += -1 if reverse else 1
    #     self._weather_index %= len(self._weather_presets)
    #     preset = self._weather_presets[self._weather_index]
    #     # self.hud.notification('Weather: %s' % preset[1])
    #     self.player.get_world().set_weather(preset[0])

    #
    # def next_map_layer(self, reverse=False):
    #     self.current_map_layer += -1 if reverse else 1
    #     self.current_map_layer %= len(self.map_layer_names)
    #     selected = self.map_layer_names[self.current_map_layer]

    # def load_map_layer(self, unload=False):
    #     selected = self.map_layer_names[self.current_map_layer]
    #     if unload:
    #         self.world.unload_map_layer(selected)
    #     else:
    #         self.world.load_map_layer(selected)

        #
        # try:
        #     physics_control = player.get_physics_control()
        #     physics_control.use_sweep_wheel_collision = True
        #     player.apply_physics_control(physics_control)
        # except Exception:
        #     pass

    @need_member('player', '_controller')
    def tick(self, clock):
        """Method for every tick"""
        command = self._controller.do_action(clock)
        if command is None:
            return -1
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
        # if self.radar_sensor is not None:
        #     self.toggle_radar()
        # sensors = [
        #     self.camera_manager.sensor,
        #     self.collision_sensor.sensor,
        #     self.lane_invasion_sensor.sensor,
        #     self.gnss_sensor.sensor,
        #     self.imu_sensor.sensor]
        for sensor in self._sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
        if self.player is not None:
            self.player.destroy()
