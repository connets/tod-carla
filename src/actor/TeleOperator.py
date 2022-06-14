import threading

from src.communication.NetworkMessage import InstructionNetworkMessage
from src.communication.NetworkNode import NetworkNode
from src.core.TeleSimulator import FinishCode


class TeleOperator(NetworkNode):
    lock = threading.RLock()

    def __init__(self, controller):
        super().__init__()
        self._last_snapshot = None
        self._controller = controller

    # TODO update only if the latest vehicle has less ts
    def receive_vehicle_state_info(self, tele_vehicle_state, timestamp):
        if self._controller.done():
            self._tele_context.finish(FinishCode.OK)
        elif tele_vehicle_state.collisions:
            self._tele_context.finish(FinishCode.ACCIDENT)
        else:
            command = self._controller.do_action(tele_vehicle_state)
            if command is not None:
                self.send_message(InstructionNetworkMessage(command))
