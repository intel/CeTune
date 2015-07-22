###CeTune: A Ceph Profiling and Tuning Framework

#####We will maintain a performance profiling and tuning framework named "CeTune". CeTune comprises five function components:
> (1)Deployment, support installing ceph from binary pkg and source codes, and deploying ceph using ceph-deploy or mkcephfs

> (2)Workload generator, generates well defined use cases and automatically evaluate the RBD, object, and CephFS performance with various pluggable workloads
>> a.    Leverage CBT do the fio rbd test, rados bench test.

>> b.    Integrate cosbench as the object(rgw) workload generator.

>> c.    Integrate fio cephfs engine and other filesystem benchmark as CephFS workload generator.

> (3) Analyzer, monitors the performance and reveal the bottleneck
>> a.    Leverage blkin (LTTng + Zipkin) patch to do the ceph latency breakdown.

>> b.    Integrate vtune to show the CPU profiling data.

> (4) The Tuner, dynamically injects args and compares the performance to identify best tuning knobs.

> (5) the Visualizer, automatically presents the data w/ a web GUI.
>> a.    using CeTune in daily work to evaluate the major Ceph release performance, data will be shown on a [public portal](https://01.org/cephperf) for users/developer reference.

#####Any question please contact
Jian Zhang <jian.zhang@intel.com>
Chendi Xue <chendi.xue@intel.com> 
