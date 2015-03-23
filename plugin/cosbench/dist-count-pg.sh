#!/bin/bash

for node in `cat osd.lst`
do
  scp count-pg.sh $node:~/
done
