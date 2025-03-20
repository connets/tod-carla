from pycarlanet.utils import InstanceExist
from pycarlanet import CarlanetActor, CarlaClient
import carla
from utils.TeleVehicleState import TeleVehicleState

from Actor.Mixin import CooperativeUpdateMixin

from FakeActor import MovingFakeActor

class SLDisturbing(CarlanetActor, CooperativeUpdateMixin):
    def __init__(self, actor_type: str, origin: carla.Location = None):
        super().__init__(None, actor_type)
        if origin == None:
            self._carla_actor = MovingFakeActor()
        else:
            self._carla_actor = MovingFakeActor(position=origin)

    #methods for API calls
    @InstanceExist(CarlaClient)
    def generate_status(self):
        return TeleVehicleState.generate_vehicle_state(CarlaClient.instance.world.get_snapshot().timestamp, self, [], [])
    
    def done(self, timestamp):
        return True
    
    def handle_cooperative_update(self, status_id):
        ...
        #print("handle_cooperative_update NRUeMovingDisturbing")