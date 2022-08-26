import enum


# (simulation_status, car_status)
class SimulationStatus(enum.Enum):
    RUNNING = 0
    FINISHED_OK = 1
    FINISHED_ACCIDENT = 2
    FINISHED_TIME_LIMIT = 3
    FINISHED_ERROR = -1

    @classmethod
    def is_finished(cls, status):
        return status in (cls.FINISHED_OK, cls.FINISHED_ACCIDENT, cls.FINISHED_TIME_LIMIT, cls.FINISHED_ERROR)


