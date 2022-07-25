import abc
from queue import PriorityQueue

from lib.carla_omnet.CarlaOmnetManager import CarlaOmnetManager
from src.TeleOutputWriter import TeleLogger
from src.core import TeleEvent
from src.utils.decorators import preconditions


class TeleContext(abc.ABC):
    def __init__(self):
        self.finish_code = None
        self.finished = False
        self._queue = PriorityQueue()
        self._timestamp = self._initial_timestamp = None
        self._finish_callback = None
        # self._finished = False

    def start(self, initial_timestamp, finish_callback):
        self._initial_timestamp = initial_timestamp
        self._timestamp = initial_timestamp
        self._finish_callback = finish_callback

    @property
    def timestamp(self):
        return self._timestamp

    def current_duration(self):
        return self._timestamp - self._initial_timestamp

    @abc.abstractmethod
    def next_timestamp_event(self):
        ...

    @abc.abstractmethod
    def has_runnable_events(self, timestamp_limit=None):
        ...

    @preconditions('_timestamp')
    def schedule(self, event, s):
        # print("-"*5, self._timestamp_func(), ms, self._timestamp_func() + ms)
        if all(hasattr(event, attr) for attr in ['log_event', 'name_event']) and event.log_event:
            TeleLogger.instance.event_logger.write(self._timestamp, 'scheduled', event)
        # if not self._finished:

    @preconditions('_queue', valid=lambda q: not q.empty())
    def run_next_event(self):
        timing_event = self._queue.get()
        event = timing_event.event
        self._timestamp = timing_event.timestamp

        if all(hasattr(event, attr) for attr in ['log_event', 'name_event']) and event.log_event:
            TeleLogger.instance.event_logger.write(self._timestamp, 'executed', event)
        event()

    def finish(self, finish_code):
        self.finished = True
        self.finish_code = finish_code
        self._finish_callback(finish_code)

    @abc.abstractmethod
    def _schedule(self, event, s):
        ...

    class TimingEvent:
        def __init__(self, event, timestamp):
            self.event = event
            self.timestamp = timestamp

        def __lt__(self, e):
            return self.timestamp < e.timestamp

        @property
        def timestamp_scheduled(self):
            return self.timestamp


class TODTeleContext(TeleContext):

    @property
    def next_timestamp_event(self):
        return self._queue.queue[0].timestamp if not self._queue.empty() else None

    def has_runnable_events(self, timestamp_limit=None):
        """
                if not self._queue.empty():
                    return timestamp_limit is None or self._queue.queue[0].timestamp <= timestamp_limit
                """
        return not self._queue.empty() and (
                timestamp_limit is None or self._queue.queue[0].timestamp <= timestamp_limit)

    def _schedule(self, event, s):
        print("***** => ")
        self._queue.put(self.TimingEvent(event, self._timestamp + s))


class CarlaOmnetTeleContext(TeleContext):

    @property
    def next_timestamp_event(self):
        return self._queue.queue[0].timestamp if not self._queue.empty() and self._queue.queue[
            0] <= self._carla_omnet_manager.timestamp else self.timestamp

    def __init__(self, carla_omnet_manager):
        super().__init__()
        self._carla_omnet_manager: CarlaOmnetManager = carla_omnet_manager

    def run_next_event(self):
        if self._queue.queue[0].timestamp <= self._carla_omnet_manager.timestamp:
            super(CarlaOmnetTeleContext, self).run_next_event()
        else:
            action = self._carla_omnet_manager.do_omnet_step()
            if action is not None:
                self._queue.put(self.TimingEvent(action, self._timestamp))

    def _schedule(self, event, s):
        if event.event_type == TeleEvent.EventType.NETWORK:
            self._carla_omnet_manager.schedule_message(event)
        else:
            self._queue.put(self.TimingEvent(event, self._timestamp + s))

    def has_runnable_events(self, timestamp_limit=None):
        if not self._queue.empty():
            if self._queue.queue[0].timestmap <= self._carla_omnet_manager.timestamp:
                return True
            else:
                ...
                return True
        return False
