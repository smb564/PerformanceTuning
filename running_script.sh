#!/usr/bin/env bash
source venv/bin/activate

TUNE=false
CASE_NAME="shopping_100_tuning_without_apache"

if [[ -d "server_metrics/$CASE_NAME" ]]
then
    read -p "Directory already exists. Replace?" yn
    case $yn in
        [Yy]* ) true;;
        * ) exit;;
    esac
fi


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

#ssh wso2@192.168.32.6 "cd supun/dist && java rbe.RBE -EB rbe.EBTPCW2Factory 200 -OUT data/test.m -RU 60 -MI 600 -RD 60 -ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW http://192.168.32.11:8080/tpcw/"

echo "Starting EBs.."
# run the performance test
nohup ssh wso2@192.168.32.6 "cd supun/dist && java rbe.RBE -EB rbe.EBTPCW2Factory 100 -OUT tune_results_without_apache/shopping_100_default.m -RU 60 -MI 600 -RD 60 -ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW http://192.168.32.11:8080/tpcw/" > eb_log.txt &
#

echo "EB Command Executed"

echo "Running python script to collect performance numbers"

if $TUNE
then
    ## TODO: This can get stuck here if the directory (case_name) already exists because it provieds a prompt
    nohup python3 server_side_metrics.py "$CASE_NAME"> metrics_log.txt &

    echo "Starting running the optimizer"
    python3 bayesian_opt.py
else
    python3 server_side_metrics.py "$CASE_NAME"
fi