import sys
import re
import json
import numpy
import RWLock
import csv
import socket
from copy import copy
from collections import OrderedDict
from datetime import datetime

def is_empty( dictionary ):
    return not bool(dictionary)

def cal_avg_without_zero( data_list ):
    res_sum=0
    count=0
    for value in data_list:
        if( value != 0):
            res_sum+=value
            count+=1
    if( count == 0 ):
        res = 0
    else:
        res=res_sum/count
    return res

def print_pid_dict( pid_output_dict ):
    for pid in pid_output_dict:
        print("========="+str(pid)+"============")
        output_dict=pid_output_dict[pid]['data_dict']
        for key in output_dict:
            output=""
            for data in output_dict[key]:
                output += ','+str(data)
            avg_output=numpy.mean(output_dict[key])
            #avg_output=cal_avg_without_zero(output_dict[key])
            #print(key+","+str(avg_output))
            print(key+","+str(avg_output)+output)
            #print(key+","+output)

class Config:
    def __init__(self):
        filename = 'config/run.conf'
        data = self.load_json_from_file( filename )
        self.log_output = data['log_output']
        self.result_output = data['result_output']
        self.tracepoint_list = data['tracepoint_list']
    
    def load_json_from_file(self, filename ):
        with open(filename,'r') as infile:
            json_data = infile.read()
        data = json.loads(json_data)
        return data

class SyncController:
    def save_record( self, record ):
        with open('one_round_record.txt','a') as file:
            file.write( json.dumps(record) )
            file.write( '\n' )
    def record_send_to_merge_socket( self, record ):
        data = json.dumps( {'op_type':'record_update','data':record} )
        self.sync_request( data )
    
    def get_tracepoint_dict( self ):
        data = json.dumps( {'op_type':'tracepoint_request'} )
        self.sync_request(data)
    
    def sync_request( self, send_data ):
        HOST, PORT = "localhost", 8888
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            sock.connect((HOST, PORT))
            sock.sendall(send_data.encode('utf-8'))
            res = sock.recv(1024)
            return res
         
        finally:
            sock.close()

class Calculator:
    """
        This is the base class.
    """
    pid_dict={} 
    typename_dict={}
    typename_count=0
    first_event={}
    last_event={}
    reqid_dict={}
    record_id_map = {}
    sync = SyncController()
    config = Config()
    
    def parse_typename_list(self, typename_list):
