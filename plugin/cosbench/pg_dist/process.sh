#!/bin/bash

for dir in `ls|grep id64`
do
	awk '{print $2}' $dir/*hashps* > $dir/raw.log
done
