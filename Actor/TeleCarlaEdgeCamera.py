from pycarlanet.utils import InstanceExist, ObjectStorage
from pycarlanet import CarlanetActor, CarlaClient
import carla

import sys,os
import numpy as np


#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.TeleVehicleControl import TeleVehicleControl
from utils.TeleVehicleState import TeleVehicleState

from Actor.Mixin import CooperativeUpdateMixin

class FakeActor():
    def __init__(self):
        self.id = 0
        self.bounding_box = carla.BoundingBox(carla.Location(x=0, y=0, z=0), carla.Vector3D(x=0.2, y=0.2, z=0.2))

    def get_transform(self):
        return carla.Transform(carla.Location(x=0, y=0, z=0), carla.Rotation(pitch=0, yaw=0, roll=0))
    def get_velocity(self):
        return carla.Vector3D(x=0, y=0, z=0)
    def get_speed_limit(self):
        return 0.0
    def get_acceleration(self):
        return carla.Vector3D(x=0, y=0, z=0)

class TeleCarlaEdgeCamera(CarlanetActor, CooperativeUpdateMixin):

    def __init__(self, carla_actor: carla.Actor, actor_type: str):
        super().__init__(None, actor_type)
        self._carla_actor = FakeActor()
        #     for actor_id, actor in self._carlanet_actors.items():
        # transform: carla.Transform = actor.carla_actor.get_transform()
        # velocity: carla.Vector3D = actor.carla_actor.get_velocity()
        # position = dict()
        # position['actor_id'] = actor_id
        # position['position'] = [transform.location.x, transform.location.y, transform.location.z]
        # position['rotation'] = [transform.rotation.pitch, transform.rotation.yaw, transform.rotation.roll]
        # position['velocity'] = [velocity.x, velocity.y, velocity.z]
        # position['type'] = actor.actor_type

    #methods for API calls
    @InstanceExist(CarlaClient)
    def generate_status(self):
        visible_vehicles = [v for v in CarlaClient.instance.world.get_actors().filter('vehicle.*')]
        visible_pedestrians = CarlaClient.instance.world.get_actors().filter('*walker.pedestrian.*')

        return TeleVehicleState.generate_vehicle_state(CarlaClient.instance.world.get_snapshot().timestamp, self, visible_vehicles, visible_pedestrians)
    
    def done(self, timestamp):
        return True
    
    def handle_cooperative_update(self, status_id):
        print("handle_cooperative_update EdgeCamera")