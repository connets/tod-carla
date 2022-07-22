from abc import abstractmethod, ABC
from enum import Enum

from lib.carla_omnet.CarlaOmnetManager import CarlaOmnetManager
from src.communication.NetworkNode import NetworkNode
from src.core.TeleContext import TeleContext
from src.actor.TeleCarlaActor import TeleCarlaActor


class Simulator(ABC):
    class FinishCode(Enum):
        OK = 0
        ACCIDENT = 1
        TIME_LIMIT = 2

    def __init__(self, tele_world, clock):
        self._tele_world = tele_world
        self._clock = clock

        self._tick_listeners = set()
        self._step_callbacks = set()
        self._finished = False
        self._finish_code = None

        self._actors = []

        self._tele_context = TeleContext(tele_world.timestamp.elapsed_seconds, self.finish)

    def finish(self, finish_code):
        self._finish_code = finish_code
        self._finished = True

    @property
    def tele_world(self):
        return self._tele_world

    def add_actor(self, actor):
        self._actors.append(actor)
        actor.set_context(self._tele_context)
        if isinstance(actor, NetworkNode):
            actor.set_network_context(self._tele_context)
        if isinstance(actor, TeleCarlaActor):
            actor.spawn_in_the_world(self._tele_world)

    @property
    @abstractmethod
    def _network_context(self):
        ...

    def add_tick_listener(self, listener):
        self._tick_listeners.add(listener)

    def add_step_listener(self, callback):
        self._step_callbacks.add(callback)

    # def start(self):
    #     for actor in self._actors:
    #         actor.set_context(self._tele_context)
    #         if isinstance(actor, TeleCarlaActor):
    #             actor.spawn_in_the_world(self._tele_world)
    #         actor.start()

    @abstractmethod
    def do_simulation(self):
        ...

    # go ahead with simulation until timestamp
    def do_simulation_step(self, limit_timestamp):
        has_scheduled_events_before = self._tele_context.has_scheduled_events(limit_timestamp)
        while not self._finished and (
                limit_timestamp > self._tele_world.timestamp.elapsed_seconds or has_scheduled_events_before):
            # network_delay.tick()

            has_scheduled_events_before &= self._tele_context.has_scheduled_events(limit_timestamp)

            next_simulator_timestamp = round(
                self._tele_context.next_timestamp_event if has_scheduled_events_before else limit_timestamp, 6)
            while next_simulator_timestamp > self._tele_world.timestamp.elapsed_seconds:
                self._clock.tick()
                self._tele_world.tick()
                for listener in self._tick_listeners:
                    listener(self._tele_world.timestamp)

            # busy waiting for attending the last data sensors
            while any(not actor.done(self._tele_world.timestamp) for actor in self._actors):
                ...
            if has_scheduled_events_before:
                for callback in self._step_callbacks: callback(self._tele_world.timestamp)
                self._tele_context.run_next_event()
            print("**** => ", has_scheduled_events_before)

            # data_collector.tick()
            # print(sim_world.get_snapshot().timestamp)
        ...


class TODSimulator(Simulator):

    def __init__(self, tele_world, clock):
        super().__init__(tele_world, clock)

    @property
    def _network_context(self):
        return self._tele_context

    def do_simulation(self):
        for actor in self._actors:
            actor.start()
        while not self._finished and self._tele_context.has_scheduled_events():
            self.do_simulation_step(self._tele_context.next_timestamp_event)

        self._tele_world.quit()
        for actor in self._actors:
            actor.quit()

        return self._finish_code


class CarlaOmnetSimulator(Simulator):

    def __init__(self, tele_world, clock, carla_omnet_manager: CarlaOmnetManager):
        super().__init__(tele_world, clock)
        self._carla_omnet_manager = carla_omnet_manager

    @property
    def _network_context(self):
        return self._carla_omnet_manager

    def do_simulation(self):
        for actor in self._actors:
            actor.start()

        self._carla_omnet_manager.start(lambda ts: self.do_simulation_step(ts))
        self._tele_world.quit()
        for actor in self._actors:
            actor.quit()

        return self._finish_code
