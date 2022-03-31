import random
import sys
from abc import ABC, abstractmethod

import carla
from carla import ActorBlueprint

from src.utils.utils import need_member


class TeleActor(ABC):
    def __init__(self, actor_filter, actor_id, attrs):
        self._actor_filter = actor_filter
        self._actor_id = actor_id
        self._attrs = attrs
        self.model = None

    @abstractmethod
    def spawn_in_world(self, map, world):
        ...


class TeleVehicle(TeleActor):

    def __init__(self, actor_filter, actor_id, attrs, modify_vehicle_physics=False):
        super().__init__(actor_filter, actor_id, attrs)
        self._show_vehicle_telemetry = False
        self._modify_vehicle_physics = modify_vehicle_physics

    @need_member('model')
    def __getattr__(self, *args):
        return self.model.__getattribute__(*args)

    def spawn_in_world(self, map, world):

        blueprint: ActorBlueprint = random.choice(world.get_blueprint_library().filter(self._actor_filter))
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)

        for key, value in self._attrs.items():
            blueprint.set_attribute(key, value)

        self.model = None
        while self.model is None:
            if not map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)
            spawn_points = map.get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.model = world.try_spawn_actor(blueprint, spawn_point)
        if self._modify_vehicle_physics:
            self.modify_vehicle_physics()
        self.set_light_state(carla.VehicleLightState.Position)

    def modify_vehicle_physics(self):
        try:
            physics_control = self.get_physics_control()
            physics_control.use_sweep_wheel_collision = True
            self.apply_physics_control(physics_control)
        except Exception:
            pass
