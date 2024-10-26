from abc import ABC, abstractmethod

class TeleCarlaSensor(ABC):
    sensor = None
    def stop(self):
        ...

    @abstractmethod
    def destroy(self):
        ...

    """
    Create the sensor and attach to the carla actor.
    """
    def attach_to_actor(self, parent_actor):
        ...

    def attach_data(self, vehicle_state):
        ...

    def done(self, timestamp):
        return True


class TeleCarlaRenderingSensor(TeleCarlaSensor):
    @abstractmethod
    def render(self):
        ...
