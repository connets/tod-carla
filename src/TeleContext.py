# @Singleton
# class TeleContext:
#
#     def __init__(self, scheduler: TeleEventsScheduler):
#         self._scheduler = scheduler
#         self._worlds = []
#
#     def add_world(self, world: TeleWorld):
#         world.start(self._scheduler)
#         self._worlds.append(world)
#
#     def get_world(self, world_name: str) -> TeleWorld:
#         for world in self._worlds:
#             if world.world_name == world_name: return world
#         raise Exception(f"There isn't any associated {world_name} world")
#
#     @property
#     def current_timestamp(self):
#         return self._current_timestamp
#
#     @property
#     def start_timestamp(self):
#         return self._start_timestamp
#
#     @property
#     def end_timestamp(self):
#         return self._end_timestamp
#
#     @property
#     def time_step(self):
#         return self._time_step
