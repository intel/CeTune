import sys
import os
sys.path.append("..")
from workflow import workflow
from visualizer import *

dest_dir = '/mnt/data'
path = 'summary_excel'

def run():
    file_list_old = os.listdir('/mnt/data')
    workflow.main([])
    file_list_new = os.listdir('/mnt/data')
    for l in file_list_old:
        file_list_new.remove(l)
    cmd = ['--dest_dir', '%s/%s/' % (dest_dir, path), '--type','filestore','--path']
    cmd.extend(file_list_new)
    excel_summary_generator.main(cmd)

if __name__ == '__main__':
    run()