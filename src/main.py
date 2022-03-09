print("Hello world")

from utils import need_member


class Tmp:
    def __init__(self):
        self._a = None

    def set_a(self, a):
        self._a = a

    @property
    def a(self):
        return self._a

    @need_member("a")
    def exec(self):
        print("Hello")


t = Tmp()
t.set_a("ds")
t.exec()
