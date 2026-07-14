#!/bin/bash
usage () {                       
    echo "
    SUMMARY:

    This script staggers the start time of submitted jobs for a user.

    USAGE:

        bash $0 [ARG [OPTARG]]...

    Where ARG [OPTARG] can be the following:
    " ;
    grep " .)\ \#" $0 | sed 's/#//' | sed -r 's/([a-z])\)/-\1/';        
    exit $1;                                                             
}                                                                       
                                                                        

# Default options:
user=amin;
stat=Q;
mem=750;
stag_time=3600;
dry_run=false;

while getopts "hdu:s:m:t:" arg; do
    case "$arg" in
        h) # : Display help
            usage 0
            ;;
        d) # : Dry-run, will print out the command to run
            dry_run=true
            ;;
        u) # <Username> : (default is 'amin')
            user=$OPTARG
            ;;
        s) # <status> : Status to query (default is Q)
            stat=$OPTARG
            ;;
        m) # <memory> : Memory requested for job (default is 750)
            mem=$OPTARG
            ;;
        t) # <time> : Time to stagger (default is 3600 seconds)
            stag_time=$OPTARG
            ;;
        *) # All other options will fail
            usage 1
            ;;
    esac
done 

echo "qstat -u ${user} | grep ""${mem}gb   --  ${stat}   --"" | awk "'{print $1}'
IDs=$( qstat -u ${user} | grep "${mem}gb   --  ${stat}   --" | awk '{print $1}' )


START=$(date "+%s")

i=0
for id in $IDs; do
    time=$((START + i * ${stag_time}))
    job_time=$(date -d @"$time" +%Y%m%d%H%M)
    if ${dry_run} ; then
        echo "Dry run, would run:";
        echo "qalter -a $job_time $id";
     
    else
        qalter -a $job_time $id
    fi
    ((i++))
done

if [ $i == 0 ]; then
    echo "No jobs found with the given parameters"
fi
