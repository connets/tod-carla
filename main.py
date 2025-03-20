from utils.FolderPath import FolderPath
from listeners.MyWorldManager import MyWorldManager
from listeners.MyActorManager import MyActorManager
from listeners.MyAgentManager import MyAgentManager

from pycarlanet import CarlaClient, ActorType, SocketManager
from utils.CarlaServerHandler import CarlaServerHandler
from utils.InterCommunicationListeners import InterCommunicationListeners
from otherManagers.LoggerManager import LoggerManager
import time
import yaml

#redirect print on logfile dependecies
#import sys
#from functools import partial
import argparse

if __name__ == '__main__':

    # #redirect print on logfile for debug purposes
    # class TeeOutput:
    #     def __init__(self, filename):
    #         self.file = open(filename, 'a')
    #         self.stdout = sys.stdout
            
    #     def write(self, data):
    #         self.file.write(data)
    #         self.stdout.write(data)
            
    #     def flush(self):
    #         self.file.flush()
    #         self.stdout.flush()
    # # Redirect stdout
    # sys.stdout = TeeOutput('logfile.txt')
    # # Use a partial function to preserve print's other arguments
    # print = partial(print, flush=True)

    renderingMode = False

    parser = argparse.ArgumentParser(description="Process the render argument.")

    # Add the -render argument with a default value of False
    parser.add_argument('-render', type=str, default='false', help='Enable or disable rendering')
    # Parse the arguments
    args = parser.parse_args()
    # Check the value of the 'render' argument
    if args.render.lower() == 'true': renderingMode = True

    print(f"rendering: {renderingMode}")
    
    

    file = open(f'{FolderPath.CONFIGURATION_PATH}server.yaml', 'r')
    serverConfig = yaml.safe_load(file)
    file.close()

    if "zerorpc" not in serverConfig or "carla" not in serverConfig:
        print("Error: server.yaml file is not valid")
        exit(1)
    
    if \
    "host" not in serverConfig["zerorpc"] or \
    "port" not in serverConfig["zerorpc"] or \
    "host" not in serverConfig["carla"] or \
    "port" not in serverConfig["carla"]:
        print("Error: server.yaml file is not valid")
        exit(1)



    #start carla server
    CarlaServerHandler(config=serverConfig["zerorpc"])
    CarlaServerHandler.launch_carla_server()
    time.sleep(20)
    #minimal part for co-simulation
    ActorType()
    CarlaClient(host=serverConfig["carla"]["host"], port=serverConfig["carla"]["port"])

    #print(f"CarlaClient {CarlaClient.instance.client.get_available_maps()}")
    wm = MyWorldManager(synchronousMode=True, renderingMode=renderingMode)
    acm = MyActorManager()
    agm = MyAgentManager()
    
    try:
        print(f"CarlaClient test calling server version: response -> {CarlaClient.instance.client.get_server_version()}")
    except Exception as e:
        print(f"Error during CarlaClient test calling : {e}")
        exit(1)
        
    #intercommunication between listeners, not needed for co-simulation. you can pass more managers to handle other thinks just passing them and use their functions calling
    #InterCommunicationListeners.askToManager(self, managerClass, functionName, *args, **kwargs)
    InterCommunicationListeners(wm, acm, agm, LoggerManager())
    
    SocketManager(
        listening_port=5555,
        worldManager=wm,
        actorManager=acm,
        agentManager=agm,
        log_messages=True
    )
    
    SocketManager.instance.start_socket()