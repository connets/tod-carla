from abc import ABC, abstractmethod
from enum import Enum


class EventType(Enum):
    NETWORK = 1
    GENERAL = 2


def tele_event(name, event_type: EventType = EventType.GENERAL, log=True):
    def tele_event_aux(f):
        f.name_event = name
        f.event_type = event_type
        f.log_event = log
        return f

    return tele_event_aux


if __name__ == '__main__':
    class Tmp:
        @property
        def tmp(self):
            return 'ciao'

    class Tmp1(Tmp):

        def tmp(self):
            return "ue"


    print(Tmp1().tmp)
