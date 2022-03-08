import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/')))

from unittest.mock import MagicMock, PropertyMock, call, Mock
from src.network_tele_world import NetworkTeleWorld
from src.tele_context import TeleContext


def create_empty_event(time):
    event = MagicMock()
    event_time = PropertyMock(return_value=time)
    type(event).time = event_time
    event.__lt__ = lambda self, e: self.time < e.time
    return event


def test_add_event_to_world():
    tele_context = TeleContext(100, 200, 10)

    world = NetworkTeleWorld()
    tele_context.add_world(world)

    assert not world.has_events()
    event = create_empty_event(2 * 1000)
    world.schedule_event(event)

    assert world.has_events()


def test_time_pass():
    tele_context = TeleContext(100, 200, 10)
    tele_context.start()
    assert tele_context.current_timestamp == tele_context.end_timestamp - tele_context.time_step


def test_world_is_called():
    tele_context = TeleContext(100, 150, 10)
    world = MagicMock()
    world.proceed = MagicMock()

    tele_context.add_world(world)
    tele_context.start()

    world.proceed.assert_has_calls([call(100), call(110), call(120), call(130), call(140)])
