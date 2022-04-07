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


class TeleController(ABC):

    @abstractmethod
    def add_player_in_world(self, player):
        ...

    @abstractmethod
    def do_action(self, clock):
        ...

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)



class KeyboardTeleWorldController(TeleController):
    """Class that handles keyboard input."""

    def __init__(self, camera_manager):
        # self._autopilot_enabled = start_in_autopilot
        self._control = carla.VehicleControl()
        self._lights = carla.VehicleLightState.NONE
        # world.player.set_autopilot(self._autopilot_enabled)
        # world.player.set_light_state(self._lights)
        self._steer_cache = 0.0
        self._camera_manager = camera_manager

    def add_player_in_world(self, player):
        self._world = player.get_world()

    def do_action(self, clock):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return None
                elif event.key == K_BACKSPACE:
                    #     if self._autopilot_enabled:
                    #         world.player.set_autopilot(False)
                    #         world.restart()
                    #         world.player.set_autopilot(True)
                    #     else:
                    self._world.restart()
                # elif event.key == K_TAB:
                #     self._world.camera_manager.toggle_camera()
                # elif event.key == K_g:
                #     self._world.toggle_radar()
                # elif event.key == K_BACKQUOTE:
                #     self._world.camera_manager.next_sensor()
                # elif event.key == K_n:
                #     self._world.camera_manager.next_sensor()
                # elif event.key == K_w and (pygame.key.get_mods() & KMOD_CTRL):
                #     if self._world.constant_velocity_enabled:
                #         self._world.player.disable_constant_velocity()
                #         self._world.constant_velocity_enabled = False
                #         self._world.hud.notification("Disabled Constant Velocity Mode")
                #     else:
                #         self._world.player.enable_constant_velocity(carla.Vector3D(17, 0, 0))
                #         self._world.constant_velocity_enabled = True
                #         self._world.hud.notification("Enabled Constant Velocity Mode at 60 km/h")

                # elif event.key == K_t:
                #     if self._world.show_vehicle_telemetry:
                #         self._world.player.show_debug_telemetry(False)
                #         self._world.show_vehicle_telemetry = False
                #         self._world.hud.notification("Disabled Vehicle Telemetry")
                #     else:
                #         try:
                #             self._world.player.show_debug_telemetry(True)
                #             self._world.show_vehicle_telemetry = True
                #             self._world.hud.notification("Enabled Vehicle Telemetry")
                #         except Exception:
                #             pass
                elif event.key > K_0 and event.key <= K_9:
                    index_ctrl = 0
                    if pygame.key.get_mods() & KMOD_CTRL:
                        index_ctrl = 9
                    self._world.camera_manager.set_sensor(event.key - 1 - K_0 + index_ctrl)
                elif event.key == K_r and not (pygame.key.get_mods() & KMOD_CTRL):
                    self._world.camera_manager.toggle_recording()
                # elif event.key == K_r and (pygame.key.get_mods() & KMOD_CTRL):
                #     if (self._world.recording_enabled):
                #         client.stop_recorder()
                #         self._world.recording_enabled = False
                #         self._world.hud.notification("Recorder is OFF")
                #     else:
                #         client.start_recorder("manual_recording.rec")
                #         self._world.recording_enabled = True
                #         self._world.hud.notification("Recorder is ON")
                # elif event.key == K_p and (pygame.key.get_mods() & KMOD_CTRL):
                #     # stop recorder
                #     client.stop_recorder()
                #     self._world.recording_enabled = False
                #     # work around to fix camera at start of replaying
                #     current_index = self._world.camera_manager.index
                #     self._world.destroy_sensors()
                #     # disable autopilot
                #     self._autopilot_enabled = False
                #     self._world.player.set_autopilot(self._autopilot_enabled)
                #     self._world.hud.notification("Replaying file 'manual_recording.rec'")
                #     # replayer
                #     client.replay_file("manual_recording.rec", self._world.recording_start, 0, 0)
                #     self._world.camera_manager.set_sensor(current_index)
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
                    # self._world.hud.notification("Recording start time is %d" % (self._world.recording_start))
                # if isinstance(self._control, carla.VehicleControl):
                if event.key == K_q:
                    self._control.gear = 1 if self._control.reverse else -1
                elif event.key == K_m:
                    self._control.manual_gear_shift = not self._control.manual_gear_shift
                    self._control.gear = self._world.player.get_control().gear
                    # self._world.hud.notification('%s Transmission' % ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                elif self._control.manual_gear_shift and event.key == K_COMMA:
                    self._control.gear = max(-1, self._control.gear - 1)
                elif self._control.manual_gear_shift and event.key == K_PERIOD:
                    self._control.gear = self._control.gear + 1
                # elif event.key == K_p and not pygame.key.get_mods() & KMOD_CTRL:
                #     if not self._autopilot_enabled and not sync_mode:
                #         print("WARNING: You are currently in asynchronous mode and could " + "experience some issues with the traffic simulation")
                #     self._autopilot_enabled = not self._autopilot_enabled
                #     self._world.player.set_autopilot(self._autopilot_enabled)
                # self._world.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
                # elif event.key == K_l and pygame.key.get_mods() & KMOD_CTRL:
                #     current_lights ^= carla.VehicleLightState.Special1
                # elif event.key == K_l and pygame.key.get_mods() & KMOD_SHIFT:
                #     current_lights ^= carla.VehicleLightState.HighBeam
                # elif event.key == K_l:
                # Use 'L' key to switch between lights:
                # closed -> position -> low beam -> fog
                # if not self._lights & carla.VehicleLightState.Position:
                # self._world.hud.notification("Position lights")
                # current_lights |= carla.VehicleLightState.Position
                # else:
                # self._world.hud.notification("Low beam lights")
                # current_lights |= carla.VehicleLightState.LowBeam
                # if self._lights & carla.VehicleLightState.LowBeam:
                # self._world.hud.notification("Fog lights")
                # current_lights |= carla.VehicleLightState.Fog
                # if self._lights & carla.VehicleLightState.Fog:
                # self._world.hud.notification("Lights off")
                # current_lights ^= carla.VehicleLightState.Position
                # current_lights ^= carla.VehicleLightState.LowBeam
                # current_lights ^= carla.VehicleLightState.Fog
                # elif event.key == K_i:
                #     current_lights ^= carla.VehicleLightState.Interior
                # elif event.key == K_z:
                #     current_lights ^= carla.VehicleLightState.LeftBlinker
                # elif event.key == K_x:
                #     current_lights ^= carla.VehicleLightState.RightBlinker

        # if not self._autopilot_enabled:
        # if isinstance(self._control, carla.VehicleControl):
        self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
        self._control.reverse = self._control.gear < 0
        # Set automatic control-related vehicle lights
        # if self._control.brake:
        #     current_lights |= carla.VehicleLightState.Brake
        # else:  # Remove the Brake flag
        #     current_lights &= ~carla.VehicleLightState.Brake
        # if self._control.reverse:
        #     current_lights |= carla.VehicleLightState.Reverse
        # else:  # Remove the Reverse flag
        #     current_lights &= ~carla.VehicleLightState.Reverse
        # if current_lights != self._lights:  # Change the light state only if necessary
        #     self._lights = current_lights
        #     self._world.player.set_light_state(carla.VehicleLightState(self._lights))
        # elif isinstance(self._control, carla.WalkerControl):
        #     self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time(), self._world)
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



class BasicAgentTeleWorldController(TeleController):

    def __init__(self):
        self._player = None
        self.carla_agent = None

    def add_player_in_world(self, player):
        self._player = player
        self.carla_agent = BasicAgent(player.model)

    def do_action(self, clock):
        control = self.carla_agent.run_step()
        control.manual_gear_shift = False
        return control


class BehaviorAgentTeleWorldController(TeleController):

    def __init__(self, behavior, destination_position):
        self._behavior = behavior
        self._destination_position = destination_position
        self._player = None
        self.carla_agent = None

    def add_player_in_world(self, player):
        self._player = player
        self.carla_agent = BehaviorAgent(player.model, behavior=self._behavior)
        self.carla_agent.set_destination(self._destination_position)

    def _quit(self, event):
        return event.type == pygame.QUIT or (event.type == pygame.KEYUP and self._is_quit_shortcut(event.key))

    def do_action(self, clock):
        if any(self._quit(e) for e in pygame.event.get()):
            return None

        control = self.carla_agent.run_step()
        control.manual_gear_shift = False
        return control
