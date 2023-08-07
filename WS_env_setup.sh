#!/bin/bash

CONDA_INIT_SCRIPT="/opt/lst-safetybroker/conda/conda_init.sh"

# Check if Conda init script exists
if [ ! -f "$CONDA_INIT_SCRIPT" ]; then
    echo "Error: Conda init script not found at $CONDA_INIT_SCRIPT"
    exit 1
fi

# Initialize Conda
source "$CONDA_INIT_SCRIPT"

# Path to environment.yml file
ENV_FILE="/opt/lst-safetybroker/bin/environment.yml"

# Check if environment.yml file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: environment.yml file not found"
    exit 1
fi

# Create Conda environment using the environment.yml file
conda env create -f "$ENV_FILE"

# Activate the newly created environment
#conda activate ws

# Display a message indicating successful environment creation
echo "Conda environment created successfully!"