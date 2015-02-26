#!/bin/bash

if [ "$#" != "1" ]; then
    echo "$0 {path_to_lttng-traces/auto*****}"
    exit
fi
path_to_lttng=$1"/ust/pid/"
lttng_res_dir=$1"/result/"

mkdir -p ${lttng_res_dir}

for file_dir in `ls $path_to_lttng`
do
    python3 parser.py ${path_to_lttng}/${file_dir}/ > ${lttng_res_dir}/${file_dir}_lttng.csv &
done
