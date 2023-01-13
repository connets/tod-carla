from abc import ABC, abstractmethod

import carla
import pygame
from pygame.locals import KMOD_CTRL, KMOD_SHIFT, K_0, K_9, K_BACKQUOTE, K_BACKSPACE, K_COMMA, K_DOWN, K_ESCAPE, K_F1, \
    K_LEFT, K_PERIOD, K_RIGHT, K_SLASH, K_SPACE, K_TAB, K_UP, K_a, K_b, K_c, K_d, K_g, K_h, K_i, K_l, K_m, K_n, K_o, \
    K_p, K_q, K_r, K_s, K_t, K_v, K_w, K_x, K_z, K_MINUS, K_EQUALS

from lib.agents.navigation.basic_agent import BasicAgent
from lib.agents.navigation.behavior_agent import BehaviorAgent
from src.communication.TeleVehicleControl import TeleVehicleControl
from src.utils.decorators import preconditions


class TeleAdapterController(ABC):

    def __init__(self):
        self._tele_vehicle_state = None

    @abstractmethod
    def add_player_in_world(self, player):
        ...

    @abstractmethod
    def do_action(self, vehicle_state):
        ...

    @abstractmethod
    def done(self):
        ...

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

    def update_vehicle_state(self, tele_vehicle_state):
        self._tele_vehicle_state = tele_vehicle_state

    @abstractmethod
    def get_trajectory(self):
        ...


class BasicAgentTeleWorldAdapterController(TeleAdapterController):

    def get_trajectory(self):
        return []

    def __init__(self):
        super().__init__()
        self._player = None
        self.carla_agent = None

    def add_player_in_world(self, player):
        self._player = player
        self.carla_agent = BasicAgent(player.model)

    def do_action(self, vehicle_state=None):
        if vehicle_state is not None:
            self.carla_agent.update_vehicle_state(vehicle_state)

        control = self.carla_agent.run_step()
        control.manual_gear_shift = False
        return control

    def done(self):
        return self.carla_agent.done()


class BehaviorAgentTeleWorldAdapterController(TeleAdapterController):

    def __init__(self, behavior, sampling_resolution, start_location, destination_locations, opt_dict={}):
        super().__init__()
        self._behavior = behavior
        self._sampling_resolution = sampling_resolution
        self._start_location = start_location
        self._destination_locations = destination_locations
        self._opt_dict = opt_dict
        self._player = None
        self.carla_agent = None
        self._waypoints = None

    def add_player_in_world(self, player):
        self._player = player
        self.carla_agent = BehaviorAgent(player.model, self._sampling_resolution, behavior=self._behavior, opt_dict=self._opt_dict)

        self._waypoints = self.carla_agent.set_destinations(*self._destination_locations,
                                                            start_location=self._start_location)

    def _quit(self, event):
        return event.type == pygame.QUIT or (event.type == pygame.KEYUP and self._is_quit_shortcut(event.key))

    @preconditions('carla_agent')
    def do_action(self, vehicle_state):
        if pygame.get_init() and any(self._quit(e) for e in pygame.event.get()):
            return None

        control = None
        if self.carla_agent.last_vehicle_state is None or self.carla_agent.last_vehicle_state.timestamp.elapsed_seconds < vehicle_state.timestamp.elapsed_seconds:
            self.carla_agent.update_vehicle_state(vehicle_state)
            control = TeleVehicleControl(self._player.get_world().get_snapshot().timestamp, self.carla_agent.run_step(True))
        return control

    @preconditions('carla_agent')
    def get_trajectory(self):
        return self._waypoints

    def done(self):
        return self.carla_agent.done()
