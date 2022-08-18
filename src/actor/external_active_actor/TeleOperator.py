import enum
import threading

from src.actor.external_active_actor.ExternalActiveActor import ExternalActiveActor
from src.carla_omnet.SimulationStatus import SimulationStatus


class TeleOperator(ExternalActiveActor):

    def __init__(self, controller, maximum_time):
        super().__init__()
        self._controller = controller
        self._maximum_time = maximum_time
        self._last_snapshot = None

    # TODO update only if the latest vehicle has less ts
    def receive_vehicle_state_info(self, tele_vehicle_state, timestamp):
        # if timestamp > self._maximum_time:
        #     self._tele_context.finish(TeleSimulator.FinishCode.TIME_LIMIT)
        if self._controller.done():
            return SimulationStatus.FINISHED_OK, None
        elif tele_vehicle_state.collisions:
            return SimulationStatus.FINISHED_ACCIDENT, None
        # else:
        return SimulationStatus.RUNNING, self._controller.do_action(tele_vehicle_state)

        # if command is not None:
        #     self.send_message(InstructionNetworkMessage(command))

    def quit(self):
        ...
