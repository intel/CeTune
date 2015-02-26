#!/usr/bin/python
#IMPORTANT: this script is based on python 2.x, and python 3.x is not supported.
#Before using this script, you shoule make sure the following modules have been installed.


import os
import re
import sys
import random
import linecache
import xlsxwriter
import shutil


def check_index(vlist,vnum):
    try:
        return vlist[vnum]
    except IndexError,e:
        return ''


def get_data_throughput(directory,data_throughput,op_type):
    data_throughput.append(['','Throughput','IOPS','BW','Latency','Throughput_avg','IOPS','BW','Latency'])
    file1=os.path.join(directory,'ceph/ceph_all_osd_iostat.csv')
    if os.path.exists(file1):
        list1=linecache.getline(file1,1).strip().strip(',').split(',')
        list2=linecache.getline(file1,2).strip().strip(',').split(',')
        list3=linecache.getline(file1,3).strip().strip(',').split(',')
        if op_type=='read':
            data_throughput.append(['Ceph','from_iostat',check_index(list2,list1.index('r/s')),check_index(list2,list1.index('rMB/s')),check_index(list2,list1.index('await')),'',check_index(list3,list1.index('r/s')),check_index(list3,list1.index('rMB/s')),check_index(list3,list1.index('await'))])
        elif op_type=='write':
            data_throughput.append(['Ceph','from_iostat',check_index(list2,list1.index('w/s')),check_index(list2,list1.index('wMB/s')),check_index(list2,list1.index('await')),'',check_index(list3,list1.index('w/s')),check_index(list3,list1.index('wMB/s')),check_index(list3,list1.index('await'))])
        else:
            data_throughput.append(['Ceph','from_iostat','','','','','','',''])
    else:
        data_throughput.append(['Ceph','from_iostat','','','','','','',''])

    file2=os.path.join(directory,'vclient/vclient_fio.csv')
    if os.path.exists(file2):
        f=open(file2,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[0].strip().strip(',').split(',')
            list2=flist[-2].strip().strip(',').split(',')
            list3=flist[-1].strip().strip(',').split(',')
            data_throughput.append(['vclient','from_fio',check_index(list2,list1.index('iops')),check_index(list2,list1.index('bw(KB/s)')),check_index(list2,list1.index('lat(ms)')),'',check_index(list3,list1.index('iops')),check_index(list3,list1.index('bw(KB/s)')),check_index(list3,list1.index('lat(ms)'))])
        else:
            data_throughput.append(['vclient','from_fio','','','','','','',''])
    else:
        data_throughput.append(['vclient','from_fio','','','','','','',''])

    file3=os.path.join(directory,'client/client_fio.csv')
    if os.path.exists(file3):
        f=open(file3,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[0].strip().strip(',').split(',')
            list2=flist[-2].strip().strip(',').split(',')
            list3=flist[-1].strip().strip(',').split(',')
            data_throughput.append(['client','from_fio',check_index(list2,list1.index('iops')),check_index(list2,list1.index('bw(KB/s)')),check_index(list2,list1.index('lat(ms)')),'',check_index(list3,list1.index('iops')),check_index(list3,list1.index('bw(KB/s)')),check_index(list3,list1.index('lat(ms)'))])
        else:
            data_throughput.append(['client','from_fio','','','','','','',''])
    else:
        data_throughput.append(['client','from_fio','','','','','','',''])


def get_data_cpu(directory,data_cpu):
    data_cpu.append(['CPU','sar all user%','sar all sys%','sar all iowait%','sar all soft%','sar all idle%'])
    file1=os.path.join(directory,'ceph/ceph_cpu_sar.csv')
    if os.path.exists(file1):
        f=open(file1,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[-1].strip().strip(',').split(',')
            list2=flist[0].strip().strip(',').split(',')
            data_cpu.append(['Ceph',check_index(list1,list2.index('%usr')),check_index(list1,list2.index('%sys')),check_index(list1,list2.index('%iowait')),check_index(list1,list2.index('%soft')),check_index(list1,list2.index('%idle'))])
        else:
            data_cpu.append(['Ceph','','','','',''])
    else:
        data_cpu.append(['Ceph','','','','',''])

    file2=os.path.join(directory,'vclient/vclient_cpu_sar.csv')
    if os.path.exists(file2):
        f=open(file2,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[-1].strip().strip(',').split(',')
            list2=flist[0].strip().strip(',').split(',')
            data_cpu.append(['vclient',check_index(list1,list2.index('%usr')),check_index(list1,list2.index('%sys')),check_index(list1,list2.index('%iowait')),check_index(list1,list2.index('%soft')),check_index(list1,list2.index('%idle'))])
        else:
            data_cpu.append(['vclient','','','','',''])
    else:
        data_cpu.append(['vclient','','','','',''])


    file3=os.path.join(directory,'client/client_cpu_sar.csv')
    if os.path.exists(file3):
        f=open(file3,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[-1].strip().strip(',').split(',')
            list2=flist[0].strip().strip(',').split(',')
            data_cpu.append(['Client',check_index(list1,list2.index('%usr')),check_index(list1,list2.index('%sys')),check_index(list1,list2.index('%iowait')),check_index(list1,list2.index('%soft')),check_index(list1,list2.index('%idle'))])
        else:
            data_cpu.append(['Client','','','','',''])
    else:
        data_cpu.append(['Client','','','','',''])


def get_data_memory(directory,data_memory):
    data_memory.append(['Memory','kbmemfree','kbmemused','%memused'])
    file1=os.path.join(directory,'ceph/ceph_mem_sar.csv')
    if os.path.exists(file1):
        f=open(file1,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[-1].strip().strip(',').split(',')
            list2=flist[0].strip().strip(',').split(',')
            data_memory.append(['Ceph',check_index(list1,list2.index('kbmemfree')),check_index(list1,list2.index('kbmemused')),check_index(list1,list2.index('%memused'))])
        else:
            data_memory.append(['Ceph','','',''])
    else:
        data_memory.append(['Ceph','','',''])

    file2=os.path.join(directory,'vclient/vclient_mem_sar.csv')
    if os.path.exists(file2):
        f=open(file2,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[-1].strip().strip(',').split(',')
            list2=flist[0].strip().strip(',').split(',')
            data_memory.append(['vclient',check_index(list1,list2.index('kbmemfree')),check_index(list1,list2.index('kbmemused')),check_index(list1,list2.index('%memused'))])
        else:
            data_memory.append(['vclient','','',''])
    else:
        data_memory.append(['vclient','','',''])

    file3=os.path.join(directory,'client/client_mem_sar.csv')
    if os.path.exists(file3):
        f=open(file3,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[-1].strip().strip(',').split(',')
            list2=flist[0].strip().strip(',').split(',')
            data_memory.append(['Client',check_index(list1,list2.index('kbmemfree')),check_index(list1,list2.index('kbmemused')),check_index(list1,list2.index('%memused'))])
        else:
            data_memory.append(['Client','','',''])
    else:
        data_memory.append(['Client','','',''])


def get_data_nic(directory,data_nic):
    data_nic.append(['NIC','rxpck/s','txpcks','rxkB/s','txkB/s'])
    file1=os.path.join(directory,'ceph/ceph_nic_sar.csv')
    if os.path.exists(file1):
        f=open(file1,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[0].strip().strip(',').split(',')
            list2=flist[-1].strip().strip(',').split(',')
            data_nic.append(['Ceph',check_index(list2,list1.index('rxpck/s')),check_index(list2,list1.index('txpck/s')),check_index(list2,list1.index('rxkB/s')),check_index(list2,list1.index('txkB/s'))])
        else:
            data_nic.append(['Ceph','','','',''])
    else:
        data_nic.append(['Ceph','','','',''])

    file2=os.path.join(directory,'vclient/vclient_nic_sar.csv')
    if os.path.exists(file2):
        f=open(file2,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[0].strip().strip(',').split(',')
            list2=flist[-1].strip().strip(',').split(',')
            data_nic.append(['vclient',check_index(list2,list1.index('rxpck/s')),check_index(list2,list1.index('txpck/s')),check_index(list2,list1.index('rxkB/s')),check_index(list2,list1.index('txkB/s'))])
        else:
            data_nic.append(['vclient','','','',''])
    else:
        data_nic.append(['vclient','','','',''])

    file3=os.path.join(directory,'client/client_nic_sar.csv')
    if os.path.exists(file3):
        f=open(file3,'r')
        flist=f.readlines()
        f.close()
        num=len(flist)
        if num>3:
            list1=flist[0].strip().strip(',').split(',')
            list2=flist[-1].strip().strip(',').split(',')
            data_nic.append(['Client',check_index(list2,list1.index('rxpck/s')),check_index(list2,list1.index('txpck/s')),check_index(list2,list1.index('rxkB/s')),check_index(list2,list1.index('txkB/s'))])
        else:
            data_nic.append(['Client','','','',''])
    else:
        data_nic.append(['Client','','','',''])


def get_data_ceph_disk(directory,data_ceph_disk):
    data_ceph_disk.append(['AVG_IOPS_Journal','r/s','w/s','rMB/s','wMB/s','avgrq-sz','avgqu-sz','await','svtcm','%util'])
    file1=os.path.join(directory,'ceph/ceph_all_osd_iostat.csv')
    if os.path.exists(file1):
        list1=linecache.getline(file1,1).strip().strip(',').split(',')
        list2=linecache.getline(file1,3).strip().strip(',').split(',')
        data_ceph_disk.append(['Osd',check_index(list2,list1.index('r/s')),check_index(list2,list1.index('w/s')),check_index(list2,list1.index('rMB/s')),check_index(list2,list1.index('wMB/s')),check_index(list2,list1.index('avgrq-sz')),check_index(list2,list1.index('avgqu-sz')),check_index(list2,list1.index('await')),check_index(list2,list1.index('svctm')),check_index(list2,list1.index('%util'))])
    else:
        data_ceph_disk.append(['Osd','','','','','','','','',''])

    file2=os.path.join(directory,'ceph/ceph_all_journal_iostat.csv')
    if os.path.exists(file2):
        list1=linecache.getline(file2,1).strip().strip(',').split(',')
        list2=linecache.getline(file2,3).strip().strip(',').split(',')
        data_ceph_disk.append(['Journal',check_index(list2,list1.index('r/s')),check_index(list2,list1.index('w/s')),check_index(list2,list1.index('rMB/s')),check_index(list2,list1.index('wMB/s')),check_index(list2,list1.index('avgrq-sz')),check_index(list2,list1.index('avgqu-sz')),check_index(list2,list1.index('await')),check_index(list2,list1.index('svctm')),check_index(list2,list1.index('%util'))])
    else:
        data_ceph_disk.append(['Journal','','','','','','','','',''])


def format_write(worksheet,row,col,var,cell_format):
    global cell_format_num_int
    global cell_format_num_float
    try:
        var1=float(var)
        if var1==int(var1):
             worksheet.write(row,col,var1,cell_format_num_int)
        else:
             worksheet.write(row,col,var1,cell_format_num_float)
    except ValueError:
        worksheet.write(row,col,var,cell_format)


def xlsxwriter_write_csv(workbookname,directory,color,filename,sheetname):
    global filenum
    global filenoload
    global cell_format_title
    file1=os.path.join(directory,filename)
    try:
        f=open(file1,'r')
        row=-1
        workbook=workbookname
        worksheet=workbook.add_worksheet(sheetname)
        worksheet.set_column(0,0,16)
        worksheet.set_column(1,15,13)
        worksheet.set_tab_color(color)
        for line in f.readlines():
            row+=1
            col=-1
            line=line.strip().strip(',')
            list2=line.split(',')
            for var in list2:
                col+=1
                format_write(worksheet,row,col,var,cell_format_title)
        f.close()
    except IOError,e:
        filenum+=1
        filenoload.append(filename)


def xlsxwriter_write_list(worksheet,row,col,dlist):
    global cell_format_title
    global cell_format_title_color
    cnum=col-1
    for i in dlist:
        cnum+=1
        rnum=row-1
        for j in i:
            rnum+=1
            if rnum-row==0:
                format_write(worksheet,rnum,cnum,j,cell_format_title_color)
            else:
                format_write(worksheet,rnum,cnum,j,cell_format_title)


def xlsxwriter_summary_title(row,col,directory,summaryname):
    global cell_format_title
    global cell_format_title_color
    summaryname.write(row,col,'ceph_server',cell_format_title_color)
    summaryname.write(row+1,col,'ceph_client',cell_format_title_color)
    summaryname.write(row+2,col,'ceph_vclient',cell_format_title_color)
    allconf=os.path.join(directory,'all.conf')
    try:
        f=open(allconf,'r')
        for line in f.readlines():
            line=line.strip()
            if re.search('deploy_osd_servers',line):
                num_osd=len(line.split(','))
                format_write(summaryname,row,col+1,num_osd,cell_format_title)
            if re.search('deploy_rbd_nodes',line):
                num_rbd=len(line.split(','))
                format_write(summaryname,row+1,col+1,num_rbd,cell_format_title)
            if re.search('list_vclient',line):
                num_vclient=len(line.split(','))
                format_write(summaryname,row+2,col+1,num_vclient,cell_format_title)
        f.close()
    except IOError,e:
        print 'Could not open file:',e


def xlsxwriter_write_title(row1,col1,row2,col2,workbook,worksheet,var):
    tformat=workbook.add_format()
    tformat.set_border()
    tformat.set_align('center')
    tformat.set_align('vcenter')
    tformat.set_bold()
    worksheet.merge_range(row1,col1,row2,col2,var,tformat)


def write_history_csv(history_directory,work_directory,directory):
    global data_throughput
    global data_cpu
    history_file=os.path.join(history_directory,'history.csv')
    if not os.path.exists(history_file):
        fh=open(history_file,'w')
        fh.write('Runid,OP_SIZE,OP_TYPE,QD,Engine,server_num,client_num,rbd_num,RBD_FIO_IOPS,RBD_FIO_BW,RBD_FIO_Latency,osd_read_iops,osd_write_iops,osd_read_bw,osd_write_bw,cpu_idle\n')
        fh.close()
    list1=directory.strip().strip('.').strip('/').split('-')
    list2=[]
    for i in 0,3,2,4,-1:
        list2.append(list1[i]+',')
    allconf=os.path.join(work_directory,'all.conf')
    try:
        f=open(allconf,'r')
        for line in f.readlines():
            line=line.strip()
            if re.search('deploy_osd_servers',line):
                server_num=len(line.split(','))
            if re.search('deploy_rbd_nodes',line):
                client_num=len(line.split(','))
            if list1[-1]=='vdb':
                #if re.search('run_vm_num',line):
                #    rbd_num=(line.split('='))[1]
                rbd_num=list1[1].repalce('instance','')
            elif list1[-1]=='fiorbd':
                if re.search('rbd_num_per_client',line):
                    rbd_num=0
                    rbd_num_per_client=(line.strip().split('='))[1]
                    list3=rbd_num_per_client.strip().split(',')
                    for i in list3:
                        rbd_num=rbd_num+int(i)
        f.close()
    except IOError,e:
        server_num=''
        client_num=''
        rbd_num=''
    list2.append(str(server_num)+',')
    list2.append(str(client_num)+',')
    list2.append(str(rbd_num)+',')
    if list1[-1]=='vdb':
        list2.append(check_index(data_throughput[2],2)+',')
        list2.append(check_index(data_throughput[2],3)+',')
        list2.append(check_index(data_throughput[2],4)+',')
    elif list1[-1]=='fiorbd':
        list2.append(check_index(data_throughput[3],2)+',')
        list2.append(check_index(data_throughput[3],3)+',')
        list2.append(check_index(data_throughput[3],4)+',')
    fr=os.path.join(work_directory,'csvs/ceph/ceph_all_osd_iostat.csv')
    if os.path.exists(fr):
        list3=linecache.getline(fr,1).strip().strip(',').split(',')
        list4=linecache.getline(fr,2).strip().strip(',').split(',')
        list2.append(check_index(list4,list3.index('r/s'))+',')
        list2.append(check_index(list4,list3.index('w/s'))+',')
        list2.append(check_index(list4,list3.index('rMB/s'))+',')
        list2.append(check_index(list4,list3.index('wMB/s'))+',')
    else:
        list2.append(',,,,')
    list2.append(check_index(data_cpu[1],5)+',')
    try:
        num=0
        fh=open(history_file,'r')
        writefile=open('Temposxs.csv','w')
        for i in fh.readlines():
            if (i.strip().strip(',').split(','))[0] != list1[0]:
                writefile.writelines(i)
            else:
                num+=1
                writefile.writelines(list2)
                writefile.write('\n')
        if num==0:
            writefile.writelines(list2)
            writefile.write('\n')
        fh.close()
        writefile.close()
        os.remove(history_file)
        shutil.move('Temposxs.csv',history_file)
    except IOError,e:
        print 'Error:',e



#####################the main function####################################################
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Error: wrong number of parameters!'
        print "Usage:\n\t",sys.argv[0],'   history_directory','   work_directory'
        sys.exit()
    history_directory=sys.argv[1]
    work_directory=sys.argv[2]
    directory=(work_directory.strip().strip('.').strip('/').split('/'))[-1]
    bookname=directory+'.xlsx'
    print "Starting load all the csvs into %s..." %bookname
    global filenum
    global filenoload
    global cephnum
    global vclientnum
    filenum=0
    filenoload=[]
    path1=os.path.join(work_directory,'csvs')
    path2=os.path.join(path1,bookname)
    if os.path.exists(path2):
        os.remove(path2)


##########create workbook,and some output formats with the xlsxwriter module##########
    fp=xlsxwriter.Workbook(path2)
    summarysheet=fp.add_worksheet('Summary')
    summarysheet.set_column(0,1,18)
    summarysheet.set_column(2,15,13)
    summarysheet.set_tab_color('blue')
    global cell_format_title
    cell_format_title=fp.add_format()
    cell_format_title.set_bold()
    cell_format_title.set_border()
    cell_format_title.set_align('left')
    global cell_format_title_color
    cell_format_title_color=fp.add_format()
    cell_format_title_color.set_bold()
    cell_format_title_color.set_border()
    cell_format_title_color.set_align('left')
    cell_format_title_color.set_bg_color('yellow')
    global cell_format_num_float
    cell_format_num_float=fp.add_format()
    cell_format_num_float.set_border()
    cell_format_num_float.set_align('right')
    cell_format_num_float.set_num_format('0.000')
    global cell_format_num_int
    cell_format_num_int=fp.add_format()
    cell_format_num_int.set_border()
    cell_format_num_int.set_align('right')
    cell_format_num_int.set_num_format('0')



#########add summary sheet, and write the sheet from the csvs########################
    xlsxwriter_summary_title(0,0,work_directory,summarysheet)
    global data_throughput
    data_throughput=[]
    global data_cpu
    data_cpu=[]
    data_memory=[]
    data_nic=[]
    data_ceph_disk=[]
    if re.search('read',directory):
        get_data_throughput(path1,data_throughput,'read')
    elif re.search('write',directory):
        get_data_throughput(path1,data_throughput,'write')
    else:
        get_data_throughput(path1,data_throughput,'')
    get_data_cpu(path1,data_cpu)
    get_data_memory(path1,data_memory)
    get_data_nic(path1,data_nic)
    get_data_ceph_disk(path1,data_ceph_disk)
    xlsxwriter_write_title(5,0,13,0,fp,summarysheet,'Ceph')
    xlsxwriter_write_list(summarysheet,5,1,data_throughput)
    xlsxwriter_write_title(14,0,19,0,fp,summarysheet,'CPU')
    xlsxwriter_write_list(summarysheet,14,1,data_cpu)
    xlsxwriter_write_title(20,0,23,0,fp,summarysheet,'Memory')
    xlsxwriter_write_list(summarysheet,20,1,data_memory)
    xlsxwriter_write_title(24,0,28,0,fp,summarysheet,'NIC')
    xlsxwriter_write_list(summarysheet,24,1,data_nic)
    xlsxwriter_write_title(29,0,38,0,fp,summarysheet,'Ceph Disk')
    xlsxwriter_write_list(summarysheet,29,1,data_ceph_disk)


########################load the csvs of ceph into the workbook######################
    ceph_path=os.path.join(path1,'ceph')
    if os.path.exists(ceph_path):
        xlsxwriter_write_csv(fp,ceph_path,'red','ceph_iops_sar.csv','ceph_iops_sar')
        xlsxwriter_write_csv(fp,ceph_path,'red','ceph_cpu_sar.csv','ceph_cpu_sar')
        xlsxwriter_write_csv(fp,ceph_path,'red','ceph_all_journal_iostat.csv','ceph_journal_iostat')
        xlsxwriter_write_csv(fp,ceph_path,'red','ceph_all_journal_iostat_loadline.csv','ceph_journal_iostat_loadline')
        xlsxwriter_write_csv(fp,ceph_path,'red','ceph_all_osd_iostat.csv','ceph_osd_iostat')
        xlsxwriter_write_csv(fp,ceph_path,'red','ceph_all_osd_iostat_loadline.csv','ceph_osd_iostat_loadline')
        xlsxwriter_write_csv(fp,ceph_path,'red','ceph_mem_sar.csv','ceph_memory')
        xlsxwriter_write_csv(fp,ceph_path,'red','ceph_nic_sar.csv','ceph_nic')


########################load the csvs of client into the workbook####################
    client_path=os.path.join(path1,'client')
    if os.path.exists(client_path):
        xlsxwriter_write_csv(fp,client_path,'green','client_fio.csv','client_fio')
        xlsxwriter_write_csv(fp,client_path,'green','client_cpu_sar.csv','client_cpu')
        xlsxwriter_write_csv(fp,client_path,'green','client_iops_sar.csv','client_iops')
        xlsxwriter_write_csv(fp,client_path,'green','client_nic_sar.csv','client_nic')
        xlsxwriter_write_csv(fp,client_path,'green','client_mem_sar.csv','client_memory')


########################load the csvs of vclient into the workbook###################
    vclient_path=os.path.join(path1,'vclient')
    if os.path.exists(vclient_path):
        xlsxwriter_write_csv(fp,vclient_path,'purple','vclient_fio.csv','vclient_fio')
        xlsxwriter_write_csv(fp,vclient_path,'purple','vclient_cpu_sar.csv','vclient_cpu')
        xlsxwriter_write_csv(fp,vclient_path,'purple','vclient_iops_sar.csv','vclient_iops')
        xlsxwriter_write_csv(fp,vclient_path,'purple','vclient_mem_sar.csv','vclient_memory')
        xlsxwriter_write_csv(fp,vclient_path,'purple','vclient_nic_sar.csv','vclient_nic')
        xlsxwriter_write_csv(fp,vclient_path,'purple','vclient_all_rbd_iostat.csv','vclient_vdb_iostat')
        xlsxwriter_write_csv(fp,vclient_path,'purple','vclient_all_rbd_iostat_loadline.csv','vclient_vdb_iostat_loadline')

    fp.close()
    if filenum==0:
        print 'All the files have been loaded into the %s.' %bookname
    else:
        print 'IMPORTANT: some files failed to load into the excel:'
        for i in filenoload:
            print "\t%s" %i
########################write history.csv into sys.argv[1]###########################
    write_history_csv(history_directory,work_directory,directory)
    print "The '%s' has been updated." %os.path.join(history_directory,'history.csv')
#####################################################################################
