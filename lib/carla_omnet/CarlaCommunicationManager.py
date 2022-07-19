import zmq
import json

class CarlaOmnetError(RuntimeError):
    ...

class CarlaOmnetCommunicationError(CarlaOmnetError):
    ...

class UnknownMessageCarlaOmnetError(RuntimeError):
    def __init__(self, unknown_msg):
        self.unknown_msg = unknown_msg

    def __repr__(self) -> str:
        return "I don't know how to handle the following msg: " + self.unknown_msg


class OmnetCommunicationManager():


    def __init__(self, protocol, port, init_timeout, timeout, step_listener=None):
        self.step_listener = step_listener
        self._queued_messages = dict()

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"{protocol}://*:{port}")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = init_timeout * 1000

        print("Waiting for connection...")
        handshake = self._receive_data()
        print(handshake)
        self.socket.send(b"Hello")

        print("Connected!")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = timeout * 1000

    def _receive_data(self):
        message = self.socket.recv()
        return json.loads(message.decode("utf-8"))

    def start(self):
        message = self._receive_data()
        if message.type == 'simulation_step':
            ...
        elif message.type == 'receive_msg':
            ...
        else:
            ...
        self.socket.send(b"Hello")


#  Socket to talk to server
if __name__ == '__main__':
    manager = OmnetCommunicationManager('tcp', 5555, 1, 1)
    manager.start()
