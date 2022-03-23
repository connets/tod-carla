from src.TeleWorld import TeleWorld


from unittest.mock import MagicMock, call
from src.NetworkTeleWorld import NetworkTeleWorld
from src.TeleContext import TeleContext


def test_add_event_to_world():
    start_timestamp = 1000
    tele_context = TeleContext(start_timestamp, 5000, 100)

    world = NetworkTeleWorld("Network", start_timestamp)
    tele_context.add_world(world)

    assert not world.has_events()
    event = MagicMock()

    world.schedule_event_from_now(event, 2 * 1000)
    assert world.has_events()
    TeleContext.destroy()


def test_time_pass():
    tele_context = TeleContext(1000, 2000, 100)
    tele_context.start()
    assert tele_context.current_timestamp == tele_context.end_timestamp - tele_context.time_step
    TeleContext.destroy()


def test_world_is_called():
    tele_context = TeleContext(1000, 1500, 100)
    world = MagicMock()
    world.proceed = MagicMock()

    tele_context.add_world(world)
    tele_context.start()

    world.proceed.assert_has_calls([call(1000), call(1100), call(1200), call(1300), call(1400)])
    TeleContext.destroy()


def test_event_is_called():
    start_timestamp = 1000
    tele_context = TeleContext(start_timestamp, 1500, 100)
    world = NetworkTeleWorld("Network", start_timestamp)
    tele_context.add_world(world)

    event = MagicMock()
    event.exec = MagicMock()
    world.schedule_event_from_now(event, 300)

    tele_context.start()

    event.exec.assert_called_once_with(world)
    TeleContext.destroy()


def test_worlds_communication():
    start_timestamp = 1000
    tele_context = TeleContext(start_timestamp, 3000, 100)
    earth = TeleWorld("Earth", start_timestamp)
    mars = TeleWorld("Mars", start_timestamp)
    tele_context.add_world(earth)
    tele_context.add_world(mars)

    earth_event = MagicMock()
    earth_event.exec = MagicMock()
    earth.schedule_event_from_now(earth_event, 100)

    mars_event = MagicMock()
    mars_event.exec = MagicMock()

    def schedule_mars_event(_):
        mars2 = TeleContext.instance.get_world("Mars")
        mars2.schedule_event_from_now(mars_event, 100)

    earth_event.exec.side_effect = schedule_mars_event
    tele_context.start()

    earth_event.exec.assert_called_once_with(earth)
    mars_event.exec.assert_called_once_with(mars)
