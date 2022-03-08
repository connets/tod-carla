from unittest import mock
import pytest
from tele_context import TeleContext
from unittest.mock import MagicMock, Mock, PropertyMock

pytest.context = TeleContext()


def schedule_empty_event(context, time):
    event = MagicMock()
    event_time = PropertyMock(return_value = 20)
    type(event).time = event_time
    event.__lt__ = lambda self, e: self.time < e.time

    context = pytest.context
    context.schedule_event(event)
    return event

def test_add_event():
    context = pytest.context
    assert not context.has_events()
    _ = schedule_empty_event(context, 20)
    assert context.has_events()


def test_time_pass():
    context = pytest.context
    event = schedule_empty_event(context, 20)
    
    context.exec_next_event()
    assert context.simulation_time == event.time