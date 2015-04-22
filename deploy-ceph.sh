#!/bin/bash

function usage_exit {
    echo -e "usage:\n\t $0 {-h|{install|deploy|purge|remove-deploy|gen-cephconf} [mon|osd|mds]."
    exit
}

function help_guide {
    cat .help_guide
}

case $1 in
    -h | --help)
        help_guide
        echo ""
        usage_exit
        ;;
    install)
        cd deploy
        bash ceph-deploy-ceph.sh
        ;;
    redeploy)
        cd deploy
        python deploy.py redeploy
        cd ..
        ;;
    deploy)
        if [ "$#" -ne 5 ];then
            echo -e "bash $0 $1 --engine cbt/ceph-deploy/mkcephfs --type all/mon/osd"
            exit 1
        fi
        shift 1
        while [ "$#" -gt 0 ]
        do
            case $1 in
                '--engine')
                    lengine=$2
                    shift 2
                    ;;
                '--type')
                    ltype=$2
                    shift 2
                    ;;
                *)
                    echo "Unrecognized option '$1'"
                    exit 1
                    ;;
            esac
        done
        if [ "$lengine" = "cbt" ] || [ "$lengine" = "CBT" ]; then
            if [ "$ltype" != "all" ]; then
                echo "Only support deploy mon and osd at same time now, please enter: "
                echo `get_conf`" bash $0 $1 --engine cbt --type all"
                exit 1
            fi
            cd deploy
            bash gen_ceph_conf.sh
            mv ceph.conf.new ../plugin/ceph.conf
            cd ../plugin
            python plugin.py --engine cbt deploy
            cd ..
        elif [ "$lengine" = "ceph-deploy" ]; then
            case $ltype in
                mon)
                    cd deploy
                    bash ceph-deploy-mon.sh
                    cd ..
                ;;
                osd)
                    cd deploy
                    bash ceph-deploy-osd.sh
                    cd ..
                ;;
                add-more-osd)
                    cd deploy
                    bash ceph-deploy-osd.sh -a
                    cd ..
                ;;
                mds)
                    cd deploy
                    bash ceph-deploy-mds.sh
                    cd ..
                ;;
                all)
                    cd deploy
                    echo "=======start to deploy MON=========="
                    bash ceph-deploy-mon.sh
                    echo "=======Finished deploying MON=========="
                    echo "=======start to deploy OSD=========="
                    bash ceph-deploy-osd.sh
                    echo "=======Finished deploying OSD=========="
                    cd ..
                ;;
                *)
                    echo "Please choose type, we currently provides 5 options:  mon/osd/mds/all/add-more-osd"
                    exit
                ;;
            esac
        elif [ "$lengine" = "mkcephfs" ]; then
            case $ltype in
                all)
                    cd deploy
                    bash gen_ceph_conf.sh
                    echo "Please check the new ceph.conf, do you want to continue deploy ceph?"
                    if [ "`interact`" = "true" ]; then   
                        cp ceph.conf.new /etc/ceph/ceph.conf
                        mkcephfs -a -c ceph.conf --mkfs
                    else
                        exit
                    fi
                    cd ..
                ;;
                force)
                    cd deploy
                    bash gen_ceph_conf.sh
                    cp ceph.conf.new /etc/ceph/ceph.conf
                    mkcephfs -a -c ceph.conf --mkfs
                    cd ..
            esac
        else
            echo "please choose engine, we currently provides 3 options: cbt, ceph-deploy, mkcephfs"
        fi
        ;;
    purge)
        cd deploy
        bash ceph-deploy-purge.sh
        cd ..
    ;;
    remove-deploy)
        cd deploy
        case $2 in
            mon)
                bash remove_osd.sh mon
            ;;
            osd)
                bash remove_osd.sh osd
            ;;
            mds)
                bash remove_osd.sh mds
            ;;
            all)
                bash remove_osd.sh all
            ;;
            *)
                echo "You can only remove mon/osd/mds/all"
            exit
            ;;
        esac
        cd ..
    ;;
    gen-cephconf)
        cd deploy
        bash gen_ceph_conf.sh
        cd ..
    ;;
    *)
        echo unrecognized option \'$1\'
        usage_exit
    ;;
esac

