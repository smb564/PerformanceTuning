#!/usr/bin/env bash
source venv/bin/activate

MODEL="mpm_event"
FOLDER_NAME="apache_server_metrics"
CASE_NAME="tpcw_"
RU="60"
MI="600"
RD="60"
#CONCURRENCY="100"

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")

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

for MIX in 1 2 3
do
    for CONCURRENCY in 50 100 150 200
    do
        for PARAM in 100 200 400
        do
            echo "Running for case $PARAM"
            ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 stop"
            ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 start"

            nohup ssh wso2@192.168.32.10 "tail -0f /var/log/apache2/access.log | java -jar -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false /home/wso2/supun/apache-metrics-1.0-SNAPSHOT.jar" &

            ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"
            curl 192.168.32.1:8080/reconnect
            sleep 3s

            curl 192.168.32.10:5001/setParam?MaxRequestWorkers=${PARAM}
            sleep 5s

            nohup python3 server_side_metrics.py "$FOLDER_NAME" "$CASE_NAME${CONCURRENCY}_$PARAM" "$RU" "$MI" "$RD" "$MEASURING_INTERVAL">metrics_log.txt &

            ssh wso2@192.168.32.6 "cd supun/dist && java rbe.RBE -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/${CASE_NAME}_${MIX2NAME[${MIX}]}_${CONCURRENCY}_$PARAM.m -RU $RU -MI $MI -RD $RD -ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW http://192.168.32.10:80/tpcw/"

            ssh wso2@192.168.32.10 "./supun/stop-java.sh"
        done
    done
done