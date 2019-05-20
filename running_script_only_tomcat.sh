#!/usr/bin/env bash
source venv/bin/activate

optimizer="bayesian_opt_only_tomcat.py"

declare -A MIX2NAME
MIX2NAME=( ["1"]="browsing" ["2"]="shopping" ["3"]="ordering")

RU="60"
MI="600"
RD="60"
URL="http://192.168.32.11:8080"

# Parameters are tuned this often
TUNING_INTERVAL="60"

# Interval in which performance is measured
MEASURING_INTERVAL="20"

PARENT_FOLDER="only_tomcat_tpe"

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
        FOLDER_NAME="${PARENT_FOLDER}/${MIX2NAME[${MIX}]}_${CONCURRENCY}"

        # create the directory at client side
        ssh wso2@192.168.32.6 "cd supun/dist && mkdir -p $FOLDER_NAME"


        CASE_NAME="tuning"
        echo "Running the tuning case"

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
        ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

        # running the none tuning case
        CASE_NAME="default"
        echo "Running the default case without tuning"

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
        ssh wso2@192.168.32.11 "./supun/scripts/restart-tomcat.sh"

        # now join the plots
        python3 join_plots.py ${FOLDER_NAME} "default" "tuning"
    done
done
