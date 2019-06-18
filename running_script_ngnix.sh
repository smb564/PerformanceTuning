#!/usr/bin/env bash
source venv/bin/activate

optimizer="skopt_gp_only_tomcat.py"

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")

declare -A MIX2CONCURRENCY
MIX2CONCURRENCY=( ["1"]="1000" ["2"]="600" ["3"]="100")

TT="0.8"
RU="60"
MI="3600"
RD="60"
URL="http://192.168.32.10:80"

# Parameters are tuned this often
TUNING_INTERVAL="120"

# Time window to take average response time
MEASURING_WINDOW="60"

# Interval in which performance is measured
MEASURING_INTERVAL="60"

PARENT_FOLDER="ngnix/long_tt_0.8"

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
    CONCURRENCY=${MIX2CONCURRENCY[${MIX}]}
    FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}"

    # create the directory at client side
    ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"

    CASE_NAME="tuning"
    echo "Running the tuning case"

    ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx restart"

    echo "Restarting tomcat server..."
    # restart the tomcat server
    ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

    echo "Tomcat restarted"

    # start the client
    nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
    "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
    "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
    "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD " \
    "-ITEM 1000 -TT ${TT} -MAXERROR 0 -WWW ${URL}/tpcw/" > eb.log &

    sleep ${RU}s

    echo "Reconnecting Performance Monitor to Tomcat"
    # reconnect the monitor server to the new Tomcat instance
    curl 192.168.32.2:8080/reconnect

    nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &
    nohup python3 ${optimizer} "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$TUNING_INTERVAL"> optimizer.log &

    # to finish the tests after the time eliminates
    sleep ${MI}s
    sleep ${RD}s
    sleep 100s

    # reset the database
    ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
    ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"

    # running the none tuning case
    CASE_NAME="default"
    echo "Running the default case without tuning"

    ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx restart"

    echo "Restarting tomcat server..."
    # restart the tomcat server
    ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

    echo "Tomcat restarted"

    # start the client
    nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
    "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
    "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
    "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD " \
    "$RD -ITEM 1000 -TT ${TT} -MAXERROR 0 -WWW ${URL}/tpcw/" > eb.log &

    sleep ${RU}s

    echo "Reconnecting Performance Monitor to Tomcat"
    # reconnect the monitor server to the new Tomcat instance
    curl 192.168.32.2:8080/reconnect

    nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &

    # to finish the tests after the time eliminates
    sleep ${MI}s
    sleep ${RD}s
    sleep 100s


    # now join the plots
    python3 join_plots.py ${FOLDER_NAME} "default" "tuning"

    # reset the database
    ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
    ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"

done
