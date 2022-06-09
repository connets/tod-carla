import socket
from abc import ABC
from typing import List

from src.actor.TeleActor import TeleActor
from src.communication.NetworkChannel import NetworkChannel
from src.utils.decorators import needs_member


class NetworkNode(TeleActor):

    def __init__(self):
        super().__init__()
        # self._network_delay_manager = NetworkChannel()
        self._channels: List[NetworkChannel] = []
        self._tele_context = None

    def add_channel(self, channel):
        channel.bind(self)
        self._channels.append(channel)

    def set_context(self, tele_context):
        self._tele_context = tele_context

    def send_message(self, network_message):
        for channel in self._channels:
            channel.send(network_message)

    def quit(self):
        for channel in self._channels:
            channel.quit()

    def run(self):
        ...

    @needs_member('_tele_context')
    def start(self):
        for channel in self._channels:
            channel.start(self._tele_context)
        super(NetworkNode, self).start()