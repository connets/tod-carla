import sys
import os
import json
import carla
import yaml
import random

import carla
from carla.libcarla import ActorBlueprint

from pycarlanet.utils import InstanceExist, ObjectStorage
from pycarlanet.listeners import ActorManager
from pycarlanet.enum import SimulatorStatus
from pycarlanet import CarlaClient, ActorType, CarlanetActor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.FolderPath import FolderPath
from Actor.TeleCarlaVehicle import TeleCarlaVehicle
from Actor.Sensors.TeleCarlaCollisionSensor import TeleCarlaCollisionSensor
from Actor.Sensors.TeleCarlaCameraSensor import TeleCarlaCameraSensor
from Actor.Sensors.TeleCarlaLidarSensor import TeleCarlaLidarSensor
from Actor.Sensors.TeleCarlaObstacleSensor import TeleCarlaObstacleSensor
from Actor.TeleCarlaPedestrian import TeleCarlaPedestrian
from Actor.Mixin import CooperativeUpdateMixin

from Actor.TeleCarlaEdgeCamera import TeleCarlaEdgeCamera

from utils.InterCommunicationListeners import InterCommunicationListeners
import utils.LidarUtility as LidarUtility
#from utils.Hud import HUD
import pygame


class MyActorManager(ActorManager):
    after_tick_callback = []

    def omnet_init_completed(self, message):
        super().omnet_init_completed(message)
        try:
            with open(f"{FolderPath.CONFIGURATION_PATH}{message['user_defined']['config_name']}.yaml", 'r') as file:
                #data = json.load(file)
                data = yaml.safe_load(file)

                for actor in data["new_vehicles"]:
                    print(f"creating actor as: {actor}")
                    if actor['actor_type'] not in ActorType.instance.get_available_types():
                        raise RuntimeError(f"I don\'t know this type {actor['actor_type']}\nActor type {actor['actor_type']} is not available in ActorTypes: {ActorType.instance.get_available_types()}")
                    
                    #try to get the origin point for spawn in correct position
                    origin = None
                    if 'origin' in actor:
                        origin = actor["origin"]
                    elif ('agents' in data and 'actor_id' in actor):
                        agents = [a for a in data["agents"] if a["actor_id_to_control"]==actor["actor_id"]]
                        if len(agents) > 0: origin = agents[0]["route"]["origin"]

                    if actor['actor_type'] == 'Vehicle':
                        self._generateVehicle(actor=actor,origin=origin)
                    
                    if actor['actor_type'] == 'Pedestrian':
                        self._generatePedestrian(actor=actor,origin=origin)
                    
                    if actor['actor_type'] == 'EdgeCamera':
                        self._generateEdgeCamera(actor=actor,origin=origin)
                    
                        
        except Exception as error:
            print(f"{self.__class__} omnet_init_completed error: {error}")
        
    #@InstanceExist(CarlaClient)
    #def create_actors_from_omnet(self, actors):
        #print("create_actors_from_omnet")
        #print(actors)
        # for actor in actors:
        #     if actor['actor_type'] not in ActorType.instance.get_available_types():
        #         raise RuntimeError(f"I don\'t know this type {actor['actor_type']}\nActor type {actor['actor_type']} is not available in ActorTypes: {ActorType.instance.get_available_types()}")
    
        #     if actor['actor_type'] == 'car':
        #         self._generateVehicle(actor=actor)
    
    @InstanceExist(CarlaClient)
    def generic_message(self, timestamp, message) -> (SimulatorStatus, dict):
        #print(f"message from omnet: {message['user_message_type']} for actor {message['actor_id']}")
        #if not 'msg_type' in message: return SimulatorStatus.RUNNING, {'message': 'from carla'}
        if message['user_message_type'] == 'ACTOR_STATUS_UPDATE':
            #check for actor.done() is useful to get all sensor data
            return self._generate_status(message=message)
        elif message['user_message_type'] == 'APPLY_INSTRUCTION':
            instruction_id = message['instruction_id']
            actor_id = message['actor_id']
            if isinstance(self._carlanet_actors[actor_id], TeleCarlaVehicle):
                if instruction_id != str(-1): self._carlanet_actors[actor_id].apply_instruction(ObjectStorage.get_and_remove(instruction_id))
                return SimulatorStatus.RUNNING, {'user_message_type': 'OK'}
            else:
                raise RuntimeError(f"I can\'t manage this type of message ({message['user_message_type']}) on actor {actor_id} of type {self._carlanet_actors[actor_id].__class__}")
        #generate the status for cooperative perception app (this status id propageted in broadcast)
        elif message['user_message_type'] == 'COOPERATIVE_STATUS_REQUEST':
            return self._generate_status(message=message)
        #receive from broadcast status generated by others vehicles
        elif message['user_message_type'] == 'COOPERATIVE_UPDATE':
            actor_id = message['actor_id']
            if isinstance(self._carlanet_actors[actor_id], CooperativeUpdateMixin):
                status_id = message['status_id']
                self._carlanet_actors[actor_id].handle_cooperative_update(status_id=status_id)
            return SimulatorStatus.RUNNING, {'user_message_type': 'OK'}
        else:
            raise RuntimeError(f"I don\'t know how to handle this message: {message}")
    
    @InstanceExist(CarlaClient)
    def before_world_tick(self, timestamp):
        if len(self._carlanet_actors) == 0: return

        try:
            # Get the spectator from the world
            spectator = CarlaClient.instance.world.get_spectator()
            # Get the the vehicle
            #key = next(iter(self._carlanet_actors)
            car: carla.Actor = self._carlanet_actors['Car01'].carla_actor
            # Set the camera view on top of vehicle
            spectator.set_transform(carla.Transform(
                car.get_transform().location + carla.Location(z=20),
                carla.Rotation(pitch=-90)
            ))
            
        except Exception as error:
            print(f"actormanager before_world_tick error: {error}")

    def after_world_tick(self, timestamp):
        for callback in self.after_tick_callback:
            callback(timestamp)


    #InterCommunicationListeners Function    
    def get_actor_from_id(self, actor_id):
        return self._carlanet_actors[actor_id]
    
    #others functions
    def _generate_status(self,message):
        while any(not actor.done(CarlaClient.instance.world.get_snapshot().timestamp) for actor in self._carlanet_actors.values() if 'done' in actor.__dict__):
                ...
        actor_id = message['actor_id']
        if isinstance(self._carlanet_actors[actor_id], TeleCarlaVehicle) or isinstance(self._carlanet_actors[actor_id], TeleCarlaEdgeCamera):
            actor_status = self._carlanet_actors[actor_id].generate_status()
            status_id = ObjectStorage.put(actor_status)
            return SimulatorStatus.RUNNING, {'user_message_type': 'ACTOR_STATUS', 'actor_id': actor_id, 'status_id': status_id}
        else:
            raise RuntimeError(f"I can\'t manage this type of message ({message['user_message_type']}) on actor {actor_id} of type {self._carlanet_actors[actor_id].__class__}")
    
    @InstanceExist(CarlaClient)
    def _generatePedestrian(self, actor, origin):
        walker_bp = CarlaClient.instance.world.get_blueprint_library().filter("walker.pedestrian.*")[0]
        walker_bp.set_attribute('is_invincible', 'false')

        spawn_point = carla.Transform()
        
        spawn_point.location = CarlaClient.instance.world.get_random_location_from_navigation()
        #print("spawn pedestrian in random position")
        response = CarlaClient.instance.client.apply_batch_sync([
            carla.command.SpawnActor(walker_bp, spawn_point),
        ], True)[0]

        #print("spawned pedestrian")
        #print("try to set specific transform")
        if origin is not None:
            results = CarlaClient.instance.client.apply_batch_sync([
                carla.command.ApplyTransform(
                    response.actor_id,
                    carla.Transform(
                        carla.Location(x=origin['x'], y=origin['y'], z=origin['z']),
                        carla.Rotation(pitch=origin['pitch'], yaw=origin['yaw'], roll=origin['roll'])
                    )
                )
            ], True)
            #print(results)
        #print("setted specific transform")
        carla_actor = CarlaClient.instance.world.get_actor(response.actor_id)
        carla_actor.set_simulate_physics(True)

        speed_limit = None
        if 'speed_limit' in actor:
            speed_limit = actor['speed_limit']
            #carla_actor.set_max_speed(actor['speed_limit'])

        destination = None
        if 'destination' in actor:
            destination = carla.Location(x=actor['destination']['x'], y=actor['destination']['y'], z=actor['destination']['z'])
        #else:
            #destination = CarlaClient.instance.world.get_random_location_from_navigation()[0]
        #print("create TeleCarlaPedestrian")
        TeleCarlaPedestrian(carla_actor, 'Pedestrian', destination=destination, max_speed=speed_limit)
        #carlanet_actor = TeleCarlaPedestrian(carla_actor, 'Pedestrian', destination=destination, max_speed=speed_limit)
        #aid = f"{carla_actor.id}" if ('actor_id' not in actor or actor['actor_id'] == '') else actor['actor_id'] #if id is not specified use carla id
        #print(f"add to actors dictionary: {aid}")
        #self._carlanet_actors[aid] = carlanet_actor

    @InstanceExist(CarlaClient)
    def _generateVehicle(self, actor, origin):
        blueprint: ActorBlueprint = random.choice(CarlaClient.instance.world.get_blueprint_library().filter(actor['model']))
        spawn_points = CarlaClient.instance.world.get_map().get_spawn_points()
        spawn_point = random.choice(spawn_points)
        response = CarlaClient.instance.client.apply_batch_sync(
            [carla.command.SpawnActor(blueprint, spawn_point)],
            True
        )[0]
        
        #set start position (getted from start origin of agent route or origin in vehicle specification) otherwise it start from the random spown_point
        if origin is not None:    
            CarlaClient.instance.client.apply_batch_sync([
                carla.command.ApplyTransform(
                    response.actor_id,
                    carla.Transform(
                        carla.Location(x=origin['x'], y=origin['y'], z=origin['z']),
                        carla.Rotation(pitch=origin['pitch'], yaw=origin['yaw'], roll=origin['roll'])
                    )
                )
            ], True)

        carla_actor: carla.Vehicle = CarlaClient.instance.world.get_actor(response.actor_id)
        
        carla_actor.set_simulate_physics(True)
        #carla_actor.set_autopilot(True)

        carlanet_actor = TeleCarlaVehicle(carla_actor, 'Vehicle')
        if actor['role_name'] == 'hero': carlanet_actor.hero = True

        try:
            #obstacle_sensor = TeleCarlaObstacleSensor(parent_actor=carlanet_actor.carla_actor)
            #carlanet_actor.attach_sensor(obstacle_sensor)
            #create sensors and attach them to parent
            if 'collision' in actor and actor['collision']:
                collisions_sensor = TeleCarlaCollisionSensor(parent_actor=carlanet_actor.carla_actor)
                carlanet_actor.attach_sensor(collisions_sensor)

            
            if 'camera' in actor:
                camera_sensor = TeleCarlaCameraSensor(parent_actor=carlanet_actor.carla_actor, gamma_correction=2.2)
                carlanet_actor.attach_sensor(camera_sensor)
                if actor["renderCamera"]:
                    self._create_display(
                        carlanet_actor,
                        actor['camera']['width'],
                        actor['camera']['height'],
                        camera_sensor
                    )

            if 'lidar' in actor and actor['lidar']:
                if carlanet_actor.hero:
                    #print("hero lidar ", carla_actor.id)
                    lidar_sensor = TeleCarlaLidarSensor(parent_actor=carlanet_actor.carla_actor, position=LidarUtility.SensorPosition.Up)
                    carlanet_actor.attach_sensor(lidar_sensor)
                else:
                    #print("other lidar ", carla_actor.id)
                    for position in LidarUtility.SensorPosition:
                        lidar_sensor = TeleCarlaLidarSensor(parent_actor=carlanet_actor.carla_actor, position=position)
                        carlanet_actor.attach_sensor(lidar_sensor)

            #attaching sensors to parent in carla, add in sensor constructor
            #for sensor in carlanet_actor.sensors:
            #    sensor.attach_to_actor(carlanet_actor.carla_actor)
        except Exception as e:
            print(f"exception during sensors init: {e}")



        


        aid = f"{carla_actor.id}" if ('actor_id' not in actor or actor['actor_id'] == '') else actor['actor_id'] #if id is not specified use carla id
        print(f"add to actors dictionary: {aid}")
        self._carlanet_actors[aid] = carlanet_actor


    @InstanceExist(CarlaClient)
    def _generateEdgeCamera(self, actor, origin):
        carlanet_actor = TeleCarlaEdgeCamera(None, 'EdgeCamera')
        aid = "NoID" if ('actor_id' not in actor or actor['actor_id'] == '') else actor['actor_id'] #if id is not specified use carla id
        print(f"add to actors dictionary: {aid}")
        self._carlanet_actors[aid] = carlanet_actor

    def _create_display(self, player, camera_width, camera_height, camera_sensor):
        pygame.init()
        pygame.font.init()
        display = pygame.display.set_mode((camera_width, camera_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        # display.fill((0, 0, 0))
        pygame.display.flip()

        #hud = HUD(player, self.clock, display)
        camera_sensor.add_display(display)

        def render(_):
            camera_sensor.render()
            #hud.render()
            pygame.display.flip()
        
        #every tick call render function of camerasensor that render on display the captured camera iamge
        self.after_tick_callback.append(render)
        #self.tele_world.add_tick_callback(render)
        #self.tele_world.add_tick_callback(hud.tick)