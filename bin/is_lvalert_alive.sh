#!/bin/sh
# usage : is_lvalert_alive.sh ${resource} ${config} ${out} ${err} "${recipients}" 
# written by Reed Essick (reed.essick@ligo.org)

# check whether a lvalert process exists. If not, we attempt to launch one.
# right now, we rely on the netrc file being in the standard location (~/.netrc)

#--------------------------------------------------------------------------

### parser command line
resource=${1}   ### resource for lvalert_listen
config=${2}     ### configuration file for lvalert_listen
out=${3}        ### out file for lvalert_listen
err=${4}        ### err file for lvalert_listen
recipients=${5} ### email addresses for restart notifications

#--------------------------------------------------------------------------

### report when we ran
echo `date`

### check whether process is alive or not by looking in the process table
### we first extract all PIDs associated with this user (-u), and only then request the full command line (-F)
### then we filter based on lvalert command line options

Proc=$(ps -u $(whoami) | grep "lvalert_listen" | awk '{print $1}')
if [ -n "${Proc}" ]
then
    Proc=$(ps -F ${Proc} | grep ${resource} | grep ${config})
fi

if [ -z "$Proc" ] ### if empty, there is no process
then
	echo "process does not exist"

    ### restart process
	echo "nohup lvalert_listen --resource ${resource} --config-file ${config} --dont-wait 1>> ${out} 2>> ${err} &"
    nohup lvalert_listen --resource ${resource} --config-file ${config} --dont-wait 1>> ${out} 2>> ${err} &

    ### send an email warning
	if [ -n "${recipients}" ]
	then
            echo "sending email to ${recipients}"
#	        echo "echo \"cron monitor on ${HOSTNAME} restarted lvalert_listen running under $(whoami) with resource=${resource} and eonfig=${config} at $(date) -> GPS=$(lalapps_tconvert now).\" | mailx -s \"lvalert_listen restarted on ${HOSTNAME}\" \"${recipients}\""
	        echo "cron monitor on ${HOSTNAME} restarted lvalert_listen running under $(whoami) with resource=${resource} and eonfig=${config} at $(date) -> GPS=$(lalapps_tconvert now)." | mailx -s "lvalert_listen restarted on ${HOSTNAME}" "${recipients}"
	fi
else ### process does exist
	echo "process exists"
	echo ${Proc}
fi
