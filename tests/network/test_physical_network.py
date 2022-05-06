import datetime
from time import sleep
from unittest.mock import MagicMock

from src.network.NetworkChannel import PhysicNetworkChannel, TcNetworkInterface
from src.network.NetworkMessage import NetworkMessage
from src.network.NetworkNode import NetworkNode
from src.utils.utils import find_free_port


class MyNetworkMessage(NetworkMessage):

    def action(self, destination):
        destination.receive_msg()


def test_network_two_nodes_without_delay():
    node2 = NetworkNode('localhost', find_free_port())
    node1 = NetworkNode('localhost', find_free_port())

    channel1 = TcNetworkInterface(node2, lambda: 0, lambda: 0, 0, 'lo')
    channel2 = TcNetworkInterface(node1, lambda: 0, lambda: 0, 0, 'lo')

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    msg = MyNetworkMessage(datetime.datetime.now().timestamp())
    node2.receive_msg = MagicMock()

    assert node2.receive_msg.call_count == 0

    node1.send_message(msg)
    sleep(1)  # enough time to receive msg

    node2.receive_msg.assert_called_once()

    node1.quit()
    node2.quit()


def test_network_called_two_nodes_without_delay():
    node2 = NetworkNode('127.0.0.1', find_free_port())
    node1 = NetworkNode('127.0.0.1', find_free_port())

    delay = 0.3
    timestamp = 0
    channel1 = TcNetworkInterface(node2, lambda: timestamp, lambda: delay, 1, 'lo')
    channel2 = TcNetworkInterface(node1, lambda: timestamp, lambda: delay, 1, 'lo')

    node1.add_channel(channel1)
    node2.add_channel(channel2)


    node1.tick()
    node2.tick()

    sleep(delay + 0.2)  # enough time to receive msg

    node2.receive_msg = MagicMock()
    assert node2.receive_msg.call_count == 0

    msg = MyNetworkMessage(datetime.datetime.now().timestamp())
    node1.send_message(msg)
    sleep(1)  # enough time to receive msg

    node2.receive_msg.assert_called_once()

    node2.receive_msg = MagicMock()

    timestamp += 1
    delay += 2
    channel2.tick()
    channel1.tick()
    sleep(1)  # enough time to receive msg

    assert node2.receive_msg.call_count == 0

    node1.quit()
    node2.quit()


def test_network_called_two_nodes_with_delay():
    node2 = NetworkNode('127.0.0.1', find_free_port())
    node1 = NetworkNode('127.0.0.1', find_free_port())

    delay = 0.3
    timestamp = 0
    channel1 = TcNetworkInterface(node2, lambda: timestamp, lambda: delay, 1, 'lo')
    channel2 = TcNetworkInterface(node1, lambda: timestamp, lambda: delay, 1, 'lo')

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    channel2.tick()
    channel1.tick()

    sleep(delay + 0.2)  # enough time to receive msg

    node2.receive_msg = MagicMock()
    assert node2.receive_msg.call_count == 0

    msg = MyNetworkMessage(datetime.datetime.now().timestamp())
    node1.send_message(msg)
    sleep(1)  # enough time to receive msg

    node2.receive_msg.assert_called_once()

    node2.receive_msg = MagicMock()

    timestamp += 1
    delay += 2
    channel2.tick()
    channel1.tick()
    sleep(1)  # enough time to receive msg

    assert node2.receive_msg.call_count == 0

    node1.quit()
    node2.quit()


from unittest.mock import patch


def test_network_called_two_nodes_with_exactly_delay():
    delay = 1000
    timestamp = 0

    class NetworkNodeTest(NetworkNode):

        def receive_msg(self, network_message):
            timestamp_now = datetime.datetime.now().timestamp()
            assert abs(timestamp_now - network_message) <= delay + 1

    node1 = NetworkNode('127.0.0.1', find_free_port())
    node2 = NetworkNodeTest('127.0.0.1', find_free_port())

    channel1 = TcNetworkInterface(node2, lambda: timestamp, lambda: delay, 1, 'lo')
    channel2 = TcNetworkInterface(node1, lambda: timestamp, lambda: delay, 1, 'lo')

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    channel2.tick()
    channel1.tick()

    msg = MyNetworkMessage(datetime.datetime.now().timestamp())
    node1.send_message(msg)

    sleep(delay / 1000 + 0.1)  # enough time to receive msg

    node1.quit()
    node2.quit()
