from src.utils.utils import need_member


class Singleton:
    def __init__(self, decorated_type):
        self._decorated_type = decorated_type
        self._instance = None

    @property
    @need_member("_instance")
    def instance(self):
        return self._instance

    def __call__(self, *args, **kwargs):
        if self._instance is not None: raise TypeError(
            'You already had instantiate this object, please call instance() method to retrieve')
        self._instance = self._decorated_type(*args, **kwargs)
        return self._instance

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated_type)

    def destroy(self):
        del self._instance
        self._instance = None

