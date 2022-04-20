from abc import ABC, abstractmethod

from src.carla_bridge.TeleWorld import TeleWorld


class TeleCarlaActor(ABC):
    def __init__(self, tele_world: TeleWorld):
        self.tele_world = tele_world

    @abstractmethod
    def start(self):
        ...
