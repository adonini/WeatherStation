#!/bin/bash

# Function to check if a process is running
is_process_running() {
    pgrep -f "$1" > /dev/null
}

# Check and restart the first script
if ! is_process_running "runWS.py"; then
    #echo "runWS.py is not running. Restarting..."
    /opt/lst-safetybroker/bin/start_WS.sh
fi

# Check and restart the second script
if ! is_process_running "app.py"; then
    #echo "app.py is not running. Restarting..."
    /opt/lst-safetybroker/bin/start_WSdashboard.sh
fi
