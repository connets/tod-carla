from abc import ABC, abstractmethod

from src.tele_world import TeleWorld


class TeleEvent(ABC):

    @abstractmethod
    def exec(self, world: TeleWorld):
        ...
