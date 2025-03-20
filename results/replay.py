import carla
import os
import re

#'v' = Vehicle 'w' = Walker 't' = Traffic light 'o' = Other, 'a' = All


if __name__ == '__main__':
    # Connect to the simulator running on localhost:2000
    client = carla.Client('localhost', 2000)

    absdir = os.path.abspath(".")

    if not absdir.endswith("results"): absdir = f"{absdir}/results"


    dir_list = sorted([e for e in os.listdir(absdir) if os.path.isdir(f"{absdir}/{e}")])
    dir_dict = {str(i): item for i, item in enumerate(dir_list)}
    #dir_dict = dict(sorted(dir_dict.items(), key=lambda item: item[1]))
    for k, v in dir_dict.items():
        print(k, v)

    while True:
        n = input("select number: ")
        client.stop_replayer(True)
        filepath = f"{absdir}/{dir_dict[n]}/recording.log"
        #print(filepath)
        client.replay_file(filepath,0,100,0)
        collisions = client.show_recorder_collisions(filepath, 'a', 'a')
        info = client.show_recorder_file_info(filepath, False)
        lines = collisions.splitlines()
        # Regular expression to match "v v" or "v a" in any part of the line
        pattern = r'\b(v v|v w|v t|v o)\b'
        # Iterate through lines and check for matches
        for line in lines:
            if re.search(pattern, line):
                print(f"found collision: {line}\n")
                break

    #for i, name in enumerate(drctry):
    #    print(i, name)