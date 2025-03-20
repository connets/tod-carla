import sys, os

from pycarlanet.enum import SimulatorStatus
from pycarlanet import CarlaClient
from pycarlanet.utils import InstanceExist

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.FolderPath import FolderPath
import carla
import yaml, json
from pycarlanet.CarlaClient import CarlaClient

class LoggerManager:

    def open_file_create_dir(self, file_path, mode='r'):
        # Get the directory path
        dir_path = os.path.dirname(file_path)
        
        # Create the directory if it doesn't exist
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # Open and return the file
        return open(file_path, mode)
    
    @InstanceExist(CarlaClient)
    def writeFinishStatus(self, status_code: SimulatorStatus):
        with self.open_file_create_dir(f'{FolderPath.RESULTS_PATH}FINISH_STATUS.txt', 'w') as f:
            f.write(status_code.name)
        CarlaClient.instance.client.stop_recorder()
    
    def writeYAMLconfig(self, config):                
        with self.open_file_create_dir(f'{FolderPath.RESULTS_PATH}carla_configuration.yaml', 'w') as f:
            yaml.dump(config, f)

    @InstanceExist(CarlaClient)
    def saveRGBCameraImage(self, image: carla.Image):
        #save carla.Image to disk
        image.save_to_disk(f'{FolderPath.RESULTS_PATH}RGBCamera/F_{image.frame}')
        #image.save_to_disk(f'{FolderPath.RESULTS_PATH}RGBCamera/T_{CarlaClient.instance.world.get_snapshot().timestamp.frame}')
    
    @InstanceExist(CarlaClient)
    def saveAgentState(self, agent_state):
        def obj_dump(obj):
            loc = obj.transform.location
            rot = obj.transform.rotation
            vel = obj.velocity
            return {
                "position": {"x": loc.x, "y": loc.y, "z": loc.z},
                "rotation": {"pitch": rot.pitch, "yaw": rot.yaw, "roll": rot.roll},
                "velocity": {"x": vel.x, "y": vel.y, "z": vel.z}
            }
        
        dumped_dict = {
            "vehicles": {key: obj_dump(value) for key, value in agent_state["vehicles"].items()},
            "pedestrians": {key: obj_dump(value) for key, value in agent_state["pedestrians"].items()}
        }
        with self.open_file_create_dir(f'{FolderPath.RESULTS_PATH}agentState/F_{CarlaClient.instance.world.get_snapshot().timestamp.frame}', 'w') as f:
            json.dump(dumped_dict, f)