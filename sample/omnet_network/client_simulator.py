import json
import time
import zmq


def read_json(type_request):
    with open(f'documentation/api_carla_omnet/{type_request}/from_omnet.json') as f:
        return json.load(f)


def send_info(socket, t):
    socket.send(json.dumps(t).encode("utf-8"))


def receive_info(socket):
    message = socket.recv()
    json_data = json.loads(message.decode("utf-8"))
    return json_data


context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:1234")
print("connected")

req = read_json('init')
send_info(socket, req)
message = receive_info(socket)
print(message)
while True:
    for _ in range(1):
        req = read_json('simulation_step')
        send_info(socket, req)
        message = receive_info(socket)
        print(message)

    req = read_json('actor_status_update')
    send_info(socket, req)
    message = receive_info(socket)
    print(message)
    status_id = message['payload']['status_id']

    req = read_json('compute_instruction')
    req['payload']['status_id'] = status_id
    send_info(socket, req)
    message = receive_info(socket)
    print(message)
    instruction_id = message['payload']['instruction_id']

    req = read_json('apply_instruction')
    req['payload']['instruction_id'] = instruction_id
    send_info(socket, req)
    message = receive_info(socket)
    print(message)


# print(f"Received reply  [ {message} ]")
# while True:
#     #  Wait for next request from client

#
#     #  Do some 'work'
#     time.sleep(1)


#  Send reply back to client
