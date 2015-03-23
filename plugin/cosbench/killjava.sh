killall java
for ((i=1;i<=2;i++)) 
do
ssh c$i "killall java"
done
