import random
import sys

import carla
from carla import ActorBlueprint

from src.utils.utils import need_member


class CarlaVehicle:

    def __init__(self, model, vehicle_id, attrs):
        self._model = model
        self.vehicle = vehicle_id
        self._attrs = attrs
        self._show_vehicle_telemetry = False


    @need_member('vehicle')
    def __getattr__(self, *args):
        return self.vehicle.__getattribute__(*args)

    def spawn_in_world(self, map, world, modify_vehicle_physics=False):

        blueprint: ActorBlueprint = random.choice(world.get_blueprint_library().filter(self._model))
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)

        for key, value in self._attrs.items():
            blueprint.set_attribute(key, value)

        self.vehicle = None
        while self.vehicle is None:
            if not map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)
            spawn_points = map.get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.vehicle = world.try_spawn_actor(blueprint, spawn_point)
        if modify_vehicle_physics:
            self.modify_vehicle_physics()
        self.set_light_state(carla.VehicleLightState.Position)

    def modify_vehicle_physics(self):
        try:
            physics_control = self.get_physics_control()
            physics_control.use_sweep_wheel_collision = True
            self.apply_physics_control(physics_control)
        except Exception:
            pass
