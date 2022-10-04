import json
import sys
import zmq


def send_info(socket, t):
    print("Send: ", json.dumps(t).encode("utf-8"))
    socket.send(json.dumps(t).encode("utf-8"))


def receive_info(socket):
    message = socket.recv()
    print("Received: ", message.decode("utf-8"))
    json_data = json.loads(message.decode("utf-8"))
    if json_data['simulation_status'] != 0:
        sys.exit(0)
    return json_data


if __name__ == '__main__':
    refresh_status = 0.05
    simulation_step = 0.01


    def read_json(type_request):
        with open(f'API/{type_request}.json') as f:
            return json.load(f)


    init_configuration_json = read_json('init')

    payload = init_configuration_json['payload']
    interested_actor = payload['actors'][0]
    interested_agent = interested_actor['agents'][0]
    actor_id = interested_actor['actor_id']
    agent_id = interested_agent['agent_id']

    if len(sys.argv) >= 2:
        payload['seed'] = int(sys.argv[1])
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    print("connected")

    send_info(socket, init_configuration_json)
    message = receive_info(socket)
    timestamp = message['payload']['initial_timestamp']
    limit_sim_time = 15

    while True:
        for _ in range(int(refresh_status / simulation_step)):
            timestamp += simulation_step
            req = read_json('simulation_step')
            req['timestamp'] = timestamp
            send_info(socket, req)
            message = receive_info(socket)
            if message['simulation_status'] != 0: break
        if message['simulation_status'] != 0: break

        req = read_json('actor_status_update')
        req['timestamp'] = timestamp
        send_info(socket, req)

        message = receive_info(socket)
        if message['simulation_status'] != 0: break
        status_id = message['payload']['status_id']

        req = read_json('compute_instruction')
        req['payload']['status_id'] = status_id
        req['timestamp'] = timestamp
        send_info(socket, req)

        message = receive_info(socket)
        if message['simulation_status'] != 0:
            break
        instruction_id = message['payload']['instruction_id']

        req = read_json('apply_instruction')
        req['payload']['instruction_id'] = instruction_id
        req['timestamp'] = timestamp
        send_info(socket, req)
        message = receive_info(socket)
        if message['simulation_status'] != 0:
            break
