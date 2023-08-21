# Tele Operated Driving simulator
Please note that in order to use the Tele-Operated Driving (TOD) Simulator, you will also need a communication network module. We recommend checking out [tod-simulator repository](https://github.com/connets/tod-carla), which makes it easier to run the simulator.

## Requirements
- Python 3.8.x, as specified in the [CARLA documentation](https://carla.readthedocs.io/en/latest/start_quickstart/)

## Setup definition
Available soon...

## Installation

To ensure that you can find the CARLA library in the central PyPI repository, you need to update pip first by running the following command:
```sh
pip install --upgrade pip==22.*
```
Once pip is updated, navigate to the tod_simulator directory and install all of the required dependencies by running:
```sh
pip install -r requirements.txt
```

## Citation

If you use the code or ideas in this repository for your research, please consider citing the following paper:

  - Author(s): Valerio Cislaghi, Christian Quadri, Vincenzo Mancuso, Marco Ajmone Marsan
  - Title: "Simulation of Tele-Operated Driving over 5G Using CARLA and OMNeT++"
  - Conference/Journal: IEEE Vehicular Networking Conference (VNC)
  - Year: 2023
  - BibTeX Citation:
    ```
    @inproceedings{10136340,
      author={Cislaghi, Valerio and Quadri, Christian and Mancuso, Vincenzo and Marsan, Marco Ajmone},
      booktitle={2023 IEEE Vehicular Networking Conference (VNC)}, 
      title={Simulation of Tele-Operated Driving over 5G Using CARLA and OMNeT++}, 
      year={2023},
      volume={},
      number={},
      pages={81-88},
      doi={10.1109/VNC57357.2023.10136340}
    }
    ```
