#!/bin/bash
while true; do
    echo "starting tod-carla_v2"
    python main.py
    #python -m src.main "$SIMULATOR_CONFIGURATION_FILE_PATH" "$TOD_CARLA_ARGS"
done

