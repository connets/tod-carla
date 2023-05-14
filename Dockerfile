FROM python:3.8.13-bullseye
RUN apt-get update \
    && pip install --upgrade pip==22.* \
    && apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tod-carla/
RUN pip install --no-cache-dir -r /tod-carla/requirements.txt
COPY . /app/tod-carla
WORKDIR /app/tod-carla

#CMD /bin/bash 
#CMD ["/bin/bash", "-c", "echo yaaa > /ueue/errr.txt"]
CMD while true; do python -m src.main $simulator_configuration_file_path; done
#CMD python -m sample.omnet_network.server_simulator.server_simulator
