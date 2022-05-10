from src.network.NetworkNode import NetworkNode


class TeleCarlaActor(NetworkNode):
    def __init__(self, host, port):
        super().__init__(host, port)

    def spawn_in_the_world(self, tele_world):
        ...