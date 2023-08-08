#!/bin/bash

# Initialize Conda and Activate Conda environment for WS
CONDA_INIT_SCRIPT="/opt/lst-safetybroker/conda/conda_init.sh"
source "$CONDA_INIT_SCRIPT"
conda activate ws

# Launch script in the background with nohup,  unbuffering the output
echo "Lunching OPC UA client..."
#sudo -u lst-safetybroker
nohup python -u /opt/lst-safetybroker/bin/runWS.py &

# Wait a few seconds for the process to start
sleep 2

# Check if the process is running
p=`ps aux | grep runWS.py | grep python`
if p==1; then
    # Process is running
    echo "The WS client is running"
else
    # Process is not running
    echo "Error: The process is not running. An error occurred."
fi