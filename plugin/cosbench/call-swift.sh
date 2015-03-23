#!/bin/bash

ssh gw2 "swift -A http://10.4.9.105/auth/v1.0 -U cosbench:operator -K intel2012 $1 $2 $3 $4"

#echo "-- osd1 --"
#swift -A http://10.10.10.1/auth -U cosbench:operator -K intel2012 $1 $2 $3 $4

#echo "-- osd2 --"
#swift -A http://10.10.10.2/auth -U cosbench:operator -K intel2012 $1 $2 $3 $4

#echo "-- osd3 --"
#swift -A http://10.10.10.3/auth -U cosbench:operator -K intel2012 $1 $2 $3 $4

#echo "-- osd4 --"
#swift -A http://10.10.10.4/auth -U cosbench:operator -K intel2012 $1 $2 $3 $4

#echo "-- osd5 --"
#swift -A http://10.10.10.5/auth -U cosbench:operator -K intel2012 $1 $2 $3 $4
