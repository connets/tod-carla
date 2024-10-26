from pycarlanet.utils import DecoratorSingleton
from pycarlanet.listeners import WorldManager, ActorManager, AgentManager

@DecoratorSingleton
class InterCommunicationListeners:
    def __init__(self, worldManager: WorldManager, actorManager: ActorManager, agentManager: AgentManager, *args):
        self._managers = {
            WorldManager: worldManager,
            ActorManager: actorManager,
            AgentManager: agentManager
        }
        for manager in args:
            self._managers[manager.__class__] = manager

    def askToManager(self, managerClass, functionName, *args, **kwargs):
        manager = self._managers[managerClass]
        func = getattr(manager, functionName)
        return func(*args, **kwargs)
    
    # def askToWorldManager(self, functionName, *args, **kwargs):
    #     func = getattr(self._worldManager, functionName)
    #     return func(*args, **kwargs)
    
    # def askToActorManager(self, functionName, *args, **kwargs):
    #     func = getattr(self._actorManager, functionName)
    #     return func(*args, **kwargs)

    # def askToAgentManager(self, functionName, *args, **kwargs):
    #     func = getattr(self._agentManager, functionName)
    #     return func(*args, **kwargs)

