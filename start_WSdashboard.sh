#!/bin/bash

# Initialize Conda and Activate Conda environment for WS
CONDA_INIT_SCRIPT="/opt/lst-safetybroker/conda/conda_init.sh"
source "$CONDA_INIT_SCRIPT"
conda activate ws

# Launch script in the background with nohup,  unbuffering the output
echo "Lunching the WS application..."
#sudo -u lst-safetybroker
nohup python -u /opt/lst-safetybroker/bin/dashboard/app.py > /dev/null 2>&1 &

# Wait a few seconds for the process to start
sleep 2

# Check if the process is running
p=`ps aux | grep app.py | grep python`
if p==1; then
    # Process is running
    echo "The weather station application has been launched in the background."
    echo "The WS webpage should be available in ~1min."
else
    # Process is not running
    echo "Error: The process is not running. An error occurred."
fi
