# Weather Station

Scripts to read data from the WS sensor, upload them to a MongoDB and then display the data with a dash application.

MongoDB is installed with Docker and is used to store the data read from the Weather Station.
The instance of mongodb is forwarded (ports 27010) to host machine, so that it can be used from outside of the Docker environment.

The script `runWS.py` pulls the data from OPCUA server every 5 seconds and fills the MongoDB.

A dash application `app.py` reads the weather data from MongoDB and displays them.

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

To allow the pull/push of the weather data from the WS to the MongoDB, launch the script `runWS.py` with the command `nohup python -u runWS.py &`, while to start the dashboard use `nohup python -u dashboard/app.py &`.

To see if the scripts are running use: `ps aux | grep app.py` or `ps aux | grep runWS.py`.

If you want to kill one of the script, find the process ID with the command above and kill it.

## Logs

Logs are saved in `/var/log/lst-safetybroker/WS/` for the data script and `/var/log/lst-safetybroker/WS/dashboard/` for the dashboard.
A new file is created everyday at 12:00 UTC and only the log file up to 7 days are kept. Older files are automatically removed.

## Scripts

The script `lst-ws.sh` can be used to start, stop and check the status of the processes mentioned above.
Use `lst-ws.sh -h` for the different options.
