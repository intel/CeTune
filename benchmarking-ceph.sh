#!/bin/bash

. conf/common.sh
get_conf

function usage_exit {
    echo -e "usage:\n\t $0 {-h|init-rbd|prerun-check|gen-case|run|show-result}"
    exit
}

function help_guide {
    cat .help_guide_benchmark
}

case $1 in
    -h | --help)
        help_guide_benchmark
        echo ""
        usage_exit
        ;;
    init-rbd)
        cd benchmarking
        bash init_rbd.sh
        cd ..
        ;;
    prerun-check)
        cd benchmarking
        bash before_test_check.sh
        cd ..
        ;;
    gen-case)
        cd benchmarking
        bash generate_test_cases.sh
        cat ../conf/cases.conf
        cd ..
        ;;
    run)
        if [ "$#" -eq 1 ];then
            echo -e "bash benchmarking-ceph.sh $1 --engine qemu/fiorbd/fiocephfs --type all/single"
            exit 1
        elif [ "$#" -ne 5 ];then
            echo "Wrong number of parameter! Please check your input!"
            exit 1
        fi
        shift 1
        while [ "$#" -gt 0 ]
        do
            case $1 in
                '--engine')
                    lengine=$2
                    shift 2
                    ;;
                '--type')
                    ltype=$2
                    shift 2
                    ;;
                *)
                    echo "Unrecognized option '$1'"
                    exit 1
                    ;;
            esac
        done
        if [ "${lengine}" == 'qemu' -o "${lengine}" == 'fiorbd' -o "${lengine}" == 'fiocephfs' ] && [ "${ltype}" == 'single' -o "${ltype}" == 'all' ];then
            cd benchmarking
            bash run_cases.sh ${ltype} ${lengine}
            cd ..
        else
            echo "Wrong input! Please check your input!"
            exit 1
        fi
        ;;
    show-result)
        shift 1
        if [ "$#" -gt 0 ]; then
            run=$1
        else
            index=1
            ls $dest_dir  | while read line
            do
                echo ${index}") "${line}
                index=$(( $index+1 ))
            done
            echo -n "Choose the run_id:"
            read run_id
            run=`ls $dest_dir | sed -n ${run_id}'p'`
        fi
        echo "*****  result of \"${run}\" *****"
        ls $dest_dir/$run/csvs/vclient/*.csv 2>tmp.log | grep -v loadline | while read file;do echo "*****  $file  *****";cat $file;echo "";done
        ls $dest_dir/$run/csvs/client/*.csv 2>>tmp.log | grep -v loadline | while read file;do echo "*****  $file  *****";cat $file;echo "";done
        ls $dest_dir/$run/csvs/ceph/*.csv 2>>tmp.log | grep -v loadline | while read file;do echo "*****  $file  *****";cat $file;echo "";done
        if [ ! -z "`grep 'No such file' tmp.log`" ]; then
            cd post-processing
            bash post_processing.sh $dest_dir/$run
            cd ..
        fi
        rm tmp.log
        ;;
    *)
        echo unrecognized option \'$1\'
        usage_exit
        ;;
esac
