FROM python:3.8.13-bullseye
RUN pip install --upgrade pip==22.*
COPY requirements.txt /tod_simulator/
RUN pip install -r /tod_simulator/requirements.txt
RUN apt-get update ; apt-get install ffmpeg libsm6 libxext6  -y
COPY . /tod_simulator
WORKDIR /tod_simulator

#CMD /bin/bash 
#CMD ["/bin/bash", "-c", "echo yaaa > /ueue/errr.txt"]
CMD python -m src.carla_omnet.CarlaOmnetSimulator $simulator_configuration_file_path
