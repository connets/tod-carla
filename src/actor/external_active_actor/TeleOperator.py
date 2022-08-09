import enum
import threading

from src.actor.external_active_actor.ExternalActiveActor import ExternalActiveActor


class TeleOperator(ExternalActiveActor):
    class OperatorStatus(enum.Enum):
        RUNNING = 0
        FINISHED_OK = 1
        FINISHED_ACCIDENT = 2
        FINISHED_ERROR = 3

        @classmethod
        def is_finished(cls, status):
            return status in (cls.FINISHED_OK, cls.FINISHED_ACCIDENT, cls.FINISHED_ERROR)

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
            return TeleOperator.OperatorStatus.FINISHED_OK, None
        elif tele_vehicle_state.collisions:
            return TeleOperator.OperatorStatus.FINISHED_ACCIDENT, None
        # else:
        return TeleOperator.OperatorStatus.RUNNING, self._controller.do_action(tele_vehicle_state)

        # if command is not None:
        #     self.send_message(InstructionNetworkMessage(command))

    def quit(self):
        ...
