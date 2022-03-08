import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/')))

from unittest.mock import MagicMock, call
from src.network_tele_world import NetworkTeleWorld
from src.tele_context import TeleContext


def test_add_event_to_world():
    start_timestamp = 1000
    tele_context = TeleContext(start_timestamp, 5000, 100)

    world = NetworkTeleWorld(start_timestamp)
    tele_context.add_world(world)

    assert not world.has_events()
    event = MagicMock()

    world.schedule_event_from_now(event, 2 * 1000)
    assert world.has_events()


def test_time_pass():
    tele_context = TeleContext(1000, 2000, 100)
    tele_context.start()
    assert tele_context.current_timestamp == tele_context.end_timestamp - tele_context.time_step


def test_world_is_called():
    tele_context = TeleContext(1000, 1500, 100)
    world = MagicMock()
    world.proceed = MagicMock()

    tele_context.add_world(world)
    tele_context.start()

    world.proceed.assert_has_calls([call(1000), call(1100), call(1200), call(1300), call(1400)])


def test_event_is_called():
    start_timestamp = 1000
    tele_context = TeleContext(start_timestamp, 1500, 100)
    world = NetworkTeleWorld(start_timestamp)
    tele_context.add_world(world)

    event = MagicMock()
    event.exec = MagicMock()
    world.schedule_event_from_now(event, 300)

    tele_context.start()

    event.exec.assert_called_once_with(world)
