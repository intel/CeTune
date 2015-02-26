import common
import babeltrace
import sys
import json

#============================ main function =============================#
latency_event_list=['mutex:lock_PG__lock:latency','mutex:lock_OSDService_tid_lock:latency','mutex:lock_OSDService_peer_map_epoch_lock:latency','keyvaluestore:opwq_process_start:get_lock_latency','keyvaluestore:queue_op_finish:queue_len','keyvaluestore:finish_op:latency','mutex:lock_Finisher_finisher_lock:latency','osd:log_op_stats:latency','osd:log_op_stats:process_latency','osd:log_subop_stats:latency']

if( len(sys.argv)==2 and sys.argv[1] == 'get_result'):
    sync = common.SyncController()
    sync.get_tracepoint_dict()

elif( len(sys.argv)==2):
    traces = babeltrace.TraceCollection()
    lttng_input = sys.argv[1]
    ret = traces.add_trace( lttng_input, "ctf" )
    
    #========= using checkpoint list to cal the checkpoint interval =======#
    chk_inter = common.CheckpointIntervalCal()
    chk_inter.parse_trace_to_dict( traces.events )
    #chk_inter.request_result_to_file( )
    
    #========= using latency_event_list to get latency =======#
    #lat_cal=common.LatencyCal()
    #lat_cal.parse_trace_to_dict( traces.events, latency_event_list )
    #common.print_pid_dict( lat_cal.pid_dict )
    
    #========= using event_name and pthread_id to get thread interval =======#
    #thread_inter_cal=common.ThreadInterval()
    #thread_inter_cal.parse_trace_to_dict( traces.events, "" )
    #common.print_pid_dict( thread_inter_cal.pid_dict )
