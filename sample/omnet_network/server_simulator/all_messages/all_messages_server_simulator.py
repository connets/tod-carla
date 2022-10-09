import json
import os
import sys

import zmq

if __name__ == '__main__':

    dir_path = os.path.dirname(os.path.realpath(__file__))
    messages_path = dir_path + '/' + sys.argv[1]
    received_msgs = None
    if len(sys.argv) > 2:
        received_msgs = open(dir_path + '/' + sys.argv[2], 'rb')

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:5555")

    with open(messages_path, 'rb') as f:
        while (x := next(f, None)) is not None:
            recv_msg = json.loads(socket.recv().decode("utf-8"))
            if received_msgs is not None:
                expected_msg = json.loads(next(received_msgs).decode("utf-8"))
                if expected_msg != recv_msg:
                    print("****** ERRORE ******", '\n', expected_msg, '\n', recv_msg, '\n', "***************")
            print(recv_msg['timestamp'])
            socket.send(x)
