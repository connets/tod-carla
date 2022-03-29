import time
from unittest.mock import MagicMock, patch, Mock

from src.TeleEvent import TeleEvent
from src.TeleEventsScheduler import TeleEventsSchedulerTime


def test_scheduler():

    world = MagicMock()

    TeleEvent.__abstractmethods__ = set()
    event = TeleEvent()
    event.exec = MagicMock()
    scheduler = TeleEventsSchedulerTime(blocking=True)
    scheduler.schedule(lambda: event(world), 100)

    # scheduler.schedule(world, MyEvent(), 100)
    event.exec.assert_called_once_with(world)
