import datetime
from time import sleep
from unittest.mock import MagicMock

from src.network.NetworkChannel import PhysicNetworkChannel, TcNetworkInterface
from src.network.NetworkMessage import NetworkMessage
from src.network.NetworkNode import NetworkNode


def test_network_two_nodes_without_delay():
    node2 = NetworkNode('localhost', 28002)
    node1 = NetworkNode('localhost', 28001)

    channel1 = TcNetworkInterface(lambda: 0, lambda: 0, 0, node2, 'wlp2s0')
    channel2 = TcNetworkInterface(lambda: 0, lambda: 0, 0, node1, 'wlp2s0')

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    msg = NetworkMessage(datetime.datetime.now().timestamp())
    node2.receive_msg = MagicMock()

    assert node2.receive_msg.call_count == 0

    node1.send_message(msg)
    sleep(1)  # enough time to receive msg

    node2.receive_msg.assert_called_once()

    node1.quit()
    node2.quit()


def test_network_called_two_nodes_without_delay():
    node2 = NetworkNode('127.0.0.1', 28008)
    node1 = NetworkNode('127.0.0.1', 28009)

    delay = 0.3
    timestamp = 0
    channel1 = TcNetworkInterface(lambda: timestamp, lambda: delay, 1, node2, 'lo')
    channel2 = TcNetworkInterface(lambda: timestamp, lambda: delay, 1, node1, 'lo')

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    channel2.tick()
    channel1.tick()

    sleep(delay + 0.2)  # enough time to receive msg

    node2.receive_msg = MagicMock()
    assert node2.receive_msg.call_count == 0

    msg = NetworkMessage(datetime.datetime.now().timestamp())
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
    node2 = NetworkNode('127.0.0.1', 28008)
    node1 = NetworkNode('127.0.0.1', 28009)

    delay = 0.3
    timestamp = 0
    channel1 = TcNetworkInterface(lambda: timestamp, lambda: delay, 1, node2, 'lo')
    channel2 = TcNetworkInterface(lambda: timestamp, lambda: delay, 1, node1, 'lo')

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    channel2.tick()
    channel1.tick()

    sleep(delay + 0.2)  # enough time to receive msg

    node2.receive_msg = MagicMock()
    assert node2.receive_msg.call_count == 0

    msg = NetworkMessage(datetime.datetime.now().timestamp())
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

    node1 = NetworkNode('127.0.0.1', 28008)
    node2 = NetworkNodeTest('127.0.0.1', 28009)

    channel1 = TcNetworkInterface(lambda: timestamp, lambda: delay, 1, node2, 'lo')
    channel2 = TcNetworkInterface(lambda: timestamp, lambda: delay, 1, node1, 'lo')

    node1.add_channel(channel1)
    node2.add_channel(channel2)

    channel2.tick()
    channel1.tick()

    msg = NetworkMessage(datetime.datetime.now().timestamp())
    node1.send_message(msg)

    sleep(delay / 1000 + 0.1)  # enough time to receive msg

    node1.quit()
    node2.quit()
