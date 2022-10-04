import os

import zmq

if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    messages_path = dir_path + '/messages.txt'

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:5555")

    with open(messages_path, 'rb') as f:
        while (x := next(f, None)) is not None:
            recv_msg = socket.recv()
            print(x)
            socket.send(x)
