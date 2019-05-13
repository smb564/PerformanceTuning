#!/usr/bin/env bash
source venv/bin/activate

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")
MIX=3
CONCURRENCY="100"


TUNE=true
FOLDER_NAME="tuning_both"
CASE_NAME="${MIX2NAME[${MIX}]}_${CONCURRENCY}_tuning_both"

RU="60"
MI="600"
RD="60"

# Parameters are tuned this often
TUNING_INTERVAL="60"

# Interval in which performance is measured
MEASURING_INTERVAL="20"

MODEL="mpm_event"

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

sleep 1s

ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 stop"
ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 start"

# start the apache metrics collection java program
nohup ssh wso2@192.168.32.10 "tail -0f /var/log/apache2/access.log | java -jar -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false /home/wso2/supun/apache-metrics-1.0-SNAPSHOT.jar" &

echo "Restarting tomcat server..."
# restart the tomcat server
ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

echo "Tomcat restarted"

echo "Reconnecting Performance Monitor to Tomcat"
# reconnect the monitor server to the new Tomcat instance
curl 192.168.32.1:8080/reconnect

echo "Done"
# just in case the monitor takes some to connect
sleep 3s

echo "Starting EBs.."
# run the performance test

# create folder
ssh wso2@192.168.32.6 "cd supun/dist && mkdir $FOLDER_NAME"
nohup ssh wso2@192.168.32.6 "cd supun/dist && java rbe.RBE -EB rbe.EBTPCW2Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD -ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW http://192.168.32.10:80/tpcw/" > eb_log.txt &
#

echo "EB Command Executed"

echo "Running python script to collect performance numbers"

if $TUNE
then
    nohup python3 server_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "$RU" "$MI" "$RD" "$MEASURING_INTERVAL"> metrics_log.txt &

    echo "Starting running the optimizer"
    python3 bayesian_opt.py "$FOLDER_NAME" "$CASE_NAME" "$RU" "$MI" "$RD" "$TUNING_INTERVAL"
else
    python3 server_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "$RU" "$MI" "$RD" "$MEASURING_INTERVAL"
fi

# kill the apache metrics collection java program (assuming it is the only java program)
ssh wso2@192.168.32.10 "./supun/stop-java.sh"