#!/bin/bash

# check the input is clear
if [ $# -eq 0 ]
    then
        echo "No arguments supplied. Please run with '-h' option for available options. Exiting, bye bye!"
        exit
elif [ $# -gt 1 ]
    then
        echo "Several arguments supplied. Input is ambiguous. Exiting!"
        exit
else
    :
fi

# loop over input options
case "$1" in
    -h|-\?|--help|help)
        # echo "##############################    WS OPC UA SERVER ACTIONS    ######################################"
        # echo
        # echo "   start_WS_OPCUA      -- Launches the WS OPC UA server docker"
        # echo "   stop_WS_OPCUA       -- Stops the WS OPC UA server docker"
        # echo "   status_WS_OPCUA     -- Reports the status of the WS OPC UA server docker image"
        # echo
        echo "##############################    WS DB ACTIONS    ######################################"
        echo
        echo "   start_WS_DB      -- Launches the WS DB docker image"
        echo "   stop_WS_DB       -- Stops the WS DB docker image"
        #echo "   kill       -- Not implemented"
        echo "   status_WS_DB     -- Reports the status for the WS DB docker image"
        echo
        echo "#############################    WS DATA SCRIPT ACTIONS    ##############################"
        echo
        echo "   start_WS_client   -- Launches the script to push weather data into the WS DB"
        echo "   stop_WS_client    -- Stops the script to push weather data into the WS DB"
        echo "   status_WS_client  -- Reports the status of the script to push weather data into the WS DB"
        echo
        echo "#############################    DASHBOARD ACTIONS    #############################"
        echo
        echo "   start_dashboard   -- Launches the LST-1 weather station dashboard"
        echo "   stop_dashboard    -- Stops the LST-1 weather station dashboard"
        echo "   status_dashboard  -- Reports the LST-1 weather station dashboard"
        echo
        echo "##################################################################################"
        exit
        ;;

    ##############################    WS OPC UA SERVER ACTIONS    ######################################
    # start_WS_OPCUA)
    #         echo "Starting WS OPC UA server container"
    #         docker-compose -f /opt/...../etc/... docker_compose_mongo.yaml up -d
    #         exit
    #         ;;
    #     stop_WS_OPCUA)
    #         echo "Stopping WS OPC UA server container"
    #         docker-compose -f /opt/...../etc/... docker_compose_mongo.yaml down
    #         exit
    #         ;;
    #     status_WS_OPCUA)
    #         echo "WS OPC UA server docker info"
    #         docker-compose -f /opt/...../etc/... docker_compose_mongo.yaml ps
    #         exit
    #         ;;

    ##############################    WS DB ACTIONS    ##################################
    start_WS_DB)
        echo "Starting WS DB docker container..."
        docker-compose -f /.../docker_compose_mongo.yaml up -d
        sleep 3
        data=$(docker ps | grep mongodb-WS)
        if [ $(echo $data | wc -l ) -eq 1 ]; then
            echo "WS DB docker container is running and is up since $(docker ps | grep mongodb-WS | awk '{print $8" "$9}')."
        else
            echo "An error occured and it was not possible to start the WS DB container."
        fi
        exit
        ;;
    stop_WS_DB)
        echo "Stopping WS DB docker container..."
        docker-compose -f /.../docker_compose_mongo.yaml down
        sleep 3
        data=$(docker ps | grep mongodb-WS)
        if [ $(echo $data | wc -l ) -eq 0 ]; then
            echo "WS DB docker container is down. Operation successful!"
        elif [ $(echo $data | wc -l ) -eq 1 ]; then
            echo "WS DB docker container is still running."
        else
            echo "Something is wrong."
        fi
        exit
        ;;
    # kill)
    #     echo "Killing WS container"
    #     docker-compose -f /opt/...../etc/... docker_compose_mongo.yaml kill
    #     docker-compose -f /opt/...../etc/... docker_compose_mongo.yaml down
    #     exit
    #     ;;
    status_WS_DB)
        echo "Checking WS DB docker container state..."
        data=$(docker ps | grep mongodb-WS)
        if [ $(echo $data | wc -l ) -eq 1 ]; then
            echo "WS DB docker container is running and is up since $(docker ps | grep mongodb-WS | awk '{print $8" "$9}')."
        elif [ $(echo $data | wc -l ) -eq 0 ]; then
            echo "WS DB docker container is NOT running."
        else
            echo "Something is wrong."
        fi
        exit
        ;;

    #############################    WS DATA SCRIPT    ##############################
    start_WS_client)
        #echo "Starting the WS client"
        source /.../start_WS.sh
        sleep 1
        exit
        ;;
    stop_WS_client)
        echo "Killing the WS client..."
        ps aux | grep runWS.py | grep python | awk '{system("kill " $2)}'
        sleep 1
        echo "Done!"
        exit
        ;;
    status_WS_client)
        p=`ps aux | grep runWS.py | grep python | wc -l`
        if [ $p -eq 1 ]; then
            echo "WS client is running. All good!"
        elif [ $p -eq 0 ]; then
            echo "WS client is NOT running."
        else
            echo "Something is wrong. Please stop the WS client."
        fi
        exit
        ;;

    #############################    WS DASHBOARD    ##############################
    start_dashboard)
        #echo "Starting the WS dashboard"
        source /.../start_WSdashboard.sh
        sleep 1
        exit
        ;;
    stop_dashboard)
        echo "Killing the WS dashboard..."
        ps aux | grep app.py | grep python | awk '{system("kill " $2)}'
        sleep 1
        echo "Done!"
        exit
        ;;
    status_dashboard)
        p=`ps aux | grep app.py | grep python | wc -l`
        if [ $p -eq 1 ]; then
            echo "WS dashboard is running. All good!"
        elif [ $p -eq 0 ]; then
            echo "WS dashboard is NOT running."
        else
            echo "Something is wrong. Please stop the WS dashboard."
        fi
        exit
        ;;

esac
