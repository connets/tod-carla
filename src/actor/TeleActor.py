import socket
from abc import ABC
from typing import List

from src.utils.decorators import preconditions


class TeleActor(ABC):

    def __init__(self):
        ...

    def start(self):
        ...

    def quit(self):
        ...
