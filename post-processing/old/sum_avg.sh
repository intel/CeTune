#!/bin/bash

function usage {
	echo "$0 used to calc sum and avg "
}

if [[ $# != 1 && $# != 2 ]]
then
	usage
	exit 1
fi

infile=$1
skipzero=1
if [[ $2 ]]
then
	skipzero=$2
fi

items=`head -n1 $infile | wc | awk '{print $2}'`
lines=`wc $infile | awk '{print $1}'`
declare -a sum
declare -a avg
declare -a num

(( end_index=$items - 2 ))
for i in `seq 0 $end_index`
do
	sum[$i]=0
	avg[$i]=0
	num[$i]=0
done

for index in `seq 2 $items`
do
	(( i=$index-2 ))
	for line in  `seq 2 $lines` 
	do
		data=`sed -n ''$line'p' $infile | awk '{print $'$index'}'`
		etoosmall=`echo $data | grep -cE "e"`
		if [[ $etoosmall != 0 ]]
		then
			data=0
		fi
		if [[ ! $data ]]
		then
			data=0
		fi
		if [[ $skipzero==1 && $data == 0 ]]
		then
			continue
		fi
		(( num[$i]=${num[$i]} + 1 ))
		sum[$i]=`echo "scale=9;${sum[$i]}+$data" | bc`
	done
done

for i in `seq 0 $end_index`
do
	if [[ ${num[$i]} == 0 ]]
	then
		avg[$i]=0
		continue
	fi
	avg[$i]=`echo "scale=9;${sum[$i]}/${num[$i]}" | bc`
done

sed -i "2i\ sum    ${sum[*]}" $infile
sed -i "3i\ avg    ${avg[*]}" $infile
