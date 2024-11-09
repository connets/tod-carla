import json
import sys
import zmq
import time


statusID= 1000

messages = {
    "INIT": {
        'message_type': 'INIT_COMPLETED',
        'initial_timestamp': 2.0,
        'simulation_status': 0,
        'actor_positions': [
        ]
    },
    "ACTOR_STATUS_UPDATE": {
        'message_type': 'ACTOR_GENERIC_RESPONSE',
        'simulation_status': 0,
        'user_defined': {
            'user_message_type': 'ACTOR_STATUS',
            'actor_id': 'Car01',
            'status_id': '1000'
        }
    },
    "COMPUTE_INSTRUCTION": {
        'message_type': 'AGENT_GENERIC_RESPONSE',
        'simulation_status': 0,
        'user_defined': {
            'user_message_type': 'INSTRUCTION',
            'actor_id': 'Car01',
            'instruction_id': '1008'
        }
    },
    "APPLY_INSTRUCTION": {
        'message_type': 'ACTOR_GENERIC_RESPONSE',
        'simulation_status': 0,
        'user_defined': {
            'user_message_type': 'OK'
        }
    },
    "SIMULATION_STEP": {
        'message_type': 'UPDATED_POSITIONS',
        'simulation_status': 0,
        'actor_positions': [
            {
                'actor_id': 'Car01',
                'position': [-12.158696174621582, 66.13933563232422, 0.030790900811553],
                'rotation': [0.00016392453107982874, 179.76634216308594, -6.103514533606358e-05],
                'velocity': [-1.1239238801863394e-06, 2.566447960816731e-07, 0.771381139755249],
                'type': 'Vehicle'
            },
            {
                'actor_id': 'Other01',
                'position': [-22.085369110107422, 70.28341674804688, 0.0030816267244517803],
                'rotation': [0.02570882998406887, -179.9999542236328, 0.008719069883227348],
                'velocity': [-0.00020793481962755322, 0.00017304385255556554, 0.6934877038002014],
                'type': 'Vehicle'
            },
            {
                'actor_id': 'EdgeCamera01',
                'position': [0,0,0],
                'rotation': [0,0,0],
                'velocity': [0,0,0],
                'type': 'EdgeCamera'
            }
        ]
    },
    "COOPERATIVE_STATUS_REQUEST": {
        'message_type': 'ACTOR_GENERIC_RESPONSE',
        'simulation_status': 0,
        'user_defined': {
            'user_message_type': 'ACTOR_STATUS',
            'actor_id': 'Car01',
            'status_id': '1000'
        }
    },
    "COOPERATIVE_UPDATE": {
        'message_type': '_GENERIC_RESPONSE',
        'simulation_status': 0,
        'user_defined': {
            'user_message_type': 'OK'
        }
    }
}


def send_info(socket, t):
    print(f"sending:\n{t}\n")
    socket.send(json.dumps(t).encode("utf-8"))


def receive_info(socket):
    message = socket.recv()
    json_data = json.loads(message.decode("utf-8"))
    print(f"received: {json_data}\n")
    return json_data


if __name__ == '__main__':
    
    refresh_status = 0.01
    simulation_step = 0.01


    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    print("connected")

    data = receive_info(socket)
    send_info(socket=socket, t=messages["INIT"])


    while True:
        data = receive_info(socket)

        if data['message_type'] == "SIMULATION_STEP":
            send_info(socket=socket, t=messages["SIMULATION_STEP"])
            continue

        k = data['user_defined']['user_message_type']
        response = messages[k]

        if k == "COOPERATIVE_UPDATE":
            splitted = data['message_type'].split("_")
            response["message_type"] = splitted[0] + "_GENERIC_RESPONSE"

        if k in ["ACTOR_STATUS_UPDATE", "COMPUTE_INSTRUCTION", "COOPERATIVE_STATUS_REQUEST"]:
            response['user_defined']['actor_id'] = data['user_defined']['actor_id']
            response['user_defined']['status_id'] = f"{statusID}"
            statusID += 1
        
        send_info(socket=socket, t=response)