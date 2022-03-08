from my_singleton import Singleton
import pytest

def test_singleton():

    @Singleton
    class Tmp:
        def __init__(self, a):
            self._a = a

    i1 = Tmp('tmp')
    i2 = Tmp.instance
    assert i1 == i2
    with pytest.raises(Exception) as e:
        Tmp('tmp2')


