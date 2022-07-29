import json

import pandas as pd
import zmq


def read_json(path):
    with open(path) as f:
        return json.load(f)


def send_info(socket, t):
    socket.send(json.dumps(t).encode("utf-8"))


def generate_init_completed(first_row):
    res = dict()
    res['message_type'] = "INIT_COMPLETED"
    res['payload'] = dict()
    res['payload']['initial_timestamp'] = first_row['timestamp']
    return json.dumps(res).encode("utf-8")


def generate_updated_position(row):
    res = dict()
    res['message_type'] = "UPDATED_POSITIONS"
    actor = dict()
    actor['actor_id'] = 'car'
    actor['position'] = dict()
    actor['velocity'] = dict()
    actor['rotation'] = dict()
    actor['position'] = [row['location_x'], row['location_y'], row['location_z']]
    actor['velocity'] = [row['velocity_x'], row['velocity_y'], row['velocity_z']]
    actor['rotation'] = [row['rotation_pitch'], row['rotation_yaw'], row['rotation_roll']]
    res['payload'] = dict()
    res['payload']['actors'] = [actor]

    return json.dumps(res).encode("utf-8")


if __name__ == '__main__':
    data = pd.read_csv('sensors.csv')
    data_iterators = data.iterrows()
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:5555")

    msg = (generate_init_completed(next(data_iterators)[1]))
    recv_msg = socket.recv()
    print(recv_msg)
    json_data = json.loads(recv_msg.decode("utf-8"))
    print("recv:", json_data)
    socket.send(msg)

    for _, row in data_iterators:
        recv_msg = socket.recv()
        json_data = json.loads(recv_msg.decode("utf-8"))
        print("recv:", json_data)

        msg = (generate_updated_position(row))
        socket.send(msg)

#
