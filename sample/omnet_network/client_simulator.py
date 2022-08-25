from datetime import datetime
import json
import random
import sys
import time

import numpy as np
import zmq


def read_json(type_request):
    with open(f'documentation/api_carla_omnet/{type_request}/from_omnet.json') as f:
        return json.load(f)


def send_info(socket, t):
    socket.send(json.dumps(t).encode("utf-8"))
    print("sent")


def receive_info(socket):
    message = socket.recv()
    print(message.decode("utf-8"))
    json_data = json.loads(message.decode("utf-8"))
    return json_data


simulation_step = 0.01
refresh_status = 0.05
delay = 0  # TODO implements this feature

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
print("connected")

req = read_json('init')
req['payload']['run_id'] = str(datetime.now())
send_info(socket, req)
message = receive_info(socket)
timestamp = message['payload']['initial_timestamp']

while True:
    for _ in np.arange(0, refresh_status, simulation_step):
        timestamp += simulation_step
        req = read_json('simulation_step')
        req['timestamp'] = timestamp
        send_info(socket, req)
        message = receive_info(socket)

    req = read_json('actor_status_update')
    req['timestamp'] = timestamp
    send_info(socket, req)
    message = receive_info(socket)
    status_id = message['payload']['status_id']

    req = read_json('compute_instruction')
    req['payload']['status_id'] = status_id
    req['timestamp'] = timestamp
    send_info(socket, req)
    message = receive_info(socket)
    instruction_id = message['payload']['instruction_id']
    if message['simulation_status'] != 0:
        break

    req = read_json('apply_instruction')
    req['payload']['instruction_id'] = instruction_id
    req['timestamp'] = timestamp
    send_info(socket, req)
    message = receive_info(socket)

# print(f"Received reply  [ {message} ]")
# while True:
#     #  Wait for next request from client

#
#     #  Do some 'work'
#     time.sleep(1)


#  Send reply back to client
