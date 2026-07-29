import sys
import os
import json
import carla
import yaml
import random

import carla
from carla.libcarla import ActorBlueprint

from pycarlanet.utils import InstanceExist, ObjectStorage
from pycarlanet.listeners import ActorManager, AgentManager
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
from Actor.SLDisturbing import SLDisturbing

from utils.InterCommunicationListeners import InterCommunicationListeners
import utils.LidarUtility as LidarUtility
import utils.YAMLLoader as YAMLLoader
#from utils.Hud import HUD
import pygame

from lib.agents.navigation.constant_velocity_agent import ConstantVelocityAgent

class MyActorManager(ActorManager):
    after_tick_callback = []
    _autoPilotAgents = []
    _firstsimStep = None
    _crashTime = None
    # Dead-man's switch: last simulated instant at which each teleoperated actor
    # actually applied an instruction, and whether we already reported it as lost.
    _last_instruction_time = dict()
    _link_lost = dict()

    def omnet_init_completed(self, message):
        super().omnet_init_completed(message)
        try:
            data = YAMLLoader.load_and_merge_yaml_file(f"{FolderPath.CONFIGURATION_PATH}{message['user_defined']['config_name']}.yaml")
            # with open(f"{FolderPath.CONFIGURATION_PATH}{message['user_defined']['config_name']}.yaml", 'r') as file:
            #     #data = json.load(file)
            #     data = yaml.safe_load(file)

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
                    self._generateVehicle(actor=actor,origin=origin, message=message)
                
                if actor['actor_type'] == 'Pedestrian':
                    self._generatePedestrian(actor=actor,origin=origin)
                
                if actor['actor_type'] == 'EdgeCamera':
                    self._generateEdgeCamera(actor=actor,origin=origin)

                if actor['actor_type'] == 'SLDisturbing':
                    self._generateSLDisturbing(actor=actor,origin=origin)
                    
                        
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
        if message['user_message_type'] == 'ACTOR_STATUS_UPDATE_ZERO_DELAY':
            #check for actor.done() is useful to get all sensor data
            _, status = self._generate_status(message=message)
            #ask to agent compute instruction
            _, instruction = InterCommunicationListeners.instance.askToManager(AgentManager, 'compute_instruction', status)
            #apply_instruction
            instruction['user_message_type'] = 'APPLY_INSTRUCTION'
            return self.generic_message(0, instruction)
        elif message['user_message_type'] == 'APPLY_INSTRUCTION':
            instruction_id = message['instruction_id']
            actor_id = message['actor_id']
            if isinstance(self._carlanet_actors[actor_id], TeleCarlaVehicle):
                if instruction_id != str(-1):
                    self._carlanet_actors[actor_id].apply_instruction(ObjectStorage.get_and_remove(instruction_id))
                    self._rearm_control_link(actor_id)
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
        now = CarlaClient.instance.world.get_snapshot().timestamp.elapsed_seconds
        if self._firstsimStep is None:
            self._firstsimStep = now
        self._check_control_link(now)
        for autoPilotAgent in self._autoPilotAgents:
            if 'startSeconds' in autoPilotAgent and now >= self._firstsimStep + autoPilotAgent['startSeconds']:
                if autoPilotAgent['type'] == 'v':
                    # Route loop: background traffic restarts its own route from where
                    # it is, so it does not park itself halfway through the simulation
                    # and stop loading the cells.
                    if autoPilotAgent.get('route_loop') and autoPilotAgent['agent'].done():
                        autoPilotAgent['agent'].set_destinations(
                            *autoPilotAgent['destinations'],
                            start_location=autoPilotAgent['carla_actor'].get_location())
                    control = autoPilotAgent['agent'].run_step()
                    control.manual_gear_shift = False
                    CarlaClient.instance.client.apply_batch_sync([carla.command.ApplyVehicleControl(
                        autoPilotAgent['carla_actor_id'],
                        control
                    )])
                elif autoPilotAgent['type'] == 'p':
                    autoPilotAgent['carla_actor'].start_moving()
        # if len(self._carlanet_actors) == 0: return

        # try:
        #     # Get the spectator from the world
        #     spectator = CarlaClient.instance.world.get_spectator()
        #     # Get the the vehicle
        #     #key = next(iter(self._carlanet_actors)
        #     car: carla.Actor = self._carlanet_actors['Car01'].carla_actor
        #     # Set the camera view on top of vehicle
        #     spectator.set_transform(carla.Transform(
        #         car.get_transform().location + carla.Location(z=20),
        #         carla.Rotation(pitch=-90)
        #     ))
            
        # except Exception as error:
        #     print(f"actormanager before_world_tick error: {error}")
        ...

    @InstanceExist(CarlaClient)
    def after_world_tick(self, timestamp):
        #print(f"actormanager after_world_tick: {len(self._autoPilotAgents)} {[e['type'] for e in self._autoPilotAgents]}")
        for callback in self.after_tick_callback:
            callback(timestamp)
        

    #InterCommunicationListeners Function    
    def get_actor_from_id(self, actor_id):
        return self._carlanet_actors[actor_id]
    
    @InstanceExist(CarlaClient)
    def check_hero_crash(self):
        now = CarlaClient.instance.world.get_snapshot().timestamp.elapsed_seconds
        if self._crashTime != None:
            if now > self._crashTime + 3.0:
                return True
        else:
            for _, actor in self._carlanet_actors.items():
                if isinstance(actor, TeleCarlaVehicle) and actor.hero and actor.crashed:
                    self._crashTime = now
                    break
        return False

    def check_hero_destination_reached(self):
        for actor_id, actor in self._carlanet_actors.items():
            if isinstance(actor, TeleCarlaVehicle) and actor.hero:
                # With route_loop the ego restarts the route instead of finishing,
                # so arriving at the last destination must not end the simulation.
                if InterCommunicationListeners.instance.askToManager(AgentManager, 'is_route_looping', actor_id):
                    continue
                #ask to agent compute instruction
                agent = InterCommunicationListeners.instance.askToManager(AgentManager, 'get_agent_from_actor_id_controlled', actor_id)
                last = agent._destination_locations[-1]
                if actor.carla_actor.get_location().distance(last) < 2:
                    return True
        return False

    def _rearm_control_link(self, actor_id):
        """
        An instruction was actually applied, so the teleoperator is alive: reset the
        silence timer of the dead-man's switch for this actor.
        """
        now = CarlaClient.instance.world.get_snapshot().timestamp.elapsed_seconds
        self._last_instruction_time[actor_id] = now
        if self._link_lost.pop(actor_id, False):
            print(f"[dead-man] {actor_id}: canale di controllo ripristinato a t={now:.3f}s")

    @InstanceExist(CarlaClient)
    def _check_control_link(self, now):
        """
        Dead-man's switch. The loss_ratio threshold covers PARTIAL loss: a status still
        reaches the teleoperator, it computes an instruction, and that instruction says
        "brake". If instead the control channel drops entirely (congestion, coverage,
        gNB lost) no instruction arrives at all and CARLA keeps applying the LAST one
        received: the vehicle would carry on at constant speed and steering until it
        leaves the road. Here the vehicle notices on its own and puts itself in safety.

        This lives in the actor manager, not in the co-simulation glue: it is an on-board
        function of the car, and it must keep running even while the network is silent.
        """
        for actor_id in InterCommunicationListeners.instance.askToManager(AgentManager, 'get_teleoperated_actor_ids'):
            actor = self._carlanet_actors.get(actor_id)
            if not isinstance(actor, TeleCarlaVehicle):
                continue

            controller = InterCommunicationListeners.instance.askToManager(AgentManager, 'get_agent_from_actor_id_controlled', actor_id)

            # first instruction not arrived yet: start counting from now
            last = self._last_instruction_time.setdefault(actor_id, now)
            silence = now - last
            if silence < controller.control_timeout:
                continue

            if not self._link_lost.get(actor_id, False):
                self._link_lost[actor_id] = True
                print(f"[dead-man] {actor_id}: nessuna istruzione da {silence:.3f}s "
                      f"a t={now:.3f}s -> manovra a rischio minimo")

            # re-applied at every step: the braking has to be held
            instruction = controller.minimum_risk_maneuver()
            if instruction is not None:
                actor.apply_instruction(instruction)


    #others functions
    def _generate_status(self,message):
        while any(not actor.done(CarlaClient.instance.world.get_snapshot().timestamp) for actor in self._carlanet_actors.values() if 'done' in actor.__dict__):
                ...
        actor_id = message['actor_id']
        if isinstance(self._carlanet_actors[actor_id], TeleCarlaVehicle) or isinstance(self._carlanet_actors[actor_id], TeleCarlaEdgeCamera) or isinstance(self._carlanet_actors[actor_id], SLDisturbing):
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
        teleactor = TeleCarlaPedestrian(carla_actor, 'Pedestrian', destination=destination, max_speed=speed_limit)
        #carlanet_actor = TeleCarlaPedestrian(carla_actor, 'Pedestrian', destination=destination, max_speed=speed_limit)
        #aid = f"{carla_actor.id}" if ('actor_id' not in actor or actor['actor_id'] == '') else actor['actor_id'] #if id is not specified use carla id
        #print(f"add to actors dictionary: {aid}")
        if 'startSeconds' in actor:
            self._autoPilotAgents.append({'type':'p', 'carla_actor': teleactor, 'startSeconds': actor['startSeconds']})
        #self._pedestrian[aid] = TeleCarlaPedestrian

    @InstanceExist(CarlaClient)
    def _generateVehicle(self, actor, origin, message):
        try:
            blueprint: ActorBlueprint = random.choice(CarlaClient.instance.world.get_blueprint_library().filter(actor['model']))
            spawn_points = CarlaClient.instance.world.get_map().get_spawn_points()
            spawn_point = random.choice(spawn_points)
            response = CarlaClient.instance.client.apply_batch_sync(
                [carla.command.SpawnActor(blueprint, spawn_point)],
                False
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
                ], False)

            CarlaClient.instance.world.tick()


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
                    collisions_sensor = TeleCarlaCollisionSensor(parent_actor=carlanet_actor.carla_actor, callback=carlanet_actor.sensor_callback)
                    carlanet_actor.attach_sensor(collisions_sensor)

                
                if 'camera' in actor:
                    camera_sensor = TeleCarlaCameraSensor(parent_actor=carlanet_actor.carla_actor, gamma_correction=2.2)
                    if carlanet_actor.hero: camera_sensor.set_write_out_path(True)
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


            if 'destination' in actor or 'destinations' in actor:
                # 'destination' (single) is the original form; 'destinations' is a list
                # and is what background traffic uses to cover a long route.
                if 'destinations' in actor:
                    dests = [carla.Location(x=d['x'], y=d['y'], z=d['z']) for d in actor['destinations']]
                else:
                    dests = [carla.Location(x=actor['destination']['x'], y=actor['destination']['y'], z=actor['destination']['z'])]
                opt_dict={
                    'dt': message["carla_configuration"]['carla_timestep'],
                    'ignore_traffic_lights': True,
                    'ignore_stop_signs': True,
                    'ignore_vehicles': True,
                    'ignore_pedestrian': True,
                    'collision_calculation_method': 'CARLADEFAULT',
                    'ignoreIds': []
                }
                # opt_dict['target_speed'] = target_speed
                # if 'ignore_traffic_lights' in opt_dict:
                #     self._ignore_traffic_lights = opt_dict['ignore_traffic_lights']
                # if 'ignore_stop_signs' in opt_dict:
                #     self._ignore_stop_signs = opt_dict['ignore_stop_signs']
                # if 'ignore_vehicles' in opt_dict:
                #     self._ignore_vehicles = opt_dict['ignore_vehicles']
                # if 'ignore_pedestrian' in opt_dict:
                #     self._ignore_pedestrian = opt_dict['ignore_pedestrian']
                # if 'sampling_resolution' in opt_dict:
                #     self._sampling_resolution = opt_dict['sampling_resolution']
                # if 'base_tlight_threshold' in opt_dict:
                #     self._base_tlight_threshold = opt_dict['base_tlight_threshold']
                # if 'base_vehicle_threshold' in opt_dict:
                #     self._base_vehicle_threshold = opt_dict['base_vehicle_threshold']
                # if 'max_brake' in opt_dict:
                #     self._max_steering = opt_dict['max_brake']
                
                targetSpeed = actor['targetSpeed'] if 'targetSpeed' in actor else 30
                #print(f"target speed: {targetSpeed}")
                agent = ConstantVelocityAgent(vehicle=carla_actor, target_speed=targetSpeed, opt_dict=opt_dict)
                agent.follow_speed_limits(True)
                #end_waypoint = [CarlaClient.instance.world.get_map().get_waypoint(destination) for destination in [dest]]
                if len(dests) == 1:
                    agent.set_destination(dests[0])
                else:
                    agent.set_destinations(*dests)
                # 'destinations' implies the vehicle is meant to drive, so it does not
                # need an explicit startSeconds to be scheduled.
                if 'startSeconds' in actor or 'destinations' in actor:
                    self._autoPilotAgents.append({
                        'type': 'v',
                        'agent': agent,
                        'carla_actor_id': carla_actor.id,
                        'carla_actor': carla_actor,
                        'startSeconds': actor.get('startSeconds', 0),
                        'destinations': dests,
                        'route_loop': actor.get('route_loop', False)
                    })


            aid = f"{carla_actor.id}" if ('actor_id' not in actor or actor['actor_id'] == '') else actor['actor_id'] #if id is not specified use carla id
            print(f"add to actors dictionary: {aid}")
            self._carlanet_actors[aid] = carlanet_actor
        except Exception as error:
            print(f"Error: {error}")
            raise error


    @InstanceExist(CarlaClient)
    def _generateEdgeCamera(self, actor, origin):
        if origin is not None:
            origin = carla.Location(x=origin['x'], y=origin['y'], z=origin['z'])
        carlanet_actor = TeleCarlaEdgeCamera('EdgeCamera', origin=origin)
        aid = "NoID" if ('actor_id' not in actor or actor['actor_id'] == '') else actor['actor_id'] #if id is not specified use carla id
        print(f"add to actors dictionary: {aid}")
        self._carlanet_actors[aid] = carlanet_actor
    
    @InstanceExist(CarlaClient)
    def _generateSLDisturbing(self, actor, origin):
        if origin is not None:
            origin = carla.Location(x=origin['x'], y=origin['y'], z=origin['z'])
        if 'howMany' in actor:
            for i in range(0, actor['howMany']):
                carlanet_actor = SLDisturbing('SLDisturbing', origin=origin)
                aid = f"NoID_{i}" if ('actor_id' not in actor or actor['actor_id'] == '') else f"{actor['actor_id']}_{i}" #if id is not specified use carla id
                print(f"add to actors dictionary: {aid}")
                self._carlanet_actors[aid] = carlanet_actor
        else:
            carlanet_actor = SLDisturbing('SLDisturbing', origin=origin)
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