#    """
#        Parse the tracepoint list into dict, contains below scenario
#        typename_list = {
#            'primary':[
#                'osd:ms_fast_dispatch',
#                'keyvaluestore:queue_op_finish:queue_len',
#                'keyvaluestore:do_transaction_start:op_type=10',
#                'keyvaluestore:do_transaction_start:op_type=14',
#                'osd:log_op_stats:latency'
#            ]
#        }
#        ->
#        typename_dict = {
#            'osd:ms_fast_dispatch':{
#                'type':'primary',
#                'tracepoint':{
#                    'osd:ms_fast_dispatch':{}
#                }
#            },
#            'keyvaluestore:queue_op_finish':{
#                'type':'primary',
#                'tracepoint':{
#                    'keyvaluestore:queue_op_finish:queue_len':{'queue_len'=''}
#                }
#            },
#            'keyvaluestore:do_transaction_start':{
#                'type':'primary',
#                'tracepoint':{
#                    'keyvaluestore:do_transaction_start:op_type=10':{'op_type':10},
#                    'keyvaluestore:do_transaction_start:op_type=14':{'op_type':14}
#                }
#            },
#            'osd:log_op_stats':{
#                'type':'primary',
#                'tracepoint':{
#                    'osd:log_op_stats:latency':{'latency'=''}
#                }
#            }
#        }
#        First level key is the event name.
#    """
        if( typename_list == "" ):
            return
        for tracepoint_type, tracepoint_list in typename_list.items():
            self.first_event[tracepoint_type] = {'event_name':tracepoint_list[0], 'count':0}
            self.last_event[tracepoint_type] = {'event_name':tracepoint_list[-1], 'count':0}
            #last_event may occured not once in one io, like primary osd:opwq_process_finish, so we need to also set a counter here
            for key in tracepoint_list:
                self.typename_count+=1
                m = re.match(r'(\w+:\w+):*(\w*=*\w*)', key )
                if( key == self.last_event[tracepoint_type]['event_name'] ):
                    self.last_event[tracepoint_type]['count'] += 1
                if(m.group(1) not in self.typename_dict):
                    self.typename_dict[m.group(1)]={'type':tracepoint_type, 'tracepoint':{key: self.parse_param(m.group(2))}}
                else:
                    if( self.typename_dict[m.group(1)]['type'] == tracepoint_type ):
                        self.typename_dict[m.group(1)]['tracepoint'][key]= self.parse_param(m.group(2))
                    else:
                        self.typename_dict[m.group(1)]['type'] = 'unknown'
                        self.typename_dict[m.group(1)]['tracepoint'][key]= self.parse_param(m.group(2))
    
    def parse_param( self, param ):
        m = re.match(r'(\w+)=(\w+)', param )
        try:
            if(m.group(1) and m.group(2)):
                return {m.group(1):int(m.group(2))}
        except:
            return {}

    def get_reqid( self, event ):
        if( 'num' in event and 'tid' in event ):
            reqid=str(event['num'])+str(event['tid'])
            self.reqid_dict[event['pthread_id']]=reqid
        else:
            if( event['pthread_id'] in self.reqid_dict ):
                reqid=self.reqid_dict[event['pthread_id']]
            else:
                reqid=""
        return reqid

    def del_from_reqid( self, reqid ):
        rm_list=[]
        for key,value in self.reqid_dict.items():
            if( reqid == value ):
                rm_list.append(key)
        for key in rm_list:        
            del self.reqid_dict[ key ]

    def get_eventname(self, event):
        try:
            extra=re.sub(':{2}','_',event['extra_eventname']);
            event_name=event.name+"_"+extra
        except:
            event_name=event.name
        return event_name
    
    def is_last_event( self, event_name, event_type, record_data ):
        for tracepoint_type, last_event in self.last_event.items():
            #print("[is_last_event]"+event_name+"  "+last_event['event_name'])
            if( event_type == tracepoint_type and event_name == last_event['event_name'] ):
                cur_event_count = 0
                for timestamp, cur_event_name in record_data.items():
                    if( cur_event_name == last_event['event_name'] ):
                        cur_event_count += 1
                if( cur_event_count == last_event['count'] ):
                    return True
        return False
    
    def is_first_event( self, event_name, event_type, record_data ):
        for tracepoint_type, first_event in self.first_event.items():
            if( (event_type == tracepoint_type or event_type=="unknown") and event_name == first_event['event_name'] ):
                if( first_event['count'] == 1 ):
                    return True
                else:
                    cur_event_count = 0
                    for timestamp, cur_event_name in record_data.items():
                        if( cur_event_name == first_event['event_name'] ):
                            cur_event_count += 1
                    if( cur_event_count == 0 ):
                        return True
        
        return False

class CheckpointIntervalCal(Calculator):
    def request_result_to_file( self ):
        self.sync.get_tracepoint_dict()
    
    def parse_trace_to_dict( self, trace_dict ):
        """
            This is base function to parse lttng trace result into a result dict looks like below
            pid_dict = {
                pid : {
                    eventname : [timestamp / value]
                    *example*
                    'osd:ms_fast_dispatch-pg:queue_op':[ 31949, 40129, 35267, ... ],
                    'osd:opwq_process_start-keyvaluestore:queue_op_finish':[ 1568794, 1767986, 1465762, ...],
                    ... 
                }
            }
            In our design, to get the interval of two tracepoint, using two step to complete.
            step 1: record matched tracepoint into the 'one_round_record[repid]' dict
            step 2: when we record all tracepoint of one IO, calculate the interval and insert to pid_dict.
            *tips:
            In order to link the IO in client and server( different id_tag, client uses oid_offset, server uses num_tid, and different timestamp gap ), client , primary write , replica write will be record in diffrent one_round_record, than linked before step 2.
        """
        typename_list = self.config.tracepoint_list
        self.parse_typename_list( typename_list )
        for event in trace_dict:
            pid=event['vpid']
            self.pid_dict_update( pid )
            
            one_round_record=self.pid_dict[pid]['one_round_record']
            typename_dict=self.typename_dict       
            event_name=self.get_eventname(event)
     
            if( event_name not in self.typename_dict ):
                continue
            
            #Will return True will one_round_record complete, we can send to merge
            completed_one_round_record = self.one_round_record_update( event, one_round_record )
            
            if( not is_empty(completed_one_round_record) ):
                #self.sync.save_record( completed_one_round_record )
                self.sync.record_send_to_merge_socket( completed_one_round_record )
        return

    def pid_dict_update( self, pid ):
        if(pid not in self.pid_dict):
            self.pid_dict[pid]={'one_round_record':{}}

    def del_reqid_from_record_id_map( self, record_id ):
        for record_id_type, record_id_map_value in self.record_id_map.items():
            rm_list=[]
            for key, value in record_id_map_value.items(): 
                if( record_id['record_id'] == value ):
                    rm_list.append(key)
            for key in rm_list:        
                del record_id_map_value[ key ]
    
    def get_record_id( self, event ):
        """
            This function will return the record_id and record_id_type
            At osd level, event can be identified by num + tid, aka reqid
            At Filestore/KeyValueStore/client level, event is identified by oid + offset, aka oidoff
            At message level, event is identified by rep_tid, aka rep_tid
            Other event, use threadid to identify
            So we need to identify the event/record id type here, and update the map.
        """
        record_id = {}
        if( 'oid' in event and 'off' in event and 'len' in event ):
            record_id['type'] = 'oidoff'
            record_id['record_id']=str(event['oid'])+str(event['off'])+str(event['tid'])
        
        if( is_empty(record_id) ):
            record_id['type'] = 'pthread_id'
            record_id['record_id'] = event['pthread_id']
        
        if( 'num' in event and 'tid' in event and not ( event['num']==0 and event['tid'] == 0 ) ):
            reqid = str(event['num'])+str(event['tid'])
            if( not is_empty(record_id) ):
                if( record_id['type'] not in self.record_id_map ):
                    self.record_id_map[record_id['type']] = {}
                
                record_type_before = record_id['type']
                record_id_before = record_id['record_id']
                record_id['type']='reqid'
                record_id['record_id']=reqid
                
