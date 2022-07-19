from asyncio import protocols
import zmq


class OmnetCommunicationManager():
    def __init__(self, protocol, host, port, init_timeout, timeout, step_listener=None):
        self.host = host
        self.step_listener = step_listener
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = init_timeout * 1000;
        print("Waiting for connection...")
        self.socket.bind("tcp://*:5555")
        handshake = self.socket.recv()
        self.socket.send(b"Hello")
        print("Connected!")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = timeout * 1000;

    def start(self):
        message = self.socket.recv()
        print(type(message), message.decode("utf-8"))
        self.socket.send(b"Hello")


#  Socket to talk to server
if __name__ == '__main__':
    manager = OmnetCommunicationManager('tcp', 'localhost', 5555, 10, 1)
    manager.start()