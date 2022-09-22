from src.actor.TeleActor import TeleActor


class ExternalPassiveActor(TeleActor):
    def __init__(self, interval):
        super().__init__()
        self.last_action = 0
        self.interval = interval

    def tick(self, timestamp):
        print(timestamp, self.last_action, self.interval, round(self.last_action + self.interval, 6))
        if timestamp >= round(self.last_action + self.interval, 6):
            self.last_action = timestamp
            self.do_action()

    def do_action(self):
        ...
