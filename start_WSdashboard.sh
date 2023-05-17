#!/bin/bash

# Activate Conda environment for WS
source /home/alice.donini/.bashrc
source activate modbus

# Launch script in the background with nohup,  unbuffering the output
sudo -u lst-safetybroker nohup python -u /opt/lst-safetybroker/bin/dashboard/app.py &

# Print a message indicating the script has been started
echo "Weather station dashboard script has been launched in the background."