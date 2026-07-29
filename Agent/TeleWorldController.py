import os, sys

from abc import ABC, abstractmethod


import carla
import pygame
from pygame.locals import KMOD_CTRL, KMOD_SHIFT, K_0, K_9, K_BACKQUOTE, K_BACKSPACE, K_COMMA, K_DOWN, K_ESCAPE, K_F1, \
    K_LEFT, K_PERIOD, K_RIGHT, K_SLASH, K_SPACE, K_TAB, K_UP, K_a, K_b, K_c, K_d, K_g, K_h, K_i, K_l, K_m, K_n, K_o, \
    K_p, K_q, K_r, K_s, K_t, K_v, K_w, K_x, K_z, K_MINUS, K_EQUALS

from pycarlanet.utils import preconditions, ObjectStorage
from pycarlanet import CarlaClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.agents.navigation.basic_agent import BasicAgent
from lib.agents.navigation.behavior_agent import BehaviorAgent
from utils.TeleVehicleControl import TeleVehicleControl

from Agent.MyBehaviorAgent import MyBehaviorAgent
from utils.InterCommunicationListeners import InterCommunicationListeners
from otherManagers.LoggerManager import LoggerManager

class TeleAdapterController(ABC):

    def __init__(self):
        self._tele_vehicle_state = None

    @abstractmethod
    def do_action(self, vehicle_state, loss_ratio=0.0):
        ...

    def minimum_risk_maneuver(self):
        """
        Minimum risk maneuver decided by the car when the control channel does not
        receive instruction for more than the limit imposed by the yaml.

        If this method is not implemented yet, return None and the car executes the
        last received instruction.
        """
        return None

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

    def __init__(self, player, loss_ratio_threshold=0.5):

        super().__init__()
        self._player = player
        self.carla_agent = BasicAgent(player.carla_actor) #player.model is the carla.Vehicle wrapped in player that is a TeleCarlaVehicle
        self._loss_ratio_threshold = loss_ratio_threshold

    def do_action(self, vehicle_state=None, loss_ratio=0.0):
        if vehicle_state is not None:
            self.carla_agent.update_vehicle_state(vehicle_state)

        # if loss_ratio is over the threshold the vehicle does an emergency stop
        if loss_ratio >= self._loss_ratio_threshold:
            control = self.carla_agent.add_emergency_stop(carla.VehicleControl())
        else:
            control = self.carla_agent.run_step()
        control.manual_gear_shift = False
        return control

    def done(self):
        return self.carla_agent.done()


