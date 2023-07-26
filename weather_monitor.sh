#!/bin/bash

NUM=$(ps aux | grep weather_monitor | grep -v tail | grep -v vim | grep -v defunct | grep -c -v grep)

if [ $NUM -eq 0 ] || [ $NUM -eq 2 ]; then
  date
  echo "starting weather_monitor..."
  while true; do

    NUM=$(ps aux | grep ORM_WSdata | grep -v tail | grep -v vim | grep -v defunct | grep -c -v grep)

    if [ $NUM -eq 1 ]; then
      rsync /opt/lst-safetybroker/bin/WS10.txt /opt/lst-safetybroker/bin/WS10_all.txt lst1@www.lst1.iac.es:/home/www/html/operations/weather/ >> /dev/null 2>&1
    elif [ $NUM -eq 0 ]; then
      while [ $NUM -eq 0 ]; do
        date
        echo "starting ORM_WSdata..."
        conda activate modbus
        python /opt/lst-safetybroker/bin/ORM_WSdata.py &
        sleep 1
        NUM=$(ps aux | grep ORM_WSdata | grep -v tail | grep -v vim | grep -v defunct | grep -c -v grep)
      done
      echo "done!"
    fi
    sleep 30
  done
elif [ $NUM -eq 1 ]; then
  exit 1
fi

exit 0