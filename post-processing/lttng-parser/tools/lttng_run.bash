#!/bin/bash

session=`lttng list | grep "1)" | awk '{print $2}'`
lttng destroy $session

lttng create
lttng enable-channel channel0 -u --buffers-pid --subbuf-size 16384

lttng enable-event -u -c channel0 --tracepoint osd:ceph_msg_osd_op
lttng enable-event -u -c channel0 --tracepoint osd:msg_osd_subop
lttng enable-event -u -c channel0 --tracepoint osd:msg_osd_subop_reply
lttng enable-event -u -c channel0 --tracepoint osd:execute_ctx
lttng enable-event -u -c channel0 --tracepoint osd:eval_repop
lttng enable-event -u -c channel0 --tracepoint osd:op_applied
lttng enable-event -u -c channel0 --tracepoint osd:op_commit
lttng enable-event -u -c channel0 --tracepoint osd:repop_all_applied
lttng enable-event -u -c channel0 --tracepoint osd:repop_all_committed
#lttng enable-event -u -c channel0 --tracepoint mutex:lock
lttng enable-event -u -c channel0 --tracepoint osd:ms_fast_dispatch
lttng enable-event -u -c channel0 --tracepoint pg:queue_op
lttng enable-event -u -c channel0 --tracepoint keyvaluestore:queue_op_start
lttng enable-event -u -c channel0 --tracepoint osd:opwq_process_start
lttng enable-event -u -c channel0 --tracepoint osd:opwq_process_finish
lttng enable-event -u -c channel0 --tracepoint keyvaluestore:opwq_process_start
lttng enable-event -u -c channel0 --tracepoint keyvaluestore:opwq_process_finish
lttng enable-event -u -c channel0 --tracepoint keyvaluestore:do_transaction_start
lttng enable-event -u -c channel0 --tracepoint keyvaluestore:do_transaction_finish
lttng enable-event -u -c channel0 --tracepoint osd:log_op_stats
lttng enable-event -u -c channel0 --tracepoint osd:log_subop_stats
lttng enable-event -u -c channel0 --tracepoint keyvaluestore:finish_op
lttng add-context -u -t pthread_id 
lttng add-context -u -t vpid

lttng start
