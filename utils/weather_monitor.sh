#!/bin/bash

NUM=$(ps aux | grep weather_monitor | grep -v tail | grep -v vim | grep -v defunct | grep -c -v grep)

if [ $NUM -eq 0 ] || [ $NUM -eq 2 ]; then
  echo "starting weather_monitor..."
  #while true; do

  NUM=$(ps aux | grep ORM_WSdata | grep -v tail | grep -v vim | grep -v defunct | grep -c -v grep)

  if [ $NUM -eq 1 ]; then
    rsync -a -e 'ssh -i /.../.ssh/id_[NAME]' --chmod=o=r /.../WS10.txt lst1@www.lst1.iac.es:/home/.../ >> /dev/null 2>&1
  elif [ $NUM -eq 0 ]; then
    while [ $NUM -eq 0 ]; do
      date
      echo "starting ORM_WSdata..."
      CONDA_INIT_SCRIPT="/.../conda/conda_init.sh"
      source "$CONDA_INIT_SCRIPT"
      conda activate ws
      nohup python -u /.../ORM_WSdata.py 2>&1 >> /.../ORM_WSdata.out &
      sleep 10
      NUM=$(ps aux | grep ORM_WSdata | grep -v tail | grep -v vim | grep -v defunct | grep -c -v grep)
    done
    echo "done!"
  fi
  #sleep 40
  #done
elif [ $NUM -eq 1 ]; then
  exit 1
fi

exit 0