import os, sys, yaml
from typing import Any, Dict
import carla
import random

from pycarlanet.listeners import AgentManager, ActorManager
from pycarlanet.enum import SimulatorStatus
from pycarlanet import CarlaClient
from pycarlanet.utils import InstanceExist, ObjectStorage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.FolderPath import FolderPath
from Agent.TeleWorldController import BehaviorAgentTeleWorldAdapterController
from utils.InterCommunicationListeners import InterCommunicationListeners

class MyAgentManager(AgentManager):
    #TODO: add list of agents
    _agents: Dict[str, Any] = dict()

    def omnet_init_completed(self, message):
        #open user defined configuration file
        with open(f"{FolderPath.CONFIGURATION_PATH}{message['user_defined']['config_name']}.yaml", 'r') as file:
            #data = json.load(file)
            data = yaml.safe_load(file)
            agents = data['agents']
        
        for agent in agents:
            print(f"create agent {agent}")
            start_position, end_locations, time_limit = self._create_route(agent['route'])
            controller = BehaviorAgentTeleWorldAdapterController(
                agent['agentId'],
                InterCommunicationListeners.instance.askToManager(ActorManager, 'get_actor_from_id', agent['actor_id_to_control']),
                agent['behavior'],
                agent['sampling_resolution'],
                start_position.location,
                end_locations,
                opt_dict={
                    'dt': message["carla_configuration"]['carla_timestep'],
                    'ignore_traffic_lights': True,
                    'ignore_stop_signs': True,
                    'ignore_vehicles': False,
                    'ignore_pedestrian': False,
                    'collision_calculation_method': agent.get('collision_calculation_method', 'CARLADEFAULT'),
                    'ignoreIds': agent.get('ignoreIds', [])
                }
            )

            self._agents[agent['actor_id_to_control']] = controller




    def generic_message(self, timestamp, message) -> (SimulatorStatus, dict):
        #if not 'msg_type' in message: return SimulatorStatus.RUNNING, {'message': 'from carla'}

        if message['user_message_type'] == 'COMPUTE_INSTRUCTION':
            #agent_id = message['agent_id']
            actor_id = message['actor_id']
            status_id = message['status_id']


            simulator_status, instruction = SimulatorStatus.FINISHED_OK, None
            if not self._agents[actor_id].done():
                simulator_status = SimulatorStatus.RUNNING
                instruction = self._agents[actor_id].do_action(ObjectStorage.get_and_remove(status_id))
            
            #status = self.status.pop(status_id)
            #agent = self._external_active_actors[agent_id]

            instruction_id = str(-1) if (simulator_status != SimulatorStatus.RUNNING or instruction is None) else ObjectStorage.put(instruction)
            #self.instructions[instruction_id] = instruction
            #print(f"simulator_status: {simulator_status}, instruction_id: {instruction_id}, instruction {instruction}")
            return simulator_status, {'user_message_type':'INSTRUCTION', 'actor_id':actor_id, 'instruction_id':instruction_id}
        elif message['user_message_type'] == 'COOPERATIVE_UPDATE':
            print(f"receive cooperative update in agent {message}")
            return SimulatorStatus.RUNNING, {'user_message_type': 'OK'}
        else:
            raise RuntimeError(f"I don\'t know how to handle this message: {message}")
        


    @InstanceExist(CarlaClient)
    def _create_route(self, route_conf=None):
        if route_conf is not None:

            start_transform = carla.Transform(
                carla.Location(x=route_conf['origin']['x'], y=route_conf['origin']['y'], z=route_conf['origin']['z']),
                carla.Rotation(pitch=route_conf['origin']['pitch'], yaw=route_conf['origin']['yaw'],
                         roll=route_conf['origin']['roll']))
            destination_locations = []
            for destination in route_conf['destinations']:
                destination_locations.append(carla.Location(x=destination['x'], y=destination['y'],
                                                      z=destination['z']))

            time_limit = route_conf['time_limit']
        else:
            #carla_map = self.tele_world.carla_map
            spawn_points = CarlaClient.instance.world.get_map().get_spawn_points()
            start_transform = random.choice(spawn_points) if spawn_points else carla.Transform()
            destination_locations = [random.choice(spawn_points).location]
            time_limit = sys.maxsize
        return start_transform, destination_locations, time_limit