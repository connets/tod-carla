#!/bin/bash
#python main.py
while true; do
    echo "starting cooperative-perception"
    python main.py -render=true
#     #python -m src.main "$SIMULATOR_CONFIGURATION_FILE_PATH" "$TOD_CARLA_ARGS"
done

