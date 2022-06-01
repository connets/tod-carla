"""
Welcome to CARLA manual control.

Use ARROWS or WASD keys for control.

    W            : throttle
    S            : brake
    A/D          : steer left/right
    Q            : toggle reverse
    Space        : hand-brake
    P            : toggle autopilot
    M            : toggle manual transmission
    ,/.          : gear up/down
    CTRL + W     : toggle constant velocity mode at 60 km/h

    Z/X          : toggle right/left blinker

    TAB          : change sensor position
    ` or N       : next sensor
    [1-9]        : change to sensor [1-9]
    G            : toggle radar visualization
    C            : change weather (Shift+C reverse)
    Backspace    : change vehicle

    V            : Select next map layer (Shift+V reverse)
    B            : Load current selected map layer (Shift+B to unload)

    R            : toggle recording images to disk

    CTRL + R     : toggle recording of simulation (replacing any previous)
    CTRL + P     : start replaying last recorded simulation
    CTRL + +     : increments the start time of the replay by 1 second (+SHIFT = 10 seconds)
    CTRL + -     : decrements the start time of the replay by 1 second (+SHIFT = 10 seconds)

    ESC          : quit
"""
import abc
from abc import ABC, abstractmethod

import carla
import pygame
from pygame.locals import KMOD_CTRL, KMOD_SHIFT, K_0, K_9, K_BACKQUOTE, K_BACKSPACE, K_COMMA, K_DOWN, K_ESCAPE, K_F1, \
    K_LEFT, K_PERIOD, K_RIGHT, K_SLASH, K_SPACE, K_TAB, K_UP, K_a, K_b, K_c, K_d, K_g, K_h, K_i, K_l, K_m, K_n, K_o, \
    K_p, K_q, K_r, K_s, K_t, K_v, K_w, K_x, K_z, K_MINUS, K_EQUALS
from enum import Enum

from lib.agents.navigation.basic_agent import BasicAgent
from lib.agents.navigation.behavior_agent import BehaviorAgent
from src.utils.decorators import needs_member


class TeleController(ABC):

    def __init__(self):
        self._tele_vehicle_state = None

    @abstractmethod
    def add_player_in_world(self, player):
        ...

    @abstractmethod
    def do_action(self, vehicle_state=None):
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

class KeyboardTeleWorldController(TeleController):
    """Class that handles keyboard input."""

    def __init__(self, clock):
        super().__init__()
        self._control = carla.VehicleControl()
        self._lights = carla.VehicleLightState.NONE
        self._steer_cache = 0.0
        self._clock = clock

    def add_player_in_world(self, player):
        self._world = player.get_world()

    def do_action(self, vehicle_state=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return None
                elif event.key == K_BACKSPACE:
                    self._world.restart()
                elif event.key > K_0 and event.key <= K_9:
                    index_ctrl = 0
                    if pygame.key.get_mods() & KMOD_CTRL:
                        index_ctrl = 9
                    self._world.camera_manager.set_sensor(event.key - 1 - K_0 + index_ctrl)
                elif event.key == K_r and not (pygame.key.get_mods() & KMOD_CTRL):
                    self._world.camera_manager.toggle_recording()
                elif event.key == K_MINUS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        self._world.recording_start -= 10
                    else:
                        self._world.recording_start -= 1
                    # self._world.hud.notification("Recording start time is %d" % (self._world.recording_start))
                elif event.key == K_EQUALS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        self._world.recording_start += 10
                    else:
                        self._world.recording_start += 1
                if event.key == K_q:
                    self._control.gear = 1 if self._control.reverse else -1
                elif event.key == K_m:
                    self._control.manual_gear_shift = not self._control.manual_gear_shift
                    self._control.gear = self._world.player.get_control().gear
                elif self._control.manual_gear_shift and event.key == K_COMMA:
                    self._control.gear = max(-1, self._control.gear - 1)
                elif self._control.manual_gear_shift and event.key == K_PERIOD:
                    self._control.gear = self._control.gear + 1
        self._parse_vehicle_keys(pygame.key.get_pressed(), self._clock.get_time())
        self._control.reverse = self._control.gear < 0
        return self._control

    def _parse_vehicle_keys(self, keys, milliseconds):
        if keys[K_UP] or keys[K_w]:
            self._control.throttle = min(self._control.throttle + 0.01, 1.00)
        else:
            self._control.throttle = 0.0

        if keys[K_DOWN] or keys[K_s]:
            self._control.brake = min(self._control.brake + 0.2, 1)
        else:
            self._control.brake = 0

        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            if self._steer_cache > 0:
                self._steer_cache = 0
            else:
                self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            if self._steer_cache < 0:
                self._steer_cache = 0
            else:
                self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.hand_brake = keys[K_SPACE]

    def done(self):
        return False

    def get_trajectory(self):
        return []


class BasicAgentTeleWorldController(TeleController):

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


class BehaviorAgentTeleWorldController(TeleController):

    def __init__(self, behavior, start_location, destination_location):
        super().__init__()
        self._behavior = behavior
        self._start_location = start_location
        self._destination_location = destination_location
        self._player = None
        self.carla_agent = None
        self._waypoints = None

    def add_player_in_world(self, player):
        self._player = player
        self.carla_agent = BehaviorAgent(player.model, behavior=self._behavior)
        self._waypoints = self.carla_agent.set_destination(self._destination_location,
                                                           start_location=self._start_location)
        print("*****")

    def _quit(self, event):
        return event.type == pygame.QUIT or (event.type == pygame.KEYUP and self._is_quit_shortcut(event.key))

    def do_action(self, vehicle_state=None):
        if pygame.get_init() and any(self._quit(e) for e in pygame.event.get()):
            return None

        if vehicle_state is not None:
            self.carla_agent.update_vehicle_state(vehicle_state)

        control = self.carla_agent.run_step(True)
        control.manual_gear_shift = False
        return control

    @needs_member('carla_agent')
    def get_trajectory(self):
        return self._waypoints

    def done(self):
        return self.carla_agent.done()
