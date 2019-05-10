#!/usr/bin/env bash
source venv/bin/activate

MODEL="mpm_event"
FOLDER_NAME="apache_max_clients"
CASE_NAME="browsing_worker_"
RU="60"
MI="300"
RD="0"
CONCURRENCY="200"

# Interval in which performance is measured
MEASURING_INTERVAL="20"

mkdir ${FOLDER_NAME}

if [[ -d "$FOLDER_NAME/$CASE_NAME" ]]
then
    read -p "Directory already exists. Replace? (Y/n)" yn
    case $yn in
        [Yy]* ) true;;
        * ) exit;;
    esac
fi

# set the required mpm module
curl 192.168.32.10:5001/setModel?model=${MODEL}

ssh wso2@192.168.32.6 "cd supun/dist && mkdir $FOLDER_NAME"

for PARAM in 10 50 100 150 200 250 400
do
    echo "Running for case $PARAM"
    ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 stop"
    ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 start"

    ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"
    curl 192.168.32.1:8080/reconnect
    sleep 3s

    curl 192.168.32.10:5001/setParam?MaxRequestWorkers=${PARAM}
    sleep 5s

    nohup python3 server_side_metrics.py "$FOLDER_NAME" "$CASE_NAME${CONCURRENCY}_$PARAM" "$RU" "$MI" "$RD" "$MEASURING_INTERVAL">metrics_log.txt &

    ssh wso2@192.168.32.6 "cd supun/dist && java rbe.RBE -EB rbe.EBTPCW1Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME${CONCURRENCY}_$PARAM.m -RU $RU -MI $MI -RD $RD -ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW http://192.168.32.10:80/tpcw/"

done