from abc import ABC, abstractmethod


def tele_event(name, log=True):
    def tele_event_aux(f):
        f.name_event = name
        f.log_event = log
        return f

    return tele_event_aux

if __name__ == '__main__':
    @tele_event('ciao')
    def tmp():
        print('i am tmp')
        return 'ciao'
    print(tmp())