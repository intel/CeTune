import sys
import numpy
import copy
import re

if( len(sys.argv)==2 ):
    input_file = sys.argv[1]

checkpoint_list=[]
#checkpoint_list=["filestore:do_transaction_start:op_type=10-filestore:opwq_process_finish","filestore:opwq_process_start-filestore:do_transaction_finish:op_type=10","filestore:opwq_process_start-filestore:opwq_process_finish","osd:opwq_process_finish-filestore:opwq_process_finish","osd:opwq_process_start-filestore:opwq_process_finish","osd:opwq_process_start-filestore:opwq_process_start","keyvaluestore:do_transaction_start:op_type=10-keyvaluestore:opwq_process_finish","keyvaluestore:opwq_process_start-keyvaluestore:do_transaction_finish:op_type=10","keyvaluestore:opwq_process_start-keyvaluestore:opwq_process_finish","osd:opwq_process_finish-keyvaluestore:opwq_process_finish","osd:opwq_process_start-keyvaluestore:opwq_process_finish","osd:opwq_process_start-keyvaluestore:opwq_process_start","keyvaluestore:queue_op_finish-keyvaluestore:opwq_process_finish","osd:opwq_process_finish-keyvaluestore:opwq_process_start"]
#checkpoint_list=["filestore:do_transaction_start:op_type=10-filestore:opwq_process_finish","filestore:opwq_process_start-filestore:do_transaction_finish:op_type=10","osd:opwq_process_finish-filestore:opwq_process_finish","osd:opwq_process_start-filestore:opwq_process_finish","osd:opwq_process_start-filestore:opwq_process_start","keyvaluestore:do_transaction_start:op_type=10-keyvaluestore:opwq_process_finish","keyvaluestore:opwq_process_start-keyvaluestore:do_transaction_finish:op_type=10","osd:opwq_process_finish-keyvaluestore:opwq_process_finish","osd:opwq_process_start-keyvaluestore:opwq_process_finish","osd:opwq_process_start-keyvaluestore:opwq_process_start"]

first_line = True
res_dict={}
first_line_data = ""
with open( input_file, 'r') as fd:
    for line in fd:
        if( first_line ):
            first_line = False
            first_line_data = line
            res_dict['pid']=re.search(r'=*(\w*)=*',first_line_data).group(1)
            continue
        res = line.split(',')
        data = map(int,res[2::])
        avg = numpy.mean( data )
        res_dict[res[0]]=str(avg)
        #res_dict[res[0]]=res[1]
print(input_file)
print(res_dict['pid'])

res_dict_sum={}
#for key in res_dict.keys():
#    if( key != 'pid' and key not in checkpoint_list ):
#        sum_key=re.search(r'([^-]*)-*\d*',key).group(1)
#        if( sum_key not in res_dict_sum ):
#            res_dict_sum[sum_key]=[]
#        res_dict_sum[sum_key].append(float(res_dict[key]))
#for key in sorted(res_dict_sum.keys()):
#    if( key != 'pid' and key not in checkpoint_list ):
#        print(key+":  "+str(numpy.mean(res_dict_sum[key])))

for key in sorted(res_dict.keys()):
    if( key != 'pid' and key not in checkpoint_list ):
        print(key+":  "+res_dict[key])
print("")
