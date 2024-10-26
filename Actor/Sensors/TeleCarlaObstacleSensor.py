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

class TeleCarlaObstacleSensor(TeleCarlaSensor):
    """ Class for obstacle sensors"""
    def __init__(self, parent_actor):
        self._attach_to_actor(parent_actor)

    @InstanceExist(CarlaClient)
    def _attach_to_actor(self, parent_actor):
        """Constructor method"""
        blueprint = CarlaClient.instance.world.get_blueprint_library().find('sensor.other.obstacle')
        self.sensor = CarlaClient.instance.world.spawn_actor(
            blueprint,
            carla.Transform(),
            attach_to=parent_actor
        )
        # We need to pass the lambda a weak reference to
        # self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: self._on_detection(weak_self, event))

    @staticmethod
    def _on_detection(weak_self, event):
        """On detection method"""
        self = weak_self()
        if not self:
            return
        print("**** DANGER OBSTACLE ****", event.other_actor, event.distance)
        
    def destroy(self):
        self.sensor.destroy()

