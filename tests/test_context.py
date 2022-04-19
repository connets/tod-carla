# from src.TeleEventsScheduler import TeleEventsScheduler, TeleEventsSchedulerTime
# from src.TeleWorld import TeleWorld


from unittest.mock import MagicMock
# from src.TeleContext import TeleContext


# def test_add_event_to_network_world():
#     scheduler: TeleEventsScheduler = TeleEventsSchedulerTime()
#     world = NetworkTeleWorld("Network")
#     world.start(scheduler)
#
#     event = MagicMock()
#     event_ms = 1000
#
#     world.schedule_event(event, event_ms)
#
#     TeleContext.destroy()
#
from src.network.NetworkDelayManager import DiscreteNetworkDelayManager


# def test_time_pass():
#     ts = 0
#     delay_manager = DiscreteNetworkDelayManager(lambda: ts)
#     delay_manager.start()

# assert delay_manager.current_timestamp == tele_context.end_timestamp - tele_context.time_step
# TeleContext.destroy()
#
#d
#
def test_event_is_called():
    timestamp = 0
    delay_manager = DiscreteNetworkDelayManager(lambda: timestamp)

    event = MagicMock()
    delay_manager.schedule(event, 100)
    delay_manager.start()
    timestamp += 50
    assert event.call_count == 0

    timestamp += 50
    delay_manager.tick()

    event.assert_called_once()
#
#
# def test_worlds_communication():
#     start_timestamp = 1000
#     tele_context = TeleContext(start_timestamp, 3000, 100)
#     earth = TeleWorld("Earth", start_timestamp)
#     mars = TeleWorld("Mars", start_timestamp)
#     tele_context.add_world(earth)
#     tele_context.add_world(mars)
#
#     earth_event = MagicMock()
#     earth_event.exec = MagicMock()
#     earth.schedule_event_from_now(earth_event, 100)
#
#     mars_event = MagicMock()
#     mars_event.exec = MagicMock()
#
#     def schedule_mars_event(_):
#         mars2 = TeleContext.instance.get_world("Mars")
#         mars2.schedule_event_from_now(mars_event, 100)
#
#     earth_event.exec.side_effect = schedule_mars_event
#     tele_context.start()
#
#     earth_event.exec.assert_called_once_with(earth)
#     mars_event.exec.assert_called_once_with(mars)
