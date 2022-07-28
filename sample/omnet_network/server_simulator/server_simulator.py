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
    node = dict()
    node['actor_id'] = 'car'
    node['position'] = dict()
    node['velocity'] = dict()
    node['rotation'] = dict()
    node['position']['x'] = row['location_x']
    node['position']['y'] = row['location_y']
    node['position']['z'] = row['location_z']
    node['velocity']['x'] = row['velocity_x']
    node['velocity']['y'] = row['velocity_y']
    node['velocity']['z'] = row['velocity_z']
    node['rotation']['pitch'] = row['rotation_pitch']
    node['rotation']['yaw'] = row['rotation_yaw']
    node['rotation']['roll'] = row['rotation_roll']
    res['payload'] = [node]

    return json.dumps(res).encode("utf-8")


if __name__ == '__main__':
    data = pd.read_csv('sensors.csv')
    data_iterators = data.iterrows()
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:1234")

    msg = (generate_init_completed(next(data_iterators)[1]))
    recv_msg = socket.recv()
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
