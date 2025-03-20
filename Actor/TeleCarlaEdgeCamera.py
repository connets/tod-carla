from pycarlanet.utils import InstanceExist, ObjectStorage
from pycarlanet import CarlanetActor, CarlaClient
import carla
from utils.TeleVehicleState import TeleVehicleState, OtherVehicleState

from Actor.Mixin import CooperativeUpdateMixin

from FakeActor import StaticFakeActor

class TeleCarlaEdgeCamera(CarlanetActor, CooperativeUpdateMixin):

    def __init__(self, actor_type: str, origin: carla.Location = None):
        super().__init__(None, actor_type)
        if origin == None:
            self._carla_actor = StaticFakeActor()
        else:
            self._carla_actor = StaticFakeActor(position=origin)
        self.othersStates = {}

    #methods for API calls
    @InstanceExist(CarlaClient)
    def generate_status(self):
        def generate_union(obstacles, otherObjects, otherTimestamp):
            ids = [o.id for o in obstacles]
            tMine = CarlaClient.instance.world.get_snapshot().timestamp
            for obj in otherObjects:
                #check if the object is already in the list
                if obj.id in ids: continue
                #calculate new position based on velocity vector?
                deltaSeconds = tMine.elapsed_seconds - otherTimestamp.elapsed_seconds
                obj.timestamp = tMine
                obj.transform.location = carla.Location(
                    x=obj.transform.location.x + obj.velocity.x * deltaSeconds,
                    y=obj.transform.location.y + obj.velocity.y * deltaSeconds,
                    z=obj.transform.location.z + obj.velocity.z * deltaSeconds
                )
                obstacles.append(obj)

            return obstacles
        
        visible_vehicles = [v for v in CarlaClient.instance.world.get_actors().filter('vehicle.*')]
        visible_pedestrians = CarlaClient.instance.world.get_actors().filter('*walker.pedestrian.*')

        for _,state in self.othersStates.items():
            #check who is the generator and decide to add or not, and where Vehicle or pedestrian?
            #trust generator position instead of my calculation of it?
            try:
                generator = CarlaClient.instance.world.get_actor(state.id)
                if generator==None: raise Exception("Generator not found in the world")
                generatorState = OtherVehicleState.generate_visible_vehicle(0, generator)
                if generator.type_id.startswith('vehicle'):
                    visible_vehicles = generate_union(visible_vehicles, [generatorState], state.timestamp)
                elif generator.type_id.startswith('walker.pedestrian'):
                    visible_pedestrians = generate_union(visible_pedestrians, [generatorState], state.timestamp)
            except:
                ...
            #add other visible vehicles
            visible_vehicles = generate_union(visible_vehicles, state.visible_vehicles, state.timestamp)
            visible_pedestrians = generate_union(visible_pedestrians, state.visible_pedestrians, state.timestamp)

        return TeleVehicleState.generate_vehicle_state(CarlaClient.instance.world.get_snapshot().timestamp, self, visible_vehicles, visible_pedestrians)
    
    def done(self, timestamp):
        return True
    
    def handle_cooperative_update(self, status_id):
        #print("handle_cooperative_update EdgeCamera")
        state = ObjectStorage.get(status_id)
        if state.id == self.carla_actor.id:
            return
        if state.id not in self.othersStates:
            self.othersStates[state.id] = state
            return
        if state.timestamp.elapsed_seconds > self.othersStates[state.id].timestamp.elapsed_seconds:
            self.othersStates[state.id] = state
            return