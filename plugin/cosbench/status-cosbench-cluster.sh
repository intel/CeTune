echo "CONTROL NODE"
ps aux | grep eclipse | grep java
for node in `cat client.lst`
do  
    echo "CLIENT NODE: $node"  
    ssh root@$node "ps aux | grep eclipse" | grep java
done
