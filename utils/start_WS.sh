#!/bin/bash

# Initialize Conda and Activate Conda environment for WS
CONDA_INIT_SCRIPT="/.../conda/conda_init.sh"
source "$CONDA_INIT_SCRIPT"
conda activate ws

# Launch script in the background with nohup,  unbuffering the output
echo "Lunching the WS client..."
nohup python -u /.../runWS.py 2>&1 >> /.../runWS.out &

# Wait a few seconds for the process to start
sleep 10

# Check if the process is running
p=`ps aux | grep runWS.py | grep python`
if p==1; then
    # Process is running
    echo "The WS client is running"
else
    # Process is not running
    echo "Something went wrong. The WS client is NOT running."
fi