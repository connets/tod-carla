import datetime
from time import sleep
from unittest.mock import MagicMock

from src.network.NetworkChannel import DiscreteNetworkChannel
from src.network.NetworkMessage import NetworkMessage
from src.network.NetworkNode import NetworkNode
from src.utils.utils import find_free_port


class MyNetworkMessage(NetworkMessage):

    def action(self, destination):
        destination.receive_msg()


def test_network_two_nodes_without_delay():
    node2 = NetworkNode('localhost', find_free_port())
    node1 = NetworkNode('localhost', find_free_port())

    channel1 = DiscreteNetworkChannel(node2, lambda: 0, lambda: 0, 0)
    channel2 = DiscreteNetworkChannel(node1, lambda: 0, lambda: 0, 0)

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    node1.tick()
    node2.tick()

    msg = MyNetworkMessage(0)
    node2.receive_msg = MagicMock()

    assert node2.receive_msg.call_count == 0

    node1.send_message(msg)
    node1.tick()

    node2.receive_msg.assert_called_once()

    node1.quit()
    node2.quit()


def test_network_called_two_nodes_without_delay():
    node2 = NetworkNode('127.0.0.1', find_free_port())
    node1 = NetworkNode('127.0.0.1', find_free_port())

    node2.receive_msg = MagicMock()

    delay = 2
    timestamp = 0
    channel1 = DiscreteNetworkChannel(node2, lambda: timestamp, lambda: delay, 1)
    channel2 = DiscreteNetworkChannel(node1, lambda: timestamp, lambda: delay, 1)

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    msg = MyNetworkMessage()
    node1.send_message(msg)

    timestamp += 1
    node1.tick()
    node2.tick()

    assert node2.receive_msg.call_count == 0

    timestamp += 1
    node1.tick()
    node2.tick()

    node2.receive_msg.assert_called_once()

    node1.quit()
    node2.quit()