#!/bin/sh
if [ $# != 4 ]; then
   echo "Parameters  counts must be 4!"
   exit 1
fi
Package_Name=$1
Jenkins_Start_Time=$2
Package_Version=$3
Process_Num_Plan=$4
echo $Package_Name
echo $Package_Version
echo $Jenkins_Start_Time
echo $Process_Num_Plan
# 检查package_name对应的进程数量是否等于计划的process_num_plan
function check_process_num()
{
    Process_Num=`ps -ef |grep "/data/app/${Package_Name}/" | grep -v grep | grep -v logstash |wc -l`
    echo ${Process_Num}
    if [ ${Process_Num} == ${Process_Num_Plan} ];then
	    echo "Right! The processes for the project ${Package_Name} is equal to ${Process_Num_Plan}..."
	    return 0
    else
        echo "Error!!! The processes for the project ${Package_Name} is not equal to ${Process_Num_Plan}...please check..."
        exit 1
    fi
}

check_process_num
# 检查进程的启动时间和jenkins部署job的时间对比
function check_deploy_time()
{
    PID=`ps -ef |grep "/data/app/${Package_Name}/" | grep -v grep | grep -v logstash |awk '{print $2}'`
    echo $PID
    #JIFFIES=`cat /proc/$PID/stat|cut -d " " -f 22`
    JIFFIES=`cat /proc/$PID/stat|sed 's/(.*)/CMD/' |awk '{print $22}'`
    UPTIME=`grep btime /proc/stat|cut -d " " -f 2`
    START_SEC=$(($UPTIME + $JIFFIES/$(getconf CLK_TCK)))
    echo $START_SEC
    if [ -n "${START_SEC}" -a "${START_SEC}" == "${START_SEC//[^0-9]/}" ];then
       if [ ${START_SEC} -gt ${Jenkins_Start_Time} ];then
           echo "Process start time correctly"
           return 0
       else
           echo "Process start time incorrectly"
           exit 1
       fi
     else
       echo "$START_SEC is wrong"
       exit 1
    fi
}

check_deploy_time
function check_package_version()
{
   Current_Package_Version=`readlink "/data/app/${Package_Name}/bin"|awk -F "[/|-]" '{print $7}'`
   echo $Current_Package_Version
   if [ ${Current_Package_Version} == ${Package_Version} ];then
       echo "Package  version is Correct"
       return 0
   else
       echo "Package version is not  correct"
       exit 1
   fi
}

check_package_version
