#!/bin/bash
if [ -f "all.conf" ]; then
    conf="all.conf"
elif [ -f "conf/all.conf" ]; then
    conf="conf/all.conf"
elif [ -f "../conf/all.conf" ]; then
    conf="../conf/all.conf"
elif [ -f "../../conf/all.conf" ]; then
    conf="../../conf/all.conf"
fi
function error_check {
    if [ "$?" != "0" ]; then
        exit
    fi 
}

function os_disk_check {
    host=$1
    disk=$2
    os_disk=`ssh $host mount -l | grep boot |head -1| awk '{print $1}' | sed 's/[0-9]//g'`
    if [ ! -z "`echo $disk | grep $os_disk`" ]; then
        echo true
    else
        echo false
    fi
}

function get_conf {
    if [ ! -z $1 ]; then
        conf=$1
    fi 
    line_num=`awk 'BEGIN{line_num = 0}{if(!line_num && $0=="[ceph_conf]")line_num = NR-1}END{if(!line_num)line_num=NR; print line_num}' $conf`
    head -$line_num $conf > all.conf.tmp
    source all.conf.tmp
    rm all.conf.tmp
}

function print_user_ceph_conf {
    awk 'BEGIN{p=0}{if(p==1){print $0};if($0=="[ceph_conf]")p=1;}' $conf
}

function copy_to_conf {
    conf=$1
    type=$2
    #when ceph-deploy deploy mon, if we set the cluster_network which is not the same nic with mon_host, we will fail in getting keyring
    if [ "$type" == "mon" ]; then
        print_user_ceph_conf | grep -v network | while read line
        do
            res=`grep "$line" ceph.conf`
            if [ -z "$res" ]; then
                echo $line >> ../deploy/ceph.conf
            fi
        done
    else

        print_user_ceph_conf | while read line
        do
	    res=`grep "$line" ceph.conf`
            if [ -z "$res" ]; then
                echo $line >> ../deploy/ceph.conf
	    fi
        done
    fi
}

function get_host_ip {
    host=$1
    search_kw=$2
    if [ ! -z $search_kw ]; then
        grep $host /etc/hosts | grep $search_kw | head -1 | awk '{print $1}'    
    else
        grep $host /etc/hosts | head -1 | awk '{print $1}'    
    fi
}

function get_subnet {
    net=$1
    case `echo $net | awk -F/ '{print $2}'` in
        24)
        search_kw=`echo $net | awk -F/ '{print $1}' | sed 's/\.[0-9]*$//'`
        ;;
        16)
        search_kw=`echo $net | awk -F/ '{print $1}' | sed 's/\.[0-9]*\.[0-9]*$//'`
        ;;
        *)
        search_kw=$net
        ;;
    esac
    echo $search_kw
}

function uuid_to_fstab {
    host=$1
    ssh $host "sed '/\/var\/lib\/ceph\/osd\/ceph/d' /etc/fstab" > fstab_tmp
    echo > tmp
    ssh $host blkid | while read line
    do
        dev=`echo $line | awk '{print $1}' | sed 's/://' | awk -F/ '{print $3}'`
        echo $dev" "`echo $line |awk '{print $2}'` >> tmp
    done
    ssh $host mount -l | grep osd | while read line
    do
        dev=`echo $line | awk '{print $1}' | awk -F/ '{print $3}'`
        fstype=`echo $line | awk '{print $5}'`
        echo -e `grep $dev tmp | awk '{print $2}'`"\t"`echo $line | awk '{print $3}'`"\t"$fstype"\tdefaults\t0\t0" >> fstab_tmp
    done
    rm tmp
    sed -i 's/"//g' fstab_tmp
    scp -q fstab_tmp $host://etc/fstab
    rm fstab_tmp
}

function rm_uuid_from_fstab {
    host=$1
    ssh $host "sed -i '/\/var\/lib\/ceph\/osd\/ceph/d' /etc/fstab"
}

function interact {
    read input    
        case "$input" in
            "yes" )
                echo true
                ;;
            "no" )
                echo false
                ;;
            *) echo false;;
        esac
}

function check_fio_rbd {
    res=`fio --enghelp | grep rbd`
    if [ -z "$res" ]; then
        echo "false"
        exit
    else
        echo "true"
    fi
}

function check_post_processing {
    `python -c "import xlsxwriter"`
    res=$?
    if [ $res != "0" ]; then
        echo "[WARN]Python doesn't installed the module 'xlsxwriter', pls install firstly"
        exit
    fi
}

function mytest {
    echo "$1 $2 $3"
}
#uuid_to_fstab KVSceph01
#uuid_to_fstab KVSceph02
#os_disk_check client01 /dev/sdb
if [ '$#' != '0' ]; then
     `echo $@` 2>/dev/null
fi
