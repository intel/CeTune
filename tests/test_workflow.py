import sys
import os
sys.path.append("..")
from workflow import workflow
from visualizer import *

case_file = "../conf/cases.conf"
case_old = ""
case_new = "fiorbd          40                 10G        seqwrite             64k                      64             300             300          fiorbd             rbd        4osd    restart"
dest_dir = '/mnt/data'
path = 'summary_excel'

def run():
    if os.path.exists(case_file):
        f_read =  open(case_file, 'r')
        case_old = f_read.read()
        f_read.close()

        f_write = open(case_file, 'w')
        f_write.write(case_new)
        f_write.close()

        file_list_old = os.listdir(dest_dir)
        workflow.main([])
        file_list_new = os.listdir(dest_dir)
        for l in file_list_old:
            file_list_new.remove(l)
        cmd = ['--dest_dir', '%s/' % (dest_dir), '--type','filestore','--path']
        cmd.extend(file_list_new)
        excel_summary_generator.main(cmd)

        f_write = open(case_file, 'w')
        f_write.write(case_old)
        f_write.close()

if __name__ == '__main__':
    run()