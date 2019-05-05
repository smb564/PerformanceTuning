#!/usr/bin/env bash
source venv/bin/activate

TUNE=true
FOLDER_NAME="tuning_both"
CASE_NAME="browsing_100_tuning_both"
RU="60"
MI="1800"
RD="60"

# Parameters are tuned this often
TUNING_INTERVAL="120"

# Interval in which performance is measured
MEASURING_INTERVAL="20"

if [[ -d "tuning_both/$CASE_NAME" ]]
then
    read -p "Directory already exists. Replace? (Y/n)" yn
    case $yn in
        [Yy]* ) true;;
        * ) exit;;
    esac
fi

ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 stop"
ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 start"


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
nohup ssh wso2@192.168.32.6 "cd supun/dist && java rbe.RBE -EB rbe.EBTPCW1Factory 100 -OUT tuning_both/browsing_100.m -RU $RU -MI $MI -RD $RD -ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW http://192.168.32.10:80/tpcw/" > eb_log.txt &
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