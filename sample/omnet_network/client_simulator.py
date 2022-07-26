import json
import time
import zmq



def read_json(path):
    with open(path) as f:
        return json.load(f)


def send_info(socket, t):
    socket.send(json.dumps(t).encode("utf-8"))
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
print("connected")

send_info(socket, read_json("data/init.json"))
# while True:
#     #  Wait for next request from client
#     message = socket.recv()
#     print(f"Received request: {message}")
#
#     #  Do some 'work'
#     time.sleep(1)

    #  Send reply back to client
