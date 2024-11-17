from utils.FolderPath import FolderPath
from listeners.MyWorldManager import MyWorldManager
from listeners.MyActorManager import MyActorManager
from listeners.MyAgentManager import MyAgentManager

from pycarlanet import CarlaClient, ActorType, SocketManager
from utils.CarlaServerHandler import CarlaServerHandler
from utils.InterCommunicationListeners import InterCommunicationListeners
from otherManagers.LoggerManager import LoggerManager
import time

#redirect print on logfile dependecies
import sys
from functools import partial

if __name__ == '__main__':

    #redirect print on logfile for debug purposes
    class TeeOutput:
        def __init__(self, filename):
            self.file = open(filename, 'a')
            self.stdout = sys.stdout
            
        def write(self, data):
            self.file.write(data)
            self.stdout.write(data)
            
        def flush(self):
            self.file.flush()
            self.stdout.flush()
    # Redirect stdout
    sys.stdout = TeeOutput('logfile.txt')
    # Use a partial function to preserve print's other arguments
    print = partial(print, flush=True)

    #start carla server
    CarlaServerHandler()
    CarlaServerHandler.launch_carla_server()
    time.sleep(20)
    #minimal part for co-simulation
    ActorType()
    CarlaClient(host='localhost', port=2000)

    #print(f"CarlaClient {CarlaClient.instance.client.get_available_maps()}")
    wm = MyWorldManager(synchronousMode=True, renderingMode=False)
    acm = MyActorManager()
    agm = MyAgentManager()

    print(f"CarlaClient world {CarlaClient.instance.world}")

    #intercommunication between listeners, not needed for co-simulation. you can pass more managers to handle other thinks just passing them and use their functions calling
    #InterCommunicationListeners.askToManager(self, managerClass, functionName, *args, **kwargs)

    InterCommunicationListeners(wm, acm, agm, LoggerManager())
    
    SocketManager(
        listening_port=5555,
        worldManager=wm,
        actorManager=acm,
        agentManager=agm,
        log_messages=False
    )
    
    SocketManager.instance.start_socket()