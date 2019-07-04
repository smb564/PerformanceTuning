#!/usr/bin/env bash
source venv/bin/activate

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")

RU="240"
RU1="120"
RU2="120"
MI="1200"
RD="120"
URL="http://192.168.32.2:80"
GETIM="true"

# Interval in which performance is measured
MEASURING_INTERVAL="10"

# Time window to take average response time
MEASURING_WINDOW="60"

PARENT_FOLDER="nginx_dataset/dataset/"

if [[ -d "${PARENT_FOLDER}" ]]
then
    read -p "Parent directory already exists. Replace? (Y/n)" yn
    case $yn in
        [Yy]* ) true;;
        * ) exit;;
    esac
fi

mkdir -p ${PARENT_FOLDER}

python3 add_result_summary.py "start" ${PARENT_FOLDER}

for MIX in 2 3 1
do
    for CONCURRENCY in 350 700 1050 1400 1750
    do
        FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}"
        ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"

        CASE_NAME="default"

        # restart nginx
        ssh wso2@192.168.32.2 "sudo /etc/init.d/nginx stop"
        sleep 10s
        ssh wso2@192.168.32.2 "sudo /etc/init.d/nginx start"

        # restart Tomcat
        ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

        # run the performance test
        nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
        "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
        "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
        "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD " \
        "-ITEM 1000 -TT 1 -MAXERROR 0 -WWW ${URL}/tpcw/ -GETIM ${GETIM}" > eb.log &

        sleep ${RU1}s

        # reconnect the monitor server to the new Tomcat instance
        curl 192.168.32.2:8080/reconnect
        sleep ${RU2}s

        nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &

        nohup ssh wso2@192.168.32.11 "sar -q 1 ${MI} > tomcat.sar" &
        nohup ssh wso2@192.168.32.2 "sar -q 1 ${MI} > nginx.sar" &
        nohup ssh wso2@192.168.32.7 "sar -q 1 ${MI} > mysql.sar" &

        # to finish the tests after the time eliminates
        sleep ${MI}s
        python3 add_result_summary.py ${RU} ${MI} ${RD} ${PARENT_FOLDER} ${CONCURRENCY} ${CASE_NAME}

        ssh wso2@192.168.32.11 "cat tomcat.sar" | python3 collect_sar.py ${FOLDER_NAME}/${CASE_NAME}/tomcat
        ssh wso2@192.168.32.2 "cat nginx.sar" | python3 collect_sar.py ${FOLDER_NAME}/${CASE_NAME}/nginx
        ssh wso2@192.168.32.7 "cat mysql.sar" | python3 collect_sar.py ${FOLDER_NAME}/${CASE_NAME}/mysql


        ssh wso2@192.168.32.2 "sudo /etc/init.d/nginx stop"
        ssh wso2@192.168.32.11 "./supun/scripts/stop-tomcat.sh"

        sleep ${RD}s
#        echo "Resetting the database $(date)"
#
#        # reset the database
#        ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
#        ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"
#
#        echo "Database reset completed $(date)"

        for THREAD in 50 100 200
        do
            FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}"
            ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"

            CASE_NAME="thread_${THREAD}"

            # restart nginx
            ssh wso2@192.168.32.2 "sudo /etc/init.d/nginx stop"
            sleep 10s
            ssh wso2@192.168.32.2 "sudo /etc/init.d/nginx start"

            # restart Tomcat
            ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"
            curl 192.168.32.2:8080/reconnect
            sleep 10s
            curl -XPUT "http://192.168.32.2:8080/setparam?name=minSpareThreads&value=${THREAD}"
            curl -XPUT "http://192.168.32.2:8080/setparam?name=maxThreads&value=${THREAD}"

            # run the performance test
            nohup ssh wso2@192.168.32.6 "cd supun/dist && java -Dcom.sun.management.jmxremote " \
            "-Dcom.sun.management.jmxremote.port=9010 -Dcom.sun.management.jmxremote.local.only=false " \
            "-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false " \
            "-jar rbe.jar -WINDOW ${MEASURING_WINDOW} -EB rbe.EBTPCW${MIX}Factory $CONCURRENCY -OUT $FOLDER_NAME/$CASE_NAME.m -RU $RU -MI $MI -RD $RD " \
            "-ITEM 1000 -TT 1 -MAXERROR 0 -WWW ${URL}/tpcw/" -GETIM ${GETIM} > eb.log &

            sleep ${RU1}s
            # reconnect the monitor server to the new Tomcat instance
            curl 192.168.32.2:8080/reconnect
            sleep ${RU2}s

            nohup python3 client_side_metrics.py "$FOLDER_NAME" "$CASE_NAME" "0" "$MI" "0" "$MEASURING_INTERVAL" "${MEASURING_WINDOW}"> client_side.txt &

            nohup ssh wso2@192.168.32.11 "sar -q 1 ${MI} > tomcat.sar" &
            nohup ssh wso2@192.168.32.2 "sar -q 1 ${MI} > nginx.sar" &
            nohup ssh wso2@192.168.32.7 "sar -q 1 ${MI} > mysql.sar" &

            # to finish the tests after the time eliminates
            sleep ${MI}s
            python3 add_result_summary.py ${RU} ${MI} ${RD} ${PARENT_FOLDER} ${CONCURRENCY} ${CASE_NAME}

            ssh wso2@192.168.32.11 "cat tomcat.sar" | python3 collect_sar.py ${FOLDER_NAME}/${CASE_NAME}/tomcat
            ssh wso2@192.168.32.2 "cat nginx.sar" | python3 collect_sar.py ${FOLDER_NAME}/${CASE_NAME}/nginx
            ssh wso2@192.168.32.7 "cat mysql.sar" | python3 collect_sar.py ${FOLDER_NAME}/${CASE_NAME}/mysql

            ssh wso2@192.168.32.2 "sudo /etc/init.d/nginx stop"
            ssh wso2@192.168.32.11 "./supun/scripts/stop-tomcat.sh"

            sleep ${RD}s

#            echo "Resetting the database $(date)"
#
#            # reset the database
#            ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
#            ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"
#
#            echo "Database reset completed $(date)"
        done

        echo "Resetting the database $(date)"

        # reset the database
        ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 < drop_and_create.sql"
        ssh wso2@192.168.32.11 "mysql -u root -h 192.168.32.7 -pjavawso2 tpcw < tpcw-dump.sql"

        echo "Database reset completed $(date)"
    done
done