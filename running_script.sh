#!/usr/bin/env bash
source venv/bin/activate

optimizer="gp_optimizer.py"

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")
MIX=1
CONCURRENCY="400"

RU="60"
MI="600"
RD="60"
URL="http://192.168.32.10:80"

# Parameters are tuned this often
TUNING_INTERVAL="60"

# Interval in which performance is measured
MEASURING_INTERVAL="20"

MODEL="mpm_prefork"

PARENT_FOLDER="tuning_both_same_gpopt"

if [[ -d "${PARENT_FOLDER}" ]]
then
    read -p "Parent directory already exists. Replace? (Y/n)" yn
    case $yn in
        [Yy]* ) true;;
        * ) exit;;
    esac
fi

mkdir -p ${PARENT_FOLDER}

for MIX in 1 2 3
do
    for CONCURRENCY in 100 200 300 400
    do
        FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}_${MODEL}"
        ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"


        CASE_NAME="tuning"
        echo "Running the tuning case"

        # create the directory at client side

        # set the required mpm module
        curl 192.168.32.10:5001/setModel?model=${MODEL}

        # set the default parameters
        curl 192.168.32.10:5001/default

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

        # just in case the monitor takes some to connect
        sleep 3s

        nohup python3 server_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "$RU" "$MI" "$RD" "$MEASURING_INTERVAL"> metrics_log.txt &
        nohup python3 ${optimizer} "$FOLDER_NAME" "$CASE_NAME" "$RU" "$MI" "$RD" "$TUNING_INTERVAL"> optimizer.log &

        # run the performance test
        nohup ssh wso2@192.168.32.6 "cd supun/dist && java rbe.RBE -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD -ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW ${URL}/tpcw/" > eb.log &

        # to finish the tests after the time eliminates
        sleep ${RU}s
        sleep ${MI}s
        sleep ${RD}s
        sleep 100s

        ssh wso2@192.168.32.10 "./supun/stop-java.sh"

        ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 stop"
        ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 start"


        # running the none tuning case
        CASE_NAME="default"
        echo "Running the default case without tuning"

        # set the default parameters
        curl 192.168.32.10:5001/default

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

        # just in case the monitor takes some to connect
        sleep 3s

        nohup python3 server_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "$RU" "$MI" "$RD" "$MEASURING_INTERVAL"> metrics_log.txt &

        # run the performance test
        nohup ssh wso2@192.168.32.6 "cd supun/dist && java rbe.RBE -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD -ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW ${URL}/tpcw/" > eb.log &

        # to finish the tests after the time eliminates
        sleep ${RU}s
        sleep ${MI}s
        sleep ${RD}s
        sleep 100s

        ssh wso2@192.168.32.10 "./supun/stop-java.sh"

        ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 stop"
        ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 start"

        # now join the plots
        python3 join_plots.py ${FOLDER_NAME} "default" "tuning"
    done
done

