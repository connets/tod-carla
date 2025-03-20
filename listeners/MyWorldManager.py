import carla
import sys
import os
import traceback
import yaml

from pycarlanet.listeners import WorldManager, ActorManager
from pycarlanet.enum import SimulatorStatus, CarlaMaplayers
from pycarlanet import CarlaClient
from pycarlanet.utils import InstanceExist


#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.FolderPath import FolderPath
from utils.CarlaServerHandler import CarlaServerHandler
from utils.InterCommunicationListeners import InterCommunicationListeners
from otherManagers.LoggerManager import LoggerManager
import utils.YAMLLoader as YAMLLoader

class MyWorldManager(WorldManager):    
    @InstanceExist(CarlaClient)
    def omnet_init_completed(self, message) -> SimulatorStatus:
        #define folder for results as run_id
        FolderPath.RESULTS_PATH += f"{message['run_id']}/"
        #open user defined configuration file
        data = YAMLLoader.load_and_merge_yaml_file(f"{FolderPath.CONFIGURATION_PATH}{message['user_defined']['config_name']}.yaml")
        InterCommunicationListeners.instance.askToManager(LoggerManager, 'writeYAMLconfig', data)
        # with open(f"{FolderPath.CONFIGURATION_PATH}{message['user_defined']['config_name']}.yaml", 'r') as file:
        #         #data = json.load(file)
        #         data = yaml.safe_load(file)
        worldName = data['world']
                
        super().omnet_init_completed(message=message)
        super().load_world(worldName=worldName,layer_to_unload=[CarlaMaplayers.Buildings, CarlaMaplayers.ParkedVehicles, CarlaMaplayers.Foliage]) #[x for x in CarlaMaplayers]
        self.tick()

        if 'spectator' in data:
            self._spectator = carla.Transform(
                carla.Location(
                    x=data['spectator']['x'],
                    y=data['spectator']['y'],
                    z=data['spectator']['z']
                ),
                carla.Rotation(
                    pitch=data['spectator']['pitch'],
                    yaw=data['spectator']['yaw'],
                    roll=data['spectator']['roll']
                )
            )


        dir_path = os.path.dirname(f'{FolderPath.RESULTS_PATH}recording.log')
        
        # Create the directory if it doesn't exist
        if dir_path and not os.path.exists(dir_path): os.makedirs(dir_path)
        CarlaClient.instance.client.start_recorder(f'{FolderPath.RESULTS_PATH}recording.log')
        #self.world.set_weather(carla.WeatherParameters.ClearNight)
        #self.tick()
        # traffic_manager = CarlaClient.instance.client.get_trafficmanager()
        # traffic_manager.set_synchronous_mode(self._synchronousMode)
        # traffic_manager.set_random_device_seed(message['carla_configuration']['seed'])
        # self.tick()

        self.sim_time_limit = message['carla_configuration']['sim_time_limit'] - 1

        return SimulatorStatus.RUNNING
    
    @InstanceExist(CarlaClient)
    def before_world_tick(self, timestamp):
        if self._spectator:
            # Get the spectator from the world
            spectator = CarlaClient.instance.world.get_spectator()
            # Set the camera view
            spectator.set_transform(self._spectator)

    def after_world_tick(self, timestamp) -> SimulatorStatus:
        #print(f"{timestamp} of {self.sim_time_limit}")
        #if InterCommunicationListeners.instance.askToManager(ActorManager, 'check_hero_crash'):
        #    return SimulatorStatus.FINISHED_OK
        if InterCommunicationListeners.instance.askToManager(ActorManager, 'check_hero_destination_reached'):
            return SimulatorStatus.FINISHED_OK
        if timestamp > self.sim_time_limit:
            return SimulatorStatus.FINISHED_TIME_LIMIT
        
        return SimulatorStatus.RUNNING

    def generic_message(self, timestamp, message) -> (SimulatorStatus, dict):
        ...

    def simulation_finished(self, status_code):
        InterCommunicationListeners.instance.askToManager(LoggerManager, 'writeFinishStatus', status_code)
        exit()
        #self.writeFinishStatus(status_code)

    def simulation_error(self, e):
        print(traceback.format_exc())
        print(f"Warning: Exception {e.__class__.__name__} {e}")
        CarlaServerHandler.close()
        InterCommunicationListeners.instance.askToManager(LoggerManager, 'writeFinishStatus', SimulatorStatus.FINISHED_ERROR)
        #self.writeFinishStatus(SimulatorStatus.FINISHED_ERROR)

    #def writeFinishStatus(self, status_code: SimulatorStatus):
    #    with open(f'{FolderPath.RESULTS_PATH}/FINISH_STATUS.txt', 'w') as f:
    #        f.write(status_code.name)