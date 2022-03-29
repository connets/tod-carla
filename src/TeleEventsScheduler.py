from abc import ABC, abstractmethod

from src.TeleEvent import TeleEvent


class TeleEventScheduler(ABC):
    @abstractmethod
    def schedule(self, ns: int, tele_event: TeleEvent):
        pass
