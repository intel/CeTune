#!/bin/bash

for node in `cat sn.lst`
do
  echo "clean node .. $node"
  ssh root@$node "cd /etc/swift; sh cleanalldata.sh"
  echo $node cleaned
done

