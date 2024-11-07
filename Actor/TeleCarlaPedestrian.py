from pycarlanet.utils import InstanceExist
from pycarlanet import CarlanetActor, CarlaClient
import carla
import math

import sys,os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TeleCarlaPedestrian(CarlanetActor):

    def __init__(self, carla_actor: carla.Actor, actor_type: str, destination=None, max_speed=None):
        super().__init__(carla_actor, actor_type)
        self._destination = destination
        self._max_speed = max_speed if (max_speed is not None) else 1.4
        if self._destination is not None:
            self._attach_controller()



    @InstanceExist(CarlaClient)
    def _attach_controller(self):
        control = carla.WalkerControl()
        control.speed = self._max_speed
        control.direction.x, control.direction.y, control.direction.z = self._find_direction_vector(self.carla_actor.get_location(), self._destination)
        # control.direction.x = 0
        # control.direction.y = -1
        # control.direction.z = 0
        self.carla_actor.apply_control(control)


    def _find_direction_vector(self, location_a, location_b):
        # Calculate the direction vector components
        direction_x = location_b.x - location_a.x
        direction_y = location_b.y - location_a.y
        direction_z = location_b.z - location_a.z
        
        # Calculate the magnitude of the direction vector
        magnitude = math.sqrt(direction_x**2 + direction_y**2 + direction_z**2)
        
        # Normalize the vector (if magnitude is not zero)
        if magnitude > 0:
            normalized_vector = (
                direction_x / magnitude,
                direction_y / magnitude,
                direction_z / magnitude
            )
        else:
            normalized_vector = (0.0, 0.0, 0.0)  # Handle case where A and B are the same

        return normalized_vector



        # walker_controller_bp = CarlaClient.instance.world.get_blueprint_library().find('controller.ai.walker')
        # # attach controller to pedestrian
        # result = CarlaClient.instance.client.apply_batch_sync([
        #     carla.command.SpawnActor(walker_controller_bp, carla.Transform(), self.carla_actor)
        # ], True)[0]
        # if result.error:
        #     #print(f"Error while spawning walker controller: {result}")
        #     raise Exception(f"Error while spawning walker controller: {result}")
        
        # #print(f"Walker controller spawned successfully with id: {result.actor_id}")
        # ai_controller = CarlaClient.instance.world.get_actor(result.actor_id)

        # ai_controller.start()
        # #set destination
        # ai_controller.go_to_location(self._destination)
        # #set max_speed
        # ai_controller.set_max_speed(self._max_speed)