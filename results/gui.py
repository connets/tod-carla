import curses
import time
import carla
import os
import re
import subprocess
import pandas as pd


absdir = os.path.abspath(".")
if not absdir.endswith("results"): absdir = f"{absdir}/results"
omnetPath = "omnetLink"

def retieve_list_simulation():
    list_dir = sorted([e for e in os.listdir(absdir) if os.path.isdir(f"{absdir}/{e}") and e != 'omnet' and e != 'omnetLink' and e != '.ipynb_checkpoints'])
    return [{'name':name, 'path':f"{absdir}/{name}/recording.log"} for name in list_dir]

def retieve_omnet_file():
    list_files = sorted([e.split('.')[0] for e in os.listdir(f"{absdir}/{omnetPath}") if e.endswith('.sca')])
    return [{'name':name, 'path':f"{absdir}/{omnetPath}/{name}"} for name in list_files]


class Screen():
    def __init__(self, menu_win):
        self.screen01 = {
            "options": [("check carla server connection", self.f_connect_carla_server), ("list simulation", self.f_list_simulation), ("list omnet files", self.f_omnet_file), ("total_analysis", self.f_total_analysis), ("replay", self.f_replay), ("Quit", exit)],
            "current_option": 0
        }

        self.total_analysis = {
            "options": [("csv generation", self.f_csv_generation), ("Option 2", exit), ("Option 3", exit), ("Back", self.f_back)],
            "current_option": 0
        }

        self.replay = {
            "options": [("replay_file" , self.f_replay_file), ("show_recorder_file_info", self.f_show_recorder_file_info), ("show_recorder_collisions", self.f_show_recorder_collisions), ("Back", self.f_back)],
            "current_option": 0
        }

        self.simulations_list = {
            "options": [],
            "current_option": 0
        }
        

        self.selected_simulation = None

        self.currentScreen = [self.screen01]
        self.menu_win = menu_win
        self.simulations = retieve_list_simulation()
        self.omnetFiles = retieve_omnet_file()
        self.client = carla.Client('localhost', 2000)

    def f_back(self, *args, **kwargs):
        self.currentScreen.pop()

    def f_csv_generation(self, *args, **kwargs):
        nextLine = 3
        for omnet_file in self.omnetFiles:
            try:
                nextLine+=2
                self.menu_win.addstr(nextLine, 2, f"creating {omnet_file['name']} -> ")
                csvPath = f"{absdir}/{omnetPath}/_file.csv"
                p = subprocess.Popen(['opp_scavetool', 'x', '-F', 'CSV-R', '-o', f"{csvPath}", f"{omnet_file['path']}.sca", f"{omnet_file['path']}.vec"])
                p.wait()
                nextLine+=2
                self.menu_win.refresh()
                f = open(csvPath, 'r')
                run = f.readlines()[1].split(',')[0]
                self.menu_win.addstr(nextLine, 2, f"moving file from {csvPath} to {absdir}/{run}/omnet.csv")
                nextLine+=2
                p1 = subprocess.Popen(["cp", f"{csvPath}", f"{absdir}/{run}/omnet.csv"])
                p1.wait()
                f.close()
                self.menu_win.refresh()
                #time.sleep(1)
                p1 = subprocess.Popen(["rm", f"{csvPath}"])
                p1.wait()
            except Exception as e:
                nextLine+=2
                self.menu_win.addstr(nextLine, 2, f"error: {e}")
                nextLine+=2
                continue
            
        self.menu_win.getch()


    def f_connect_carla_server(self, *args, **kwargs):
        self.menu_win.addstr(2, 2, f"checking carla server connection")
        self.menu_win.refresh()
        self.client = carla.Client('localhost', 2000)
        result = None
        try:
            v = self.client.get_server_version()
            result = f"carla server is running on version {v}"
        except Exception as e:
            result = f"error while connecting to carla server: {e}"
        self.menu_win.addstr(3, 2, f"{result}")
        self.menu_win.refresh()
        self.menu_win.getch()

    def f_list_simulation(self, *args, **kwargs):
        self.menu_win.addstr(2, 2, f"searching for simuation results availables")
        nextLine = 3
        for sim in self.simulations:
            self.menu_win.addstr(nextLine, 2, f"{sim['name']}")
            nextLine+=1
            self.menu_win.refresh()
        self.menu_win.getch()

    def f_omnet_file(self, *args, **kwargs):
        self.menu_win.addstr(2, 2, f"searching for omnet results availables")
        nextLine = 3
        for sim in self.omnetFiles:
            self.menu_win.addstr(nextLine, 2, f"{sim['name']}")
            nextLine+=1
            self.menu_win.refresh()
        self.menu_win.getch()

    def f_total_analysis(self, *args, **kwargs):
        self.menu_win.addstr(2, 2, f"select total_analysis")
        self.currentScreen.append(self.total_analysis)

    def f_replay(self, *args, **kwargs):
        self.menu_win.addstr(2, 2, f"select replay")
        self.simulations_list['options'] = []
        for sim in self.simulations:
            name = sim['name']
            omnetFilePath = f"{sim['path'].replace('recording.log','omnet.csv')}"
            if os.path.isfile(omnetFilePath):
                #extract configuration details
                df = pd.read_csv(omnetFilePath)
                df = df[df['attrname'] == "iterationvars"]
                attr = f"{df['attrvalue']}"
                attr = attr.split('\n')[0]
                name += f" - {attr}"
            else:
                name += ' - unavailable omnet file'
            self.simulations_list['options'].append((name, self.f_select_simulation))
        self.simulations_list['options'].append(("Back", self.f_back))
        self.currentScreen.append(self.simulations_list)

    
    def f_select_simulation(self, *args, **kwargs):
        self.selected_simulation = self.simulations[args[0]]
        #self.menu_win.addstr(2, 2, f"select replay {self.simulations[args[0]]['name']}")
        #self.menu_win.refresh()
        self.currentScreen.append(self.replay)

    def f_replay_file(self, *args, **kwargs):
        self.menu_win.addstr(2, 2, f"replay {self.selected_simulation['name']}")
        self.menu_win.refresh()
        # replay
        self.client.replay_file(self.selected_simulation['path'], 0, 0, 0)
        time.sleep(1)

    def f_show_recorder_file_info(self, *args, **kwargs):
        self.menu_win.addstr(2, 2, f"f_show_recorder_file_info {self.selected_simulation['name']}")
        nextLine = 3
        collisions = self.client.show_recorder_file_info(self.selected_simulation['path'], False)
        lines = collisions.splitlines()
        for line in lines[:20]:
            self.menu_win.addstr(nextLine, 2, f"{line}")
            nextLine += 1

        self.menu_win.addstr(nextLine, 2, f"...")
        nextLine += 1
        
        for line in lines[-20:]:
            self.menu_win.addstr(nextLine, 2, f"{line}")
            nextLine += 1
        self.menu_win.getch()
    
    def f_show_recorder_collisions(self, *args, **kwargs):
        self.menu_win.addstr(2, 2, f"f_show_recorder_collisions {self.selected_simulation['name']}")
        nextLine = 3
        collisions = self.client.show_recorder_collisions(self.selected_simulation['path'], 'a', 'a')
        lines = collisions.splitlines()
        for line in lines:
            self.menu_win.addstr(nextLine, 2, f"{line}")
            nextLine += 1
        self.menu_win.getch()

