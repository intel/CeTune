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
    deploy)
	    case $2 in
	        mon)
	            cd deploy
		    bash ceph-deploy-mon.sh
		    cd ..
		;;
		osd)
		    cd deploy
                    if [ $3 == '-a' ];then
                        bash ceph-deploy-osd.sh -a
                    else
                        bash ceph-deploy-osd.sh
                    fi
		    bash ceph-deploy-osd.sh
                    cd ..
                ;;
		mds)
                    cd deploy
		    bash ceph-deploy-mds.sh
		    cd ..
		;;
		*)
                    echo "You can only deploy mon/osd/mds"
		    exit
                ;;
            esac
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

