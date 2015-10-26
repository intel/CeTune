####CeTune: A Ceph Profiling and Tuning Framework

######Functionality Description
- CeTune is a toolkit/framework to deploy, benchmark, profile and tune *Ceph cluster performance. 
- Aim to speed up the procedure of benchmarking *Ceph performance, and provide clear data charts of system metrics, latency breakdown data for users to analyze *Ceph performance.
- CeTune provides test performance through three interfaces: block, file system and object to evaluate *Ceph.

######Maintainance
- CeTune is an opensource project, under LGPL V2.1, Drived by INTEL BDT CSE team.
- Maillist: https://github.com/01org/CeTune
- Subscribe maillist: https://lists.01.org/mailman/listinfo/cephperformance


######Quick Start
- Prepare:
  - one node as CeTune controller(AKA head), Other nodes as CeTune worker(AKA worker)
  - Head is able to autossh to all workers include himself, head has a 'hosts' file contains all workers info.
  - All nodes are able to connect to yum/apt-get repository and also being able to wget/curl from ceph.com
  - package pre-installation:
    - Install to head:
      - apt-get/yum install -y python-pip pdsh unzip expect sysstat curl openjdk-7-jre haproxy python-matplotlib python-numpy
      - pip install ceph-deploy pyyaml argparse
    - Install to workers
      - apt-get/yum install -y python-pip unzip sysstat curl openjdk-7-jre haproxy

- Configure:
  - conf/all.conf
    - This is a configuration file to describe cluster, benchmark
  - conf/tuner.yaml
    - This is a configuration file to tune ceph cluster, including pool configuration, ceph.conf, disk tuning, etc.
  - conf/cases.conf
  -   This is a configuration file to decide which test case to run.

- Executive workflow:
  - CeTune "Deploy ceph cluster" phase:
    - CeTune will check if ceph is installed, if no, install ceph firstly, config version in all.conf
    - CeTune will deploy ceph cluster according to cluster configuration in all.conf
    - CeTune will apply tuning in tuner.yaml to ceph cluster, waiting ceph to be healthy
    - How to kick off CeTune deploy
    ```
    config tuner.yaml workstages as "deploy" only
    cd tuner; python tuner.py
    ```
 - CeTune "Benchmark ceph cluster" phase:
     - CeTune will compare current ceph tuning with tuner.yaml, if tuner.yaml contains some ceph configuartion not applyed to ceph cluster yet, CeTune will re-generate ceph.conf and restart ceph cluster.
     - Run benchmark lists in cases.conf, currently CeTune supported qemufio, rbdfio and cosbench.
     - Start analyze results after done benchmarking, generating html after analyzer.
     - How to kick off CeTune Benchmark
     ```
     generate test case from all.conf, and edit cases.conf manually to remove the test case if unnecessary.
     config tuner.yaml workstages as "benchmark" only
     cd tuner; python tuner.py
     ```
- User Guidance:
  - [CeTune Documents Download Url](https://github.com/01org/CeTune/blob/master/CeTune%20Document.pdf)

- Examples:
  ```
  root@client01:/root#  cd /root/cetune/tuner
  root@client01:/root/cetune/tuner# python tuner.py
  [LOG]Check ceph version, reinstall ceph if necessary
  [LOG]start to redeploy ceph
  [LOG]ceph.conf file generated
  [LOG]Shutting down mon daemon
  [LOG]Shutting down osd daemon
  [LOG]Clean mon dir
  [LOG]Started to mkfs.xfs on osd devices
  [LOG]mkfs.xfs for /dev/sda1 on aceph01
  … …
  [LOG]mkfs.xfs for /dev/sdf1 on aceph04
  [LOG]Build osd.0 daemon on aceph01
  … …
  [LOG]Build osd.39 daemon on aceph01
  [LOG]delete ceph pool rbd
  [LOG]delete ceph pool data
  [LOG]delete ceph pool metadata
  [LOG]create ceph pool rbd, pg_num is 8192
  [LOG]set ceph pool rbd size to 2
  [WARNING]Applied tuning, waiting ceph to be healthy
  [WARNING]Applied tuning, waiting ceph to be healthy
  … …
  [LOG]Tuning has been applied to ceph cluster, ceph is healthy now 
  RUNID: 36, Result dir: //mnt/data/36-80-seqwrite-4k-100-300-vdb
  [LOG]Prerun_check: check if rbd volumes are initialized
  [WARNING]Ceph cluster used data: 0.00KB, planed data: 3276800MB
  [WARNING]rbd volume initialization not done
  [LOG]80 RBD Images created
  [LOG]create rbd volume vm attaching xml
  [LOG]Distribute vdbs xml
  [LOG]Attach rbd image to vclient1
  … …
  [LOG]Start to initialize rbd volumes
  [LOG]FIO Jobs started on [‘vclient01’,’vclient02’, …. ‘vclient80’]
  [WARN]160 fio job still running
  … …
  [LOG]RBD initialization complete
  [LOG]Prerun_check: check if fio installed in vclient
  [LOG]Prerun_check: check if rbd volume attached
  [LOG]Prerun_check: check if sysstat installed
  [LOG]Prepare_run: distribute fio.conf to vclient
  [LOG]Benchmark start
  [LOG]FIO Jobs started on [‘vclient01’,’vclient02’, …. ‘vclient80’]
  [WARN]160 fio job still running
  … …
  [LOG]stop monitoring, and workload
  [LOG]collecting data
  [LOG]processing data
  [LOG]creating html report
  [LOG]scp to result backup server
  ```
  - Result dir
  ```
  - 278-140-qemurbd-seqwrite-64k-qd64-40g-100-400-vdb.html
  - conf
    - all.conf
	  - tuner.yaml
	  - cetune_proces.log
  - raw
    - aceph01
    - aceph02
    - ...
  ```
  - Result HTML pages
  ![CeTune HTML](https://github.com/01org/CeTune/blob/master/examples/CeTune.png)