class BehaviorAgentTeleWorldAdapterController(TeleAdapterController):

    def __init__(self, agentId, player, behavior, sampling_resolution, start_location, destination_locations, opt_dict={},
                 loss_ratio_threshold=0.5, control_timeout=0.5):
        super().__init__()
        self._behavior = behavior
        self._sampling_resolution = sampling_resolution
        self._start_location = start_location
        self._destination_locations = destination_locations
        self._opt_dict = opt_dict
        self._player = player
        self._agentId = agentId
        self.carla_agent = MyBehaviorAgent(player.carla_actor, self._sampling_resolution, behavior=self._behavior, opt_dict=self._opt_dict)

        self._waypoints = self.carla_agent.set_destinations(*self._destination_locations, start_location=self._start_location)

        # Limit of loss packet over which the actor does the minimum risk action
        self._loss_ratio_threshold = loss_ratio_threshold

        # Dead-man's switch: seconds of silence on the control channel after which
        # the vehicle performs the minimum risk maneuver on its own. Read by the
        # actor manager, which is the one watching the clock.
        self.control_timeout = control_timeout

        self.othersStates = {}

    def _quit(self, event):
        return event.type == pygame.QUIT or (event.type == pygame.KEYUP and self._is_quit_shortcut(event.key))

    @preconditions('carla_agent')
    def do_action(self, vehicle_state, loss_ratio=0.0):
        #if pygame.get_init() and any(self._quit(e) for e in pygame.event.get()):
        #    return None

        #print("self._agents[actor_id].do_action")
        #print("self.carla_agent.last_vehicle_state: ", self.carla_agent.last_vehicle_state)
        #if self.carla_agent.last_vehicle_state is not None:
        #    print(f"self.carla_agent.last_vehicle_state.timestamp.elapsed_seconds {self.carla_agent.last_vehicle_state.timestamp.elapsed_seconds}\n")
        #    print(f"vehicle_state.timestamp.elapsed_seconds {vehicle_state.timestamp.elapsed_seconds}\n{self.carla_agent.last_vehicle_state.timestamp.elapsed_seconds < vehicle_state.timestamp.elapsed_seconds}\n")
        #print(self.carla_agent.last_vehicle_state.timestamp.elapsed_seconds < vehicle_state.timestamp.elapsed_seconds)
        control = None


        def generate_union(obstacles, otherObjects, otherTimestamp):
            ids = [o.id for o in obstacles]
            tMine = CarlaClient.instance.world.get_snapshot().timestamp
            for obj in otherObjects:
                #check if the object is already in the list
                if obj.id in ids: continue
                #calculate new position based on velocity vector?
                deltaSeconds = tMine.elapsed_seconds - otherTimestamp.elapsed_seconds
                obj.timestamp = tMine
                obj.transform.location = carla.Location(
                    x=obj.transform.location.x + obj.velocity.x * deltaSeconds,
                    y=obj.transform.location.y + obj.velocity.y * deltaSeconds,
                    z=obj.transform.location.z + obj.velocity.z * deltaSeconds
                )
                obstacles.append(obj)

            return obstacles
        
        #add to vehicle_state recevied also the states of the other agents coop received
        for _,state in self.othersStates.items():
            visible_vehicles = generate_union(vehicle_state.visible_vehicles, state.visible_vehicles, state.timestamp)
            visible_pedestrians = generate_union(vehicle_state.visible_pedestrians, state.visible_pedestrians, state.timestamp)
            vehicle_state.visible_vehicles = visible_vehicles
            vehicle_state.visible_pedestrians = visible_pedestrians

        if self.carla_agent.last_vehicle_state is None or self.carla_agent.last_vehicle_state.timestamp.elapsed_seconds < vehicle_state.timestamp.elapsed_seconds:
            state = self.carla_agent.update_vehicle_state(vehicle_state)
            InterCommunicationListeners.instance.askToManager(LoggerManager, 'saveAgentState', state)
            timestamp = self._player.carla_actor.get_world().get_snapshot().timestamp

            """
            If the loss ratio is above the threshold the car applies an emergency
            stop.
            Drastic decision that could be changed
            """
            if loss_ratio >= self._loss_ratio_threshold:
                print(f"[loss_ratio] {loss_ratio:.3f} >= soglia {self._loss_ratio_threshold}: emergency stop")
                vehicle_control = self.carla_agent.emergency_stop()
            else:
                vehicle_control = self.carla_agent.run_step(True)
            control = TeleVehicleControl(timestamp, vehicle_control)

        return control

    @preconditions('carla_agent')
    def minimum_risk_maneuver(self):
        """
        Emergency break executed by the car when the control channel does not
        receive any more instruction for at least the time given in the yaml
        """
        timestamp = self._player.carla_actor.get_world().get_snapshot().timestamp
        return TeleVehicleControl(timestamp, self.carla_agent.emergency_stop())

    @preconditions('carla_agent')
    def get_trajectory(self):
        return self._waypoints

    def done(self):
        return self.carla_agent.done()

    def handle_cooperative_update(self, status_id):
        #print("handle_cooperative_update agent")
        state = ObjectStorage.get(status_id)
        if state.id not in self.othersStates:
            self.othersStates[state.id] = state
            return
        if state.timestamp.elapsed_seconds > self.othersStates[state.id].timestamp.elapsed_seconds:
            self.othersStates[state.id] = state
            return