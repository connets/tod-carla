from abc import ABC, abstractmethod

from src.carla_bridge.TeleWorld import TeleWorld
from src.network.NetworkNode import NetworkNode


class TeleCarlaActor(NetworkNode):
    def __init__(self, host, port, tele_world: TeleWorld):
        super().__init__(host, port)
        self.tele_world = tele_world
