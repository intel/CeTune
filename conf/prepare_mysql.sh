#!/bin/bash


#echo "127.0.0.1       `hostname`" >> /etc/hosts

mount_dir=/root/test
install_dir=${mount_dir}/mysql/
default_dir=/var/lib/mysql/
filename=/etc/mysql/my.cnf

size=2G
disk=/dev/vdb

function remove_log_data {
	local dir=$1
	rm -f ${dir}/ib_logfile*
	rm -f ${dir}/ibdata*
}

function start_mysql_timeout {
	local wait_time=150
	timeout $wait_time service mysql start
	if [ $? -ne 0 ]; then
		return 1
	else
		return 0
	fi
}

function stop_mysql_with_retry {
    local cnt=0
    while [ $cnt -lt 10 ]; do
	service mysql stop
	killall -KILL mysql mysqld_safe mysqld
	service mysql status | grep "stop/waiting"
	if [ $? -eq 0 ]; then
		return;
	fi
	let cnt++
	sleep 1
    done
    echo "Can't stop MySQL, exit!"
    exit 1
}

loop_cnt=0
max_retry=5

while [ $loop_cnt -lt $max_retry ]; do
	fdisk -l | grep vdb
	if [ $? -ne 0 ]; then
	    echo "vdb not found! exit!"
	    exit 1
	else
	    (echo o; echo w) | fdisk /dev/vdb
	fi

	fdisk -l | grep vda2
	if [ $? -ne 0 ]; then
	    echo "vda2 not found! exit!"
	    exit 1
	fi

	mkfs.ext4 /dev/vda2
	mkdir -p $mount_dir
	mount /dev/vda2 $mount_dir
	mkdir -p $install_dir
	chmod -R 777 $install_dir

	stop_mysql_with_retry
	remove_log_data $default_dir
	remove_log_data $install_dir

	cd /etc/apparmor.d/
	mv usr.sbin.mysqld disable/
	service apparmor reload
	cd /root/

	sed -i '/^innodb_data_file_path/d' $filename
	sed -i '/^innodb_data_home_dir/d' $filename
	sed -i '/^user.*/d' $filename
	sed -i '/^datadir.*/d' $filename
	sed -i "/\[mysqld\]/a user=root" $filename
	mysql_install_db --user=root --datadir=$install_dir

	remove_log_data $default_dir

	sed -i "/\[mysqld\]/a datadir="$install_dir"" $filename

	start_mysql_timeout
	if [ $? -ne 0 ]; then
		echo "[$loop_cnt]: Restart at install mysql to $install_dir!"
		let loop_cnt++
		continue
	fi

	sleep 2

	stop_mysql_with_retry
	remove_log_data $install_dir

	sed -i "/\[mysqld\]/a innodb_data_file_path="$disk:$size"newraw" $filename
	sed -i "/\[mysqld\]/a innodb_data_home_dir=" $filename
	start_mysql_timeout
	if [ $? -ne 0 ]; then
		echo "[$loop_cnt]: Restart at newraw!"
		let loop_cnt++
		continue
	fi
	sleep 2
	stop_mysql_with_retry

	sed -i '/^innodb_data_file_path/d' $filename
	sed -i "/^innodb_data_home_dir/a innodb_data_file_path="$disk:$size"raw" $filename
	start_mysql_timeout
	if [ $? -ne 0 ]; then
		echo "[$loop_cnt]: Restart at raw!"
		let loop_cnt++
		continue
	fi

	sleep 2

	echo "create database sbtest; CREATE USER 'sbtest'@'localhost'; GRANT ALL PRIVILEGES ON * . * TO 'sbtest'@'localhost'; FLUSH PRIVILEGES;" | mysql -u root -p123456
	if [ $? -ne 0 ]; then
		echo "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('123456');" | mysql -uroot
		echo "create database sbtest; CREATE USER 'sbtest'@'localhost'; GRANT ALL PRIVILEGES ON * . * TO 'sbtest'@'localhost'; FLUSH PRIVILEGES;" | mysql -u root -p123456
	fi

	echo -e "\033[32m[$loop_cnt]: Success!\033[0m"	
	exit 0;
done

exit 1
