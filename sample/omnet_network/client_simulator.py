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
socket.connect("tcp://localhost:1234")
print("connected")

req = read_json('documentation/api_carla_omnet/init/from_omnet.json')
send_info(socket, req)
message = socket.recv()
print(message)
while True:
    req = read_json('documentation/api_carla_omnet/simulation_step/from_omnet.json')
    send_info(socket, req)
    message = socket.recv()
    print(message)
# print(f"Received reply  [ {message} ]")
# while True:
#     #  Wait for next request from client

#
#     #  Do some 'work'
#     time.sleep(1)


#  Send reply back to client