#                if( record_id_before in self.record_id_map[record_type_before] ):
#                    if( self.record_id_map[record_type_before][record_id_before] != "00" and reqid == "00" ):
#                        record_id['record_id']=self.record_id_map[record_type_before][record_id_before]
#                        record_id['type']='reqid'
#                    if( self.record_id_map[record_type_before][record_id_before] == "00" and reqid != "00" ):
#                        record_id['record_id_tmp']="00"
                if( 'record_id_tmp' not in record_id ):
                    record_id['record_id_tmp']=record_id_before
                self.record_id_map[record_type_before][record_id_before] = reqid
        else:
            if( record_id['record_id'] in self.record_id_map[record_id['type']] ):
                record_id['record_id']=self.record_id_map[record_id['type']][record_id['record_id']]
                record_id['type']='reqid'
        return record_id

    def is_conjunction_event( self, record_id ):
        """
            This function is to check if the event contains both reqid and threadid
        """
        if( 'record_id_tmp' in record_id ):
            return True
        else:
            return False

    def conjunct_record( self, dst_record_id, src_record_id, one_round_record ):
        if( src_record_id not in one_round_record ):
            return
        if( dst_record_id not in one_round_record ):
            one_round_record[dst_record_id]={}
        for tmp_event in one_round_record[ src_record_id ]['record_data'].keys():
            one_round_record[dst_record_id]['record_data'][tmp_event] = one_round_record[src_record_id]['record_data'][tmp_event]
        del one_round_record[src_record_id]
        
    def one_round_record_update( self, event, one_round_record ):
        """
            Put tracepoint into a reqid/oid identified one_round_record_dict
            tracepoint may belong to primary write io path or replica write io path, need to identify here
            one_round_record = { 'record_id', 'record_type', 'record_data' }
        """
        event_name=self.get_eventname(event)
        for key,value in self.typename_dict[event_name]['tracepoint'].items():
            if( not self.check_match_tracepoint( value, event ) ):
                continue
            else:
                record_id = self.get_record_id(event)
                
                if( record_id['record_id'] not in one_round_record or (self.is_first_event( key, one_round_record[record_id['record_id']]['record_type'], one_round_record[record_id['record_id']]['record_data'] )) ):
                    one_round_record[record_id['record_id']] = {'record_type':'unknown','record_data':{}}
                if( self.is_conjunction_event( record_id ) ):
                    #below action is to avoid if the previous thread is same with current thread, so the event will be added in this one_round_record
                    if( self.is_first_event( key, one_round_record[record_id['record_id']]['record_type'], one_round_record[record_id['record_id']]['record_data']) ):
                        if( record_id['record_id_tmp'] in one_round_record ):
                            del one_round_record[record_id['record_id_tmp']]
                    self.conjunct_record( record_id['record_id'], record_id['record_id_tmp'], one_round_record )
                    one_round_record[record_id['record_id']]['record_id'] = record_id['record_id']
                 
                reqid = record_id['record_id']
                
                #Need to identify the record_type here 
                if( self.typename_dict[event_name]['type'] != 'unknown' ):
                    one_round_record[reqid]['record_type'] = self.typename_dict[event_name]['type']
                #one_round_record[reqid]['record_data'][key] = event.timestamp
                one_round_record[reqid]['record_data'][event.timestamp] = key
                
                if( self.is_last_event( key, one_round_record[reqid]['record_type'], one_round_record[reqid]['record_data'] ) ):
                    self.del_reqid_from_record_id_map( record_id )
                    if( 'record_id' in one_round_record[reqid] ):
                        return one_round_record[reqid]
                    else:
                        del one_round_record[reqid]
                
                return {}

    def check_match_tracepoint( self, filters, event ):
        for key, value in filters.items():
            if( event[key] != value ):
                return False
        return True

