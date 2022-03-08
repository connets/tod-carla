class Singleton:
    def __init__(self, decorated_type):
        self._decorated_type = decorated_type
        self._instance = None

    @property
    def instance(self):
        if self._instance is None: raise TypeError('you need to instantiate singleton object')
        return self._instance

    def __call__(self, *args, **kwargs):
        if self._instance is not None: raise TypeError('you already had instantiate this object, please call instance() method to retrieve')
        self._instance = self._decorated_type(*args, **kwargs)
        return self._instance

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


    




