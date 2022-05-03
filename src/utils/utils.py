import functools
import threading

import socket
from contextlib import closing
from copy import copy, deepcopy

from src.utils.decorators import closure


def stretch_dict(d, keys_sep='.'):
    def stretch_dict_aux(d_p):
        if not isinstance(d_p, dict):
            return [('', d_p)]
        res = []
        for k_p, v_p in d_p.items():
            res = res + [(f'{k_p}{keys_sep if item[0] != "" else ""}{item[0]}', item[1]) for item in stretch_dict_aux(v_p)]
        return res

    return dict(stretch_dict_aux(d))

@closure
def expand_dict(d, keys_sep='.'):
    res = dict()
    for k, v in d.items():
        if keys_sep in k:
            key, rest = k.split(keys_sep, 1)
            if key not in res:
                res[key] = dict()
            res[key] = {**res[key], rest: v}
        elif isinstance(v, dict):
            if k not in res:
                res[k] = dict()

            res[k] = {**expand_dict(v, keys_sep), **res[k]}
        else:
            res[k] = v

    return res


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


if __name__ == '__main__':
    tmp = {'ciao.come': {'stai': 3, 'va': {'bene.grazie': 'prego'}}, 'ciao': {'com': 'tu'}, 'easy':0}
    print(expand_dict(tmp))

    # flat_dictionary()
    # for k, v in d.items():
    #     if keys_sep in k:
    #         tokens = k.split(keys_sep)
    #         rest, key = '.'.join(tokens[:-1]), tokens[-1]
    #         if rest not in res: res[rest] = dict()
    #         res[rest][key] = v
    #     else:
    #
    #         res[k] = v