class LatencyCal(Calculator):
    def parse_trace_to_dict( self, trace_dict ):
        typename_list = self.config.tracepoint_list
        self.parse_typename_list( typename_list )
        for event in trace_dict:
            pid=event['vpid']
            self.pid_dict_update( pid, typename_list  )
            
            data_dict=self.pid_dict[pid]['data_dict']
            typename_dict=self.typename_dict       
            event_name=self.get_eventname(event)
     
            if( event_name not in self.typename_dict and typename_list != ""):
                continue
            
            #record one round checkpoint into dict first
            for key,value in self.typename_dict[event_name].items():
                data_dict[key].append( event[value] )
        return self.pid_dict
    
    def pid_dict_update( self, pid, typename_list ):
        if(pid not in self.pid_dict):
            self.pid_dict[pid]={'data_dict':{},'one_round_record':{}}
            for key in typename_list:
                self.pid_dict[pid]['data_dict'][key]=[]

class ThreadInterval(Calculator):
    def parse_trace_to_dict( self, trace_dict ):
        typename_list = self.config.tracepoint_list
        self.parse_typename_list( typename_list )
        for event in trace_dict:
            pid=event['vpid']
            self.pid_dict_update( pid )
            
            data_dict=self.pid_dict[pid]['data_dict']
            one_round_record=self.pid_dict[pid]['one_round_record']
            typename_dict=self.typename_dict       
            event_name=self.get_eventname(event)
     
            if( event_name not in self.typename_dict and typename_list != ""):
                continue
            
            #record one round checkpoint into dict first
            if( self.try_one_round_record_update( event, one_round_record ) ):
                continue
            else:
                self.update_one_round_to_data_dict( typename_list, one_round_record, data_dict, event )    
                self.force_one_round_record_update( event, one_round_record )
        return self.pid_dict

    def pid_dict_update( self, pid ):
        if(pid not in self.pid_dict):
            self.pid_dict[pid]={'data_dict':{},'one_round_record':{}}
    
    def try_one_round_record_update( self, event, one_round_record ):
        event_name=self.get_eventname(event)
        key=event_name+"-"+str(event['pthread_id'])
        if( key not in one_round_record ):
            one_round_record[key] = event.timestamp 
            return True
        else:
            return False
        
    def update_one_round_to_data_dict( self, typename_list, one_round_record, data_dict, event ):
        event_name=self.get_eventname(event)
        key=event_name+"-"+str(event['pthread_id'])
        if( key not in data_dict ):
            data_dict[key]=[event.timestamp-one_round_record[key]]
        else:
            data_dict[key].append(event.timestamp-one_round_record[key])

    def force_one_round_record_update( self, event, one_round_record ):
        event_name=self.get_eventname(event)
        key=event_name+"-"+str(event['pthread_id'])
        one_round_record[key] = event.timestamp 
        
