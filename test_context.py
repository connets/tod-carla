from unittest import mock
import pytest

from NetworkTeleWorld import NetworkTeleWorld
from tele_context import TeleContext
from unittest.mock import MagicMock, Mock, PropertyMock



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


    #event = create_empty_event(2 * 1000)
    #world = NetworkTeleWorld()
    #context.exec_next_event()
    #assert context.simulation_time == event.time
