import zerorpc
import carla
import logging

host = '172.16.1.249'
counts = 10
i = 1
retry = 4
while i <= 10:
    c = zerorpc.Client()
    c.connect(f"tcp://{host}:4242")
    c.reload_simulator()
    r = 0
    sim_world = None
    while sim_world is None and r < retry:
        try:
            print(f'trying {i}, {r}...\n')
            
            client = carla.Client(host, 2000)
            client.set_timeout(10.0)
            sim_world = client.load_world("Town01_Opt")
        except RuntimeError as e:
            r += 1

    if sim_world is None:
        raise RuntimeError(f"** ERROR ** {i}")
    print(f'** {i} DONE **\n\n')
    i += 1
    
    

