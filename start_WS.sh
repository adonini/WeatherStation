#!/bin/bash

# Activate Conda environment for WS
source /home/alice.donini/.bashrc
conda activate modbus

# Launch script in the background with nohup,  unbuffering the output
sudo -u lst-safetybroker nohup python -u runWS.py &

# Print a message indicating the script has been started
echo "runWS.py script has been launched in the background."