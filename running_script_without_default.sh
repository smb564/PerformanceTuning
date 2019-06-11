#!/usr/bin/env bash
source venv/bin/activate

optimizer="gp_optimizer.py"

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")

declare -A MIX2CONCURRENCY
MIX2CONCURRENCY=( ["1"]="180" ["2"]="100" ["3"]="30")


RU="60"
MI="3600"
RD="60"
URL="http://192.168.32.10:80"

# Parameters are tuned this often
TUNING_INTERVAL="120"

# Interval in which performance is measured
MEASURING_INTERVAL="20"

# Time window to take average response time
MEASURING_WINDOW="60"

MODEL="mpm_prefork"

PARENT_FOLDER="tuning_both_skopt_long_client_numbers_3_nodes_only_tomcat"

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
    for CONCURRENCY in 100
    do
        # TODO: Remove this for normal scenarios
        CONCURRENCY=${MIX2CONCURRENCY[${MIX}]}
        FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}_${MODEL}"
        ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"


        CASE_NAME="tuning"
        echo "Running the tuning case"

        # set the required mpm module
        curl 192.168.32.10:5001/setModel?model=${MODEL}

        # set the default parameters
        curl 192.168.32.10:5001/default

        sleep 1s

        ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 stop"
        ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 start"

        # start the apache metrics collection java program
        nohup ssh wso2@192.168.32.10 "tail -0f /var/log/apache2/access.log | java -jar -Dcom.sun.management.jmxremote "\
        "-Dcom.sun.management.jmxremote.port=9010 " \
        "-Dcom.sun.management.jmxremote.local.only=false -Dcom.sun.management.jmxremote.authenticate=false " \
        "-Dcom.sun.management.jmxremote.ssl=false /home/wso2/supun/apache-metrics-1.0-SNAPSHOT.jar ${MEASURING_WINDOW}" > apache_metrics.log &

        echo "Restarting tomcat server..."
        # restart the tomcat server
        ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

        echo "Tomcat restarted"

        # run the performance test
        nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
        "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
        "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
        "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD " \
        "-ITEM 1000 -TT 0.1 -MAXERROR 0 -WWW ${URL}/tpcw/" > eb.log &

        sleep ${RU}s

        echo "Reconnecting Performance Monitor"
        # reconnect the monitor server to the new Tomcat instance
        curl 192.168.32.2:8080/reconnect

#        nohup python3 server_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "$RU" "$MI" "$RD" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> metrics_log.txt &
        nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &
        nohup python3 ${optimizer} "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$TUNING_INTERVAL"> optimizer.log &

        # to finish the tests after the time eliminates
        sleep ${MI}s
        sleep ${RD}s
        sleep 100s

        ssh wso2@192.168.32.10 "./supun/stop-java.sh"

        ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 stop"
        sleep 100s
        ssh wso2@192.168.32.10 "sudo /etc/init.d/apache2 start"

        # now join the plots
        python3 join_plots.py ${FOLDER_NAME} "../../default_numbers_3_nodes_long/${MIX2NAME[${MIX}]}_${CONCURRENCY}_${MODEL}/default" "tuning"
    done
done

