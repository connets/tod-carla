import threading

from src.communication.NetworkMessage import InstructionNetworkMessage
from src.communication.NetworkNode import NetworkNode
from src.core.TeleSimulator import TeleSimulator


class TeleOperator:
    lock = threading.RLock()

    def __init__(self, controller, maximum_time):
        super().__init__()
        self._controller = controller
        self._maximum_time = maximum_time
        self._last_snapshot = None

    # TODO update only if the latest vehicle has less ts
    def receive_vehicle_state_info(self, tele_vehicle_state, timestamp):
        # if timestamp > self._maximum_time:
        #     self._tele_context.finish(TeleSimulator.FinishCode.TIME_LIMIT)
        # if self._controller.done():
        #     self._tele_context.finish(TeleSimulator.FinishCode.OK)
        # elif tele_vehicle_state.collisions:
        #     self._tele_context.finish(TeleSimulator.FinishCode.ACCIDENT)
        # else:
        return self._controller.do_action(tele_vehicle_state)

            # if command is not None:
            #     self.send_message(InstructionNetworkMessage(command))