class TracepointMerge:
    def __init__( self ):
        self.tracepoint_dict={}
        self.record_bucket={}
        self.tracepoint_rw_lock = RWLock.RWLock()
        self.record_bucket_rw_lock = RWLock.RWLock()
        self.config = Config()
        tracepoint_dict = self.config.tracepoint_list
        self.first_event = []
        for tracepoint_type, tracepoint_list in tracepoint_dict.items():
            self.first_event.append(tracepoint_type+":"+tracepoint_list[0])

    def get_tracepoint_dict( self ):
        res = {}
        for event_name, timestamps in self.tracepoint_dict.items():
            res[event_name] = numpy.mean(timestamps)
        res = OrderedDict( sorted( res.items(), key=lambda t:t[1]) )
        with open( self.config.result_output, 'w') as file:
            for event_name, timestamp in res.items() :
                file.write( event_name )
                file.write( "\t"+str(timestamp) )
                file.write("\n")

    def record_bucket_update( self, record ):
        try:
            record_id = record['record_id']
            record_type = record['record_type']
            record_data = record['record_data']
        except:
            print(record)        
        self.record_bucket_rw_lock.writer_acquire()
        if( record_id not in self.record_bucket ):
            self.record_bucket[record_id] = {}
            self.record_bucket[record_id]['unreceived'] = 2
            self.record_bucket[record_id]['data'] = {}
         
        if( record_type not in self.record_bucket[record_id] ):
            self.record_bucket[record_id]['unreceived'] -= 1
            self.record_bucket[record_id][record_type] = record_data
            self.update_with_timestamp_shift_strategy( self.record_bucket[record_id], record_type )
        
        
        if( self.record_bucket[record_id]['unreceived'] == 0 ):
            ordered_record = OrderedDict( sorted(self.record_bucket[record_id]['data'].items(), key=lambda t: t[0] ))
            self.record_bucket[record_id]['data'] = self.tracepoint_dict_update( ordered_record )
            with open( self.config.log_output, 'a' ) as file:
                file.write( json.dumps({'record_id':record_id, 'record_data':self.record_bucket[record_id]['data']})+"\n"  )
            del self.record_bucket[record_id] 
         
        self.record_bucket_rw_lock.writer_release()
        return
    
    def timestamp_delta_cal( self, record_base, record_need_to_shift ):
        """
            find the timestamp delta between two server 
        """
        return 0
    
    def record_modify_before_merge( self, data, record_type, timestamp_delta ):
        record = {}
        for timestamp, event_name in data.items():
            event_name = record_type+":"+event_name
            timestamp = int(timestamp) - timestamp_delta
            record[timestamp] = event_name
        return record
    
    def update_with_timestamp_shift_strategy( self, record, cur_record_type ):
        """
            timeshift for different servers, timeshift will align to primary osd server
        """
        if( cur_record_type == 'primary' ):
            if( 'client' in record ):
                delta = self.timestamp_delta_cal( record['primary'] , record['client'] )
                record['client'] = self.record_modify_before_merge( record['client'], 'client', delta )
                record['data'].update( record['client'] )
            if( 'replica' in record ):
                delta = self.timestamp_delta_cal( record['primary'] , record['replica'] )
                record['replica'] = self.record_modify_before_merge( record['replica'], 'replica', delta )
                record['data'].update( record['replica'] )
            record['primary'] = self.record_modify_before_merge( record['primary'], 'primary', 0 )
            record['data'].update( record['primary'] )
        
        if( cur_record_type == 'client' ):
            if( not is_empty(record['primary']) ):
                delta = self.timestamp_delta_cal( record['primary'] , record['client'] )
                record['client'] = self.record_modify_before_merge( record['client'], 'client', delta )
                record['data'].update( record['client'] )
        
        if( cur_record_type == 'replica' ):
            if( 'primary' in record ):
                delta = self.timestamp_delta_cal( record['primary'] , record['replica'] )
                record['replica'] = self.record_modify_before_merge( record['replica'], 'replica', delta )
                record['data'].update( record['replica'] )
     
    def tracepoint_dict_update( self, record ):
        self.tracepoint_rw_lock.writer_acquire()
        first = True
        tmp_eventname_counter = {}
        tmp_record = {}
        for timestamp, event_name in record.items():
#            if( event_name not in tmp_eventname_counter ):
#                tmp_eventname_counter[event_name] = 0
#            else:
#                tmp_eventname_counter[event_name] += 1
#                event_name = event_name+"_"+str(tmp_eventname_counter[event_name])
            
            if( first ):
                if( event_name in self.first_event ):
                    base_timestamp = timestamp
                    relative_time = 0
                    first =  False
                else:
                    continue
            else:
                relative_time = timestamp - base_timestamp
            
            if( event_name not in self.tracepoint_dict ):
                self.tracepoint_dict[event_name] = []
            self.tracepoint_dict[event_name].append(relative_time)
            
            tmp_record[relative_time] = event_name
        self.tracepoint_rw_lock.writer_release()
        return OrderedDict( sorted(tmp_record.items(), key=lambda t: t[0]) )

