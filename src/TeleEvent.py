from abc import ABC, abstractmethod


class TeleEvent(ABC):

    @abstractmethod
    def exec(self, world):
        pass

    def __call__(self, *args, **kwargs):
        print("*******", args, kwargs)
        self.exec(args[0])
