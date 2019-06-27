#!/usr/bin/env bash
source venv/bin/activate

optimizer="skopt_gp_only_tomcat.py"

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")

declare -A MIX2CONCURRENCY
MIX2CONCURRENCY=( ["1"]="350" ["2"]="600" ["3"]="100")

TT="1"
RU="240"
RU1="120"
RU2="120"
MI="3600"
RD="60"
URL="http://192.168.32.10:80"
GETIM="false"

# Parameters are tuned this often
TUNING_INTERVAL="120"

# Time window to take average response time
MEASURING_WINDOW="60"

# Interval in which performance is measured
MEASURING_INTERVAL="10"

PARENT_FOLDER="ngnix/99p_tuning/browsing_tt_1"

if [[ -d "${PARENT_FOLDER}" ]]
then
    read -p "Parent directory already exists. Replace? (Y/n)" yn
    case $yn in
        [Yy]* ) true;;
        * ) exit;;
    esac
fi

mkdir -p ${PARENT_FOLDER}

for MIX in 1
do
    CONCURRENCY=${MIX2CONCURRENCY[${MIX}]}
    FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}"

    # create the directory at client side
    ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"

    CASE_NAME="tuning"
    echo "Running the tuning case"

    # restart nginx
    ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx stop"
    sleep 10s
    ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx start"

    echo "Restarting tomcat server..."
    # restart the tomcat server
    ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

    echo "Tomcat restarted"

    # start the client
    nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
    "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
    "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
    "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD " \
    "-ITEM 1000 -TT ${TT} -MAXERROR 0 -WWW ${URL}/tpcw/ -GETIM ${GETIM}" > eb.log &

    sleep ${RU1}s
    # reconnect the monitor server to the new Tomcat instance
    curl 192.168.32.2:8080/reconnect
    sleep ${RU2}s

    nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &
    nohup python3 ${optimizer} "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$TUNING_INTERVAL"> optimizer.log &

    # to finish the tests after the time eliminates
    sleep ${MI}s
    ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx stop"
    ssh wso2@192.168.32.11 "./supun/scripts/stop-tomcat.sh"

    # reset the database
    ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
    ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"

    # running the none tuning case
    CASE_NAME="default"
    echo "Running the default case without tuning"

    # restart nginx
    ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx stop"
    sleep 10s
    ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx start"

    echo "Restarting tomcat server..."
    # restart the tomcat server
    ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

    echo "Tomcat restarted"

    # start the client
    nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
    "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
    "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
    "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD " \
    "$RD -ITEM 1000 -TT ${TT} -MAXERROR 0 -WWW ${URL}/tpcw/ -GETIM ${GETIM}" > eb.log &

    sleep ${RU1}s

    # reconnect the monitor server to the new Tomcat instance
    curl 192.168.32.2:8080/reconnect
    sleep ${RU2}s

    nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &

    # to finish the tests after the time eliminates
    sleep ${MI}s
    ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx stop"
    ssh wso2@192.168.32.11 "./supun/scripts/stop-tomcat.sh"

    # now join the plots
    python3 join_plots.py ${FOLDER_NAME} "default" "tuning"

    # reset the database
    ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
    ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"

done
