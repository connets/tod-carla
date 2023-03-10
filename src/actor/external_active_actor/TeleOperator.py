import enum
import threading

from pycarlanet import SimulatorStatus

from src.actor.external_active_actor.ExternalActiveActor import ExternalActiveActor
from src.carla_omnet.SimulationStatus import SimulationStatus


class TeleOperator(ExternalActiveActor):

    def __init__(self, controller):
        super().__init__()
        self._controller = controller
        self._last_snapshot = None

    # TODO update only if the latest vehicle has less ts
    def receive_vehicle_state_info(self, tele_vehicle_state, timestamp):
        if self._controller.done():
            return SimulatorStatus.FINISHED_OK, None
        elif tele_vehicle_state.collisions:
            return SimulatorStatus.FINISHED_ERROR, None
        # else:
        return SimulatorStatus.RUNNING, self._controller.do_action(tele_vehicle_state)

        # if command is not None:
        #     self.send_message(InstructionNetworkMessage(command))

    def quit(self):
        ...
