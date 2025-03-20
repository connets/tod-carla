import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.FolderPath import FolderPath

import json
import zerorpc

class CarlaServerHandler:
    _instance = None
    _carla_handler = None
    
    def __new__(cls, config):
        if cls._instance is None:
            cls._instance = super(CarlaServerHandler, cls).__new__(cls)
            carla_simulator_host = config['host']
            carla_simulator_port = config['port']
            # start zerorpc communication to handle carla server runniong on different container
            cls._instance._carla_handler = zerorpc.Client()
            cls._instance._carla_handler.connect(f"tcp://{carla_simulator_host}:{carla_simulator_port}")
        return cls._instance
    
    @classmethod
    def launch_carla_server(cls):
        while not cls._instance._carla_handler.reload_simulator():
            ...
        print("launch_carla_server end")
    
    @classmethod
    def close(cls):
        cls._instance._carla_handler.close_simulator()
        cls._instance._carla_handler.close()