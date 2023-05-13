# Tele Operated Driving simulator
Please note that in order to use the Tele-Operated Driving (TOD) Simulator, you will also need a communication network module. We recommend checking out the tod_simulator_compose repository, which makes it easier to run the simulator.

## Requirements
- Python 3.8.x, as specified in the [CARLA documentation](https://carla.readthedocs.io/en/latest/start_quickstart/)

## Setup definition
The setup is passed by the communication module, which can be defined in OMNeT or 

## Installation

To ensure that you can find the CARLA library in the central PyPI repository, you need to update pip first by running the following command:
```sh
pip install --upgrade pip==22.*
```
Once pip is updated, navigate to the tod_simulator directory and install all of the required dependencies by running:
```sh
pip install -r requirements.txt
```
