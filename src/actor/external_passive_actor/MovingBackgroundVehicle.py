import time


from src.actor.external_passive_actor.ExternalPassiveActor import ExternalPassiveActor
from src.actor.carla_actor.TeleCarlaActor import TeleCarlaVehicle
from src.TeleWorldController import TeleAdapterController


class MovingBackgroundVehicle(ExternalPassiveActor):
    def __init__(self, interval: float, agent: TeleAdapterController, actor: TeleCarlaVehicle):
        super().__init__(interval)
        self._agent = agent
        self._actor = actor
        
    def do_action(self):
        state = self._actor.generate_status()
        control = self._agent.do_action(state)
        self._actor.apply_instruction(control)

    def quit(self):
        self._actor.quit()
