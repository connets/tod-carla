import socket
from abc import ABC
from typing import List

from src.utils.decorators import needs_member


class TeleActor(ABC):

    def __init__(self):
        self._tele_context = None

    def set_context(self, tele_context):
        self._tele_context = tele_context

    def quit(self):
        ...

    def run(self):
        ...

    @needs_member('_tele_context')
    def start(self):
        self.run()

    def done(self, timestamp):
        return True
