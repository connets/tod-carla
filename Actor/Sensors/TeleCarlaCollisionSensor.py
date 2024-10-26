import collections
import math
import weakref
import carla
import sys, os

from pycarlanet import CarlaClient
from pycarlanet.utils import InstanceExist

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Actor.Sensors.TeleCarlaSensor import TeleCarlaSensor
from utils.Carlasupport import get_actor_display_name

class TeleCarlaCollisionSensor(TeleCarlaSensor):
    """ Class for collision sensors"""
    def __init__(self, parent_actor):
        self.history = []
        self._attach_to_actor(parent_actor)

    @InstanceExist(CarlaClient)
    def _attach_to_actor(self, parent_actor):
        """Constructor method"""
        blueprint = CarlaClient.instance.world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = CarlaClient.instance.world.spawn_actor(
            blueprint,
            carla.Transform(),
            attach_to=parent_actor
        )
        # We need to pass the lambda a weak reference to
        # self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: self._on_collision(weak_self, event))

    def get_collision_history(self):
        """Gets the history of collisions"""
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        """On collision method"""
        self = weak_self()
        if not self:
            return
        actor_type = get_actor_display_name(event.other_actor)
        print("**** ACCIDENT ****", actor_type)
        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x ** 2 + impulse.y ** 2 + impulse.z ** 2)
        self.history.append((event.frame, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)

    def destroy(self):
        self.sensor.destroy()

    def attach_data(self, vehicle_state):
        vehicle_state.collisions = self.history

