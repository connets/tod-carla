from abc import ABC, abstractmethod

from src.TeleWorld import TeleWorld


class TeleEvent(ABC):

    @abstractmethod
    def exec(self, world: TeleWorld):
        ...
