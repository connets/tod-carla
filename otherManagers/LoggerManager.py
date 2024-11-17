import sys, os

from pycarlanet.enum import SimulatorStatus
from pycarlanet import CarlaClient
from pycarlanet.utils import InstanceExist

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.FolderPath import FolderPath

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