def main(stdscr):
    # Clear screen
    stdscr.clear()
    # Hide the cursor (optional)
    curses.curs_set(0)
    # Enable keypad input to capture arrow keys
    stdscr.keypad(True)
    # Get the number of lines and columns in the terminal window
    height, width = stdscr.getmaxyx()
    # Create a window to display the menu
    menu_win = curses.newwin(height, width, 0, 0)
    menu_win.clear()
    screen = Screen(menu_win=menu_win)

    while True:

        menu_win = screen.menu_win
        options = screen.currentScreen[-1]['options']
        current_option = screen.currentScreen[-1]['current_option']

        # Clear the menu window
        menu_win.clear()

        # Print the menu title
        menu_win.addstr(0, 2, "Menu, (q to Quit)", curses.A_BOLD)

        # Print the menu options
        for idx, option in enumerate(options):
            if idx == current_option:
                menu_win.attron(curses.A_REVERSE)  # Highlight selected option
                menu_win.addstr(idx + 2, 2, option[0])
                menu_win.attroff(curses.A_REVERSE)  # Turn off highlighting
            else:
                menu_win.addstr(idx + 2, 2, option[0])

        # Refresh the window to update the screen
        menu_win.refresh()

        # Wait for user input (key press)
        key = menu_win.getch()

        # menu_win.addstr(0, 0, f"You selected: {key}")
        # menu_win.refresh()
        # menu_win.getch()  # Wait for key press to continue

        # Handle user input
        if key == 65 and current_option > 0:
            screen.currentScreen[-1]['current_option'] -= 1
        elif key == 66 and current_option < len(options) - 1:
            screen.currentScreen[-1]['current_option'] += 1
        elif key == 113:
            exit()
        elif key == 10:  # Enter key (Newline)
            if options[current_option][0] == "Quit":
                exit()
            menu_win.clear()
            #menu_win.addstr(2, 2, f"You selected: {options[current_option][0]}")
            options[current_option][1](current_option)
            menu_win.refresh()
            #time.sleep(2)
            #menu_win.getch()  # Wait for key press to continue

# Run the curses application
curses.wrapper(main)
