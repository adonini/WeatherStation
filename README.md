# Weather Station

Scripts to read data from the LST-1 WS sensor, upload them to a MongoDB and then display the data with a dash application.

MongoDB is installed with Docker and is used to store the data read from the Weather Station.
The instance of mongodb is forwarded to host machine, so that it can be used from outside of the Docker environment.

The script `runWS.py` pulls the data from OPCUA server every 10 seconds and fills the MongoDB.

A dash application `app.py` reads the weather data from MongoDB and displays them.

## Environment set up

A conda environment is needed for the system to work. An **yml** file to create the environment with the required packages is provided in the repository.
Conda should be accessible by the user that is lunching the scripts, in this case `lst-safetybroker`, thus a miniconda installation and an initilization script should be available.

Copy the ```.env.example``` file to a ```.env``` file and edit it to fill the required variables.

## MongoDB

To start the container: `docker-compose -f docker_compose_mongo.yaml up -d`

To stop the container: `docker-compose -f docker_compose_mongo.yaml down`

The option `-d` detach the docker-compose, so that the container is being run in the background.

To list the running containers: `docker ps`.

To enter inside the Mongo container and run an interactive shell: `docker exec -it mongodb-WS bash`.
Once in the bash terminal of the container use command `mongo` to access MongoDB.
Run `show dbs` command to list all databases.
To switch to the database use the command `use <DB NAME>`, to see the available collections in the database use `show collections`.

To access container logs use `docker logs mongodb-WS` command.

## OPC UA client and dash app

To allow the pull/push of weather data from the WS to the MongoDB, launch the script `runWS.py` with the command `nohup python -u runWS.py &`, while to start the dashboard use `nohup python -u dashboard/app.py &`. Note that the correct conda environment should be active for these processes to start and they should always be run as `lst-safetybroker` user.

To see if the scripts are running use: `ps aux | grep app.py` or `ps aux | grep runWS.py`.

If you want to kill one of the script, find the process ID with the command above and kill it.

Scripts to perform these actions are given, see section [General Scripts](#general-scripts).

## Logs

The path for logs has to be specified in the `.env` file`.
A new file is created everyday at 08:00 UTC and only the log files up to 7 days are kept. Older files are automatically removed.

## General Scripts

The folder `utils` contains general scripts which facilitate the usage of the system.

The scripts `start_WSdashboard.sh` and `start_WS.sh` should be used to start the processes mentioned above with the correct environment.
`lst-ws.sh` is a general script from which it's possible to manage all the process. From it one can start, stop and check the status of the processes.
`lst-ws.sh` is also the only script to which the user `lst-operator` have access in case of need.
Use `lst-ws.sh -h` to see the different options.

The bash script `check_and_restart.sh` is run by a cronjob, and is responsable to call the scripts above if the process of the client `runWS.py` or the dashboard `app.py` are down.

The script `ORM_WSdata.py` creates a txt file which is then used to display LST weather station data in the ORM webpage.
The txt file is moved to the webserver by the script `weather_monitor.sh`, which also checks that `ORM_WSdata.py` is running, and if not restarts it.
A cronejob under user `lst-safetybroker` is responsable to run the script `weather_monitor.sh` every 40sec.

To be able to move the file to the webserver a ssh key for the user `lst-safetybroker` is needed.

Fill all the file paths according to the system.
