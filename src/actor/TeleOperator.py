import threading

from src.utils.utils import synchronized


class TeleOperator:
    lock = threading.RLock()

    def __init__(self, controller):
        self._last_snapshot = None
        self._controller = controller

    @synchronized(lock)
    def tick(self):
        if self._last_snapshot is not None:
            ...  # do stuffs

    @synchronized(lock)
    def receive_state_info(self, snapshot):
        self._last_snapshot = snapshot
