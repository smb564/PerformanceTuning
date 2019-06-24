#!/usr/bin/env bash
source venv/bin/activate

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")

RU="60"
RU1="30"
RU2="30"
MI="3600"
RD="60"
URL="http://192.168.32.10:80"

# Interval in which performance is measured
MEASURING_INTERVAL="60"

# Time window to take average response time
MEASURING_WINDOW="60"

PARENT_FOLDER="nginx_dataset/browsing/"

if [[ -d "${PARENT_FOLDER}" ]]
then
    read -p "Parent directory already exists. Replace? (Y/n)" yn
    case $yn in
        [Yy]* ) true;;
        * ) exit;;
    esac
fi

python3 add_result_summary.py "start" ${PARENT_FOLDER}

mkdir -p ${PARENT_FOLDER}

for MIX in 1
do
    for CONCURRENCY in 350 700 1050 1260 1400 1750
    do
        FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}"
        ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"

        CASE_NAME="default"

        # restart nginx
        ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx stop"
        sleep 10s
        ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx start"

        # restart Tomcat
        ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"
        sleep 10s

        # run the performance test
        nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
        "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
        "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
        "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD " \
        "-ITEM 1000 -TT 1 -MAXERROR 0 -WWW ${URL}/tpcw/" > eb.log &

        sleep ${RU1}s

        # reconnect the monitor server to the new Tomcat instance
        curl 192.168.32.2:8080/reconnect
        sleep ${RU2}s

        nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &
        # to finish the tests after the time eliminates
        sleep ${MI}s
        python3 add_result_summary.py ${RU} ${MI} ${RD}
        sleep ${RD}s

        # reset the database
        ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
        ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"

        for THREAD in 50 100 200
        do
            FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}"
            ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"

            CASE_NAME="thread_${THREAD}"

            # restart nginx
            ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx stop"
            sleep 10s
            ssh wso2@192.168.32.10 "sudo /etc/init.d/nginx start"

            # restart Tomcat
            ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"
            sleep 10s

            curl -XPUT "http://192.168.32.2:8080/setparam?name=minSpareThreads&value=${THREAD}"
            curl -XPUT "http://192.168.32.2:8080/setparam?name=maxThreads&value=${THREAD}"

            # run the performance test
            nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
            "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
            "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
            "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD " \
            "-ITEM 1000 -TT 1 -MAXERROR 0 -WWW ${URL}/tpcw/" > eb.log &

            sleep ${RU1}s

            # reconnect the monitor server to the new Tomcat instance
            curl 192.168.32.2:8080/reconnect
            sleep ${RU2}s

            nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &
            # to finish the tests after the time eliminates
            sleep ${MI}s
            python3 add_result_summary.py ${RU} ${MI} ${RD}
            sleep ${RD}s

            # reset the database
            ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
            ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"

        done
    done
done
