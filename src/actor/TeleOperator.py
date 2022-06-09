import threading

from src.TeleConstant import FinishCode
from src.network.NetworkMessage import InstructionNetworkMessage
from src.network.NetworkNode import NetworkNode


class TeleOperator(NetworkNode):
    lock = threading.RLock()

    def __init__(self, controller):
        super().__init__()
        self._last_snapshot = None
        self._controller = controller

    def receive_vehicle_state_info(self, tele_vehicle_state, timestamp):
        if self._controller.done():
            self._tele_context.finish(FinishCode.OK)
        elif tele_vehicle_state.collisions:
            self._tele_context.finish(FinishCode.ACCIDENT)
        else:
            command = self._controller.do_action(tele_vehicle_state)
            self.send_message(InstructionNetworkMessage(command))
