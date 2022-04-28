import functools
import threading

import socket
from contextlib import closing


def need_member(*members, valid=lambda x: x is not None):
    def wrapper_method(method):
        def validation(ref, *args, **kwargs):
            for member in members:
                if not valid(getattr(ref, member)):
                    raise Exception(f"Some errors occurred with {member} while calling method {method.__name__}")
            return method(ref, *args, **kwargs)

        return validation

    return wrapper_method


def flat_dict(d, keys_sep='.'):
    def flat_dict_aux(d_p):
        if not isinstance(d_p, dict):
            return [('', d_p)]
        res = []
        for k_p, v_p in d_p.items():
            res = res + [(f'{k_p}{keys_sep if item[0] != "" else ""}{item[0]}', item[1]) for item in flat_dict_aux(v_p)]
        return res

    return dict(flat_dict_aux(d))


def synchronized(lock: threading.RLock):
    def _decorator(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(*args, **kwargs):
            with lock:
                return wrapped(*args, **kwargs)

        return _wrapper

    return _decorator


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


if __name__ == '__main__':
    d = {'a': {'b': 2, 'd': 2}, 'c': 1, 'd': {'e': {'f': 3}}}
    print(flat_dict(d))
# flat_dictionary()
