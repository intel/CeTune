import os
import math
import json
import xlwt
import xlsxwriter
import argparse

dataObj = {}

def GetDataObj(case):
    global dataObj

    dataPath = os.path.join(case,"result.json")
    if os.path.exists(dataPath):
        with open(dataPath) as dataFile:
            return json.load(dataFile)

def GetETables(cases, storeType):
    global dataObj
    if storeType == "fileStore":
        eTables = [[["runcase","title"]],[["","subtitle"]],[["Throughput","subtitle"]],[["FIO_IOPS","sstitle"]],[["FIO_BW","sstitle"]],[["FIO_Latency","sstitle"]],[["Throughput_avg","subtitle"]],[["FIO_IOPS","sstitle"]],[["FIO_BW","sstitle"]],[["FIO_Latency","sstitle"]],
                  [["CPU","subtitle"]],[["sar all user%","sstitle"]],[["sar all kernel%","sstitle"]],[["sar all iowait%","sstitle"]],[["sar all soft%","sstitle"]],[["sar all idle%","sstitle"]],
                  [["AVG_IOPS_Journal","subtitle"]],[["r/s","sstitle"]],[["w/s","sstitle"]],[["rMB/s","sstitle"]],[["wMB/s","sstitle"]],[["avgrq-sz","sstitle"]],[["avgqu-sz","sstitle"]],[["await","sstitle"]],[["svtcm","sstitle"]],[["%util","sstitle"]],
                  [["AVG_IOPS_OSD","subtitle"]],[["r/s","sstitle"]],[["w/s","sstitle"]],[["rMB/s","sstitle"]],[["wMB/s","sstitle"]],[["avgrq-sz","sstitle"]],[["avgqu-sz","sstitle"]],[["await","sstitle"]],[["svtcm","sstitle"]],[["%util","sstitle"]],
                  [["Memory","subtitle"]],[["kbmemfree","sstitle"]],[["kbmemused","sstitle"]],[["%memused","sstitle"]],
                  [["NIC","subtitle"]],[["rxpck/s","sstitle"]],[["txpck/s","sstitle"]],[["rxkB/s","sstitle"]],[["txkB/s","sstitle"]]]
        for case in cases:
            dataObj = GetDataObj(case)
            eTables[0].append(case)
            eTables[1].extend(["ceph", "vclient", "client"])
            eTables[2].extend([["from iostat","rtitle"], ["from FIO","rtitle"], ["from iostat","rtitle"]])
            eTables[3].extend([cal_Throughput_FIO_IOPS_ceph(case), cal_Throughput_FIO_IOPS_vclient(case), ""])
            eTables[4].extend([cal_Throughput_FIO_BW_ceph(case), cal_Throughput_FIO_BW_vclient(case), ""])
            eTables[5].extend([cal_Throughput_FIO_Latency_ceph(case), cal_Throughput_FIO_Latency_vclient(case), ""])
            eTables[6].extend([["","subtitle"], ["","subtitle"], ["","subtitle"]])
            eTables[7].extend([cal_ThroughputAvg_FIO_IOPS_ceph(case), cal_Throughput_FIO_IOPS_vclient(case), ""])
            eTables[8].extend([cal_ThroughputAvg_FIO_BW_ceph(case), cal_Throughput_FIO_BW_vclient(case), ""])
            eTables[9].extend([cal_ThroughputAvg_FIO_Latency_ceph(case), cal_Throughput_FIO_Latency_vclient(case), ""])
            eTables[10].extend([["","subtitle"], ["","subtitle"], ["","subtitle"]])
            eTables[11].extend([cal_CPU_user_ceph(case), cal_CPU_user_vclient(case), cal_CPU_user_client(case)])
            eTables[12].extend([cal_CPU_kernel_ceph(case), cal_CPU_kernel_vclient(case), cal_CPU_kernel_client(case)])
            eTables[13].extend([cal_CPU_iowait_ceph(case), cal_CPU_iowait_vclient(case), cal_CPU_iowait_client(case)])
            eTables[14].extend([cal_CPU_soft_ceph(case), cal_CPU_soft_vclient(case), cal_CPU_soft_client(case)])
            eTables[15].extend([cal_CPU_idle_ceph(case), cal_CPU_idle_vclient(case), cal_CPU_idle_client(case)])
            eTables[16].extend([["SSD","rtitle"], ["vclient_total","rtitle"], ["client_total","rtitle"]])
            eTables[17].extend([cal_AVG_IOPS_Journal_r_ceph(case), cal_AVG_IOPS_Journal_r_vclient(case), cal_AVG_IOPS_Journal_r_client(case)])
            eTables[18].extend([cal_AVG_IOPS_Journal_w_ceph(case), cal_AVG_IOPS_Journal_w_vclient(case), cal_AVG_IOPS_Journal_w_client(case)])
            eTables[19].extend([cal_AVG_IOPS_Journal_rMB_ceph(case), cal_AVG_IOPS_Journal_rMB_vclient(case), cal_AVG_IOPS_Journal_rMB_client(case)])
            eTables[20].extend([cal_AVG_IOPS_Journal_wMB_ceph(case), cal_AVG_IOPS_Journal_wMB_vclient(case), cal_AVG_IOPS_Journal_wMB_client(case)])
            eTables[21].extend([cal_AVG_IOPS_Journal_avgrqsz_ceph(case), cal_AVG_IOPS_Journal_avgrqsz_vclient(case), cal_AVG_IOPS_Journal_avgrqsz_client(case)])
            eTables[22].extend([cal_AVG_IOPS_Journal_avgqusz_ceph(case), cal_AVG_IOPS_Journal_avgqusz_vclient(case), cal_AVG_IOPS_Journal_avgqusz_client(case)])
            eTables[23].extend([cal_AVG_IOPS_Journal_await_ceph(case), cal_AVG_IOPS_Journal_await_vclient(case), cal_AVG_IOPS_Journal_await_client(case)])
            eTables[24].extend([cal_AVG_IOPS_Journal_svtcm_ceph(case), cal_AVG_IOPS_Journal_svtcm_vclient(case), cal_AVG_IOPS_Journal_svtcm_client(case)])
            eTables[25].extend([cal_AVG_IOPS_Journal_util_ceph(case), cal_AVG_IOPS_Journal_util_vclient(case), cal_AVG_IOPS_Journal_util_client(case)])
            eTables[26].extend([["Data","rtitle"], ["vclient_average","rtitle"], ["client_average","rtitle"]])
            eTables[27].extend([cal_AVG_IOPS_OSD_r_ceph(case), cal_AVG_IOPS_OSD_r_vclient(case), cal_AVG_IOPS_OSD_r_client(case)])
            eTables[28].extend([cal_AVG_IOPS_OSD_w_ceph(case), cal_AVG_IOPS_OSD_w_vclient(case), cal_AVG_IOPS_OSD_w_client(case)])
            eTables[29].extend([cal_AVG_IOPS_OSD_rMB_ceph(case), cal_AVG_IOPS_OSD_rMB_vclient(case), cal_AVG_IOPS_OSD_rMB_client(case)])
            eTables[30].extend([cal_AVG_IOPS_OSD_wMB_ceph(case), cal_AVG_IOPS_OSD_wMB_vclient(case), cal_AVG_IOPS_OSD_wMB_client(case)])
            eTables[31].extend([cal_AVG_IOPS_OSD_avgrqsz_ceph(case), cal_AVG_IOPS_OSD_avgrqsz_vclient(case), cal_AVG_IOPS_OSD_avgrqsz_client(case)])
            eTables[32].extend([cal_AVG_IOPS_OSD_avgqusz_ceph(case), cal_AVG_IOPS_OSD_avgqusz_vclient(case), cal_AVG_IOPS_OSD_avgqusz_client(case)])
            eTables[33].extend([cal_AVG_IOPS_OSD_await_ceph(case), cal_AVG_IOPS_OSD_await_vclient(case), cal_AVG_IOPS_OSD_await_client(case)])
            eTables[34].extend([cal_AVG_IOPS_OSD_svtcm_ceph(case), cal_AVG_IOPS_OSD_svtcm_vclient(case), cal_AVG_IOPS_OSD_svtcm_client(case)])
            eTables[35].extend([cal_AVG_IOPS_OSD_util_ceph(case), cal_AVG_IOPS_OSD_util_vclient(case), cal_AVG_IOPS_OSD_util_client(case)])
            eTables[36].extend([["","subtitle"], ["","subtitle"], ["","subtitle"]])
            eTables[37].extend([cal_Memory_kbmemfree_ceph(case), cal_Memory_kbmemfree_vclient(case), cal_Memory_kbmemfree_client(case)])
            eTables[38].extend([cal_Memory_kbmemused_ceph(case), cal_Memory_kbmemused_vclient(case), cal_Memory_kbmemused_client(case)])
            eTables[39].extend([cal_Memory_memused_ceph(case), cal_Memory_memused_vclient(case), cal_Memory_memused_client(case)])
            eTables[40].extend([["","subtitle"], ["","subtitle"], ["","subtitle"]])
            eTables[41].extend([cal_NIC_rxpck_ceph(case), cal_NIC_rxpck_vclient(case), cal_NIC_rxpck_client(case)])
            eTables[42].extend([cal_NIC_txpck_ceph(case), cal_NIC_txpck_vclient(case), cal_NIC_txpck_client(case)])
            eTables[43].extend([cal_NIC_rxkB_ceph(case), cal_NIC_rxkB_vclient(case), cal_NIC_rxkB_client(case)])
            eTables[44].extend([cal_NIC_txkB_ceph(case), cal_NIC_txkB_vclient(case), cal_NIC_txkB_client(case)])
                
    elif storeType == "blueStore":
        eTables = [[["runcase","title"]],[["","subtitle"]],[["Throughput","subtitle"]],[["FIO_IOPS","sstitle"]],[["FIO_BW","sstitle"]],[["FIO_Latency","sstitle"]],[["Throughput_avg","subtitle"]],[["FIO_IOPS","sstitle"]],[["FIO_BW","sstitle"]],[["FIO_Latency","sstitle"]],
                  [["CPU","subtitle"]],[["sar all user%","sstitle"]],[["sar all kernel%","sstitle"]],[["sar all iowait%","sstitle"]],[["sar all soft%","sstitle"]],[["sar all idle%","sstitle"]],
                  [["AVG_IOPS_Journal","subtitle"]],[["r/s","sstitle"]],[["w/s","sstitle"]],[["rMB/s","sstitle"]],[["wMB/s","sstitle"]],[["avgrq-sz","sstitle"]],[["avgqu-sz","sstitle"]],[["await","sstitle"]],[["svtcm","sstitle"]],[["%util","sstitle"]],
                  [["AVG_IOPS_OSD","subtitle"]],[["r/s","sstitle"]],[["w/s","sstitle"]],[["rMB/s","sstitle"]],[["wMB/s","sstitle"]],[["avgrq-sz","sstitle"]],[["avgqu-sz","sstitle"]],[["await","sstitle"]],[["svtcm","sstitle"]],[["%util","sstitle"]],
                  [["Memory","subtitle"]],[["kbmemfree","sstitle"]],[["kbmemused","sstitle"]],[["%memused","sstitle"]],
                  [["NIC","subtitle"]],[["rxpck/s","sstitle"]],[["txpck/s","sstitle"]],[["rxkB/s","sstitle"]],[["txkB/s","sstitle"]]]
        for case in cases:
            eTables[0].append(case)
            eTables[1].extend(["ceph", "vclient", "client"])
            eTables[2].extend([["from iostat","rtitle"], ["from FIO","rtitle"], ["from iostat","rtitle"]])
            eTables[3].extend([cal_Throughput_FIO_IOPS_ceph(case), cal_Throughput_FIO_IOPS_vclient(case), ""])
            eTables[4].extend([cal_Throughput_FIO_BW_ceph(case), cal_Throughput_FIO_BW_vclient(case), ""])
            eTables[5].extend([cal_Throughput_FIO_Latency_ceph(case), cal_Throughput_FIO_Latency_vclient(case), ""])
            eTables[6].extend([["","subtitle"], ["","subtitle"], ["","subtitle"]])
            eTables[7].extend([cal_ThroughputAvg_FIO_IOPS_ceph(case), cal_Throughput_FIO_IOPS_vclient(case), ""])
            eTables[8].extend([cal_ThroughputAvg_FIO_BW_ceph(case), cal_Throughput_FIO_BW_vclient(case), ""])
            eTables[9].extend([cal_ThroughputAvg_FIO_Latency_ceph(case), cal_Throughput_FIO_Latency_vclient(case), ""])
            eTables[10].extend([["","subtitle"], ["","subtitle"], ["","subtitle"]])
            eTables[11].extend([cal_CPU_user_ceph(case), cal_CPU_user_vclient(case), cal_CPU_user_client(case)])
            eTables[12].extend([cal_CPU_kernel_ceph(case), cal_CPU_kernel_vclient(case), cal_CPU_kernel_client(case)])
            eTables[13].extend([cal_CPU_iowait_ceph(case), cal_CPU_iowait_vclient(case), cal_CPU_iowait_client(case)])
            eTables[14].extend([cal_CPU_soft_ceph(case), cal_CPU_soft_vclient(case), cal_CPU_soft_client(case)])
            eTables[15].extend([cal_CPU_idle_ceph(case), cal_CPU_idle_vclient(case), cal_CPU_idle_client(case)])
            eTables[16].extend([["SSD","rtitle"], ["vclient_total","rtitle"], ["client_total","rtitle"]])
            eTables[17].extend([cal_AVG_IOPS_Journal_r_ceph(case), cal_AVG_IOPS_Journal_r_vclient(case), cal_AVG_IOPS_Journal_r_client(case)])
            eTables[18].extend([cal_AVG_IOPS_Journal_w_ceph(case), cal_AVG_IOPS_Journal_w_vclient(case), cal_AVG_IOPS_Journal_w_client(case)])
            eTables[19].extend([cal_AVG_IOPS_Journal_rMB_ceph(case), cal_AVG_IOPS_Journal_rMB_vclient(case), cal_AVG_IOPS_Journal_rMB_client(case)])
            eTables[20].extend([cal_AVG_IOPS_Journal_wMB_ceph(case), cal_AVG_IOPS_Journal_wMB_vclient(case), cal_AVG_IOPS_Journal_wMB_client(case)])
            eTables[21].extend([cal_AVG_IOPS_Journal_avgrqsz_ceph(case), cal_AVG_IOPS_Journal_avgrqsz_vclient(case), cal_AVG_IOPS_Journal_avgrqsz_client(case)])
            eTables[22].extend([cal_AVG_IOPS_Journal_avgqusz_ceph(case), cal_AVG_IOPS_Journal_avgqusz_vclient(case), cal_AVG_IOPS_Journal_avgqusz_client(case)])
            eTables[23].extend([cal_AVG_IOPS_Journal_await_ceph(case), cal_AVG_IOPS_Journal_await_vclient(case), cal_AVG_IOPS_Journal_await_client(case)])
            eTables[24].extend([cal_AVG_IOPS_Journal_svtcm_ceph(case), cal_AVG_IOPS_Journal_svtcm_vclient(case), cal_AVG_IOPS_Journal_svtcm_client(case)])
            eTables[25].extend([cal_AVG_IOPS_Journal_util_ceph(case), cal_AVG_IOPS_Journal_util_vclient(case), cal_AVG_IOPS_Journal_util_client(case)])
            eTables[26].extend([["Data","rtitle"], ["vclient_average","rtitle"], ["client_average","rtitle"]])
            eTables[27].extend([cal_AVG_IOPS_OSD_r_ceph(case), cal_AVG_IOPS_OSD_r_vclient(case), cal_AVG_IOPS_OSD_r_client(case)])
            eTables[28].extend([cal_AVG_IOPS_OSD_w_ceph(case), cal_AVG_IOPS_OSD_w_vclient(case), cal_AVG_IOPS_OSD_w_client(case)])
            eTables[29].extend([cal_AVG_IOPS_OSD_rMB_ceph(case), cal_AVG_IOPS_OSD_rMB_vclient(case), cal_AVG_IOPS_OSD_rMB_client(case)])
            eTables[30].extend([cal_AVG_IOPS_OSD_wMB_ceph(case), cal_AVG_IOPS_OSD_wMB_vclient(case), cal_AVG_IOPS_OSD_wMB_client(case)])
            eTables[31].extend([cal_AVG_IOPS_OSD_avgrqsz_ceph(case), cal_AVG_IOPS_OSD_avgrqsz_vclient(case), cal_AVG_IOPS_OSD_avgrqsz_client(case)])
            eTables[32].extend([cal_AVG_IOPS_OSD_avgqusz_ceph(case), cal_AVG_IOPS_OSD_avgqusz_vclient(case), cal_AVG_IOPS_OSD_avgqusz_client(case)])
            eTables[33].extend([cal_AVG_IOPS_OSD_await_ceph(case), cal_AVG_IOPS_OSD_await_vclient(case), cal_AVG_IOPS_OSD_await_client(case)])
            eTables[34].extend([cal_AVG_IOPS_OSD_svtcm_ceph(case), cal_AVG_IOPS_OSD_svtcm_vclient(case), cal_AVG_IOPS_OSD_svtcm_client(case)])
            eTables[35].extend([cal_AVG_IOPS_OSD_util_ceph(case), cal_AVG_IOPS_OSD_util_vclient(case), cal_AVG_IOPS_OSD_util_client(case)])
            eTables[36].extend([["","subtitle"], ["","subtitle"], ["","subtitle"]])
            eTables[37].extend([cal_Memory_kbmemfree_ceph(case), cal_Memory_kbmemfree_vclient(case), cal_Memory_kbmemfree_client(case)])
            eTables[38].extend([cal_Memory_kbmemused_ceph(case), cal_Memory_kbmemused_vclient(case), cal_Memory_kbmemused_client(case)])
            eTables[39].extend([cal_Memory_memused_ceph(case), cal_Memory_memused_vclient(case), cal_Memory_memused_client(case)])
            eTables[40].extend([["","subtitle"], ["","subtitle"], ["","subtitle"]])
            eTables[41].extend([cal_NIC_rxpck_ceph(case), cal_NIC_rxpck_vclient(case), cal_NIC_rxpck_client(case)])
            eTables[42].extend([cal_NIC_txpck_ceph(case), cal_NIC_txpck_vclient(case), cal_NIC_txpck_client(case)])
            eTables[43].extend([cal_NIC_rxkB_ceph(case), cal_NIC_rxkB_vclient(case), cal_NIC_rxkB_client(case)])
            eTables[44].extend([cal_NIC_txkB_ceph(case), cal_NIC_txkB_vclient(case), cal_NIC_txkB_client(case)])
    return eTables

def GetExtTables(cases, storeType):
    global dataObj
    result = []
    for case in cases:
        if storeType == "fileStore":
            extTable = [[[case.split("-")[3], 16, 'title']], [["", 1, 'title'], ["CPU", 3, 'title'], ["Disk", 9, 'title'], ["Memory", 1, 'title'], ["NIC", 2, 'title']]]
            extTable.append(["", "user%", "kernel%+soft%", "iowait%", "r/s", "w/s", "rMB/s", "wMB/s", "requsz", "queue-sz", "await", "svctm", "%util", "used%", "rxkB/s", "txkB/s"])
            extTable.append(["Ceph", cal_CPU_user_ceph(case), cal_CPU_kenelsoft_ceph(case), cal_CPU_iowait_ceph(case), cal_AVG_IOPS_OSD_r_ceph(case), cal_AVG_IOPS_OSD_w_ceph(case), cal_AVG_IOPS_OSD_rMB_ceph(case), cal_AVG_IOPS_OSD_wMB_ceph(case), cal_AVG_IOPS_OSD_avgrqsz_ceph(case), cal_AVG_IOPS_OSD_avgqusz_ceph(case), cal_AVG_IOPS_OSD_await_ceph(case), cal_AVG_IOPS_OSD_svtcm_ceph(case), cal_AVG_IOPS_OSD_util_ceph(case), cal_Memory_memused_ceph(case), cal_NIC_rxkB_ceph(case), cal_NIC_txkB_ceph(case)])
            extTable.append(["VM", cal_CPU_user_vclient(case), cal_CPU_kenelsoft_vclient(case), cal_CPU_iowait_vclient(case), cal_AVG_IOPS_OSD_r_vclient(case), cal_AVG_IOPS_OSD_w_vclient(case), cal_AVG_IOPS_OSD_rMB_vclient(case), cal_AVG_IOPS_OSD_wMB_vclient(case), cal_AVG_IOPS_OSD_avgrqsz_vclient(case), cal_AVG_IOPS_OSD_avgqusz_vclient(case), cal_AVG_IOPS_OSD_await_vclient(case), cal_AVG_IOPS_OSD_svtcm_vclient(case), cal_AVG_IOPS_OSD_util_vclient(case), cal_Memory_memused_vclient(case), cal_NIC_rxkB_vclient(case), cal_NIC_txkB_vclient(case)])
            extTable.append(["Client", cal_CPU_user_client(case), cal_CPU_kenelsoft_client(case), cal_CPU_iowait_client(case), cal_AVG_IOPS_OSD_r_client(case), cal_AVG_IOPS_OSD_w_client(case), cal_AVG_IOPS_OSD_rMB_client(case), cal_AVG_IOPS_OSD_wMB_client(case), cal_AVG_IOPS_OSD_avgrqsz_client(case), cal_AVG_IOPS_OSD_avgqusz_client(case), cal_AVG_IOPS_OSD_await_client(case), cal_AVG_IOPS_OSD_svtcm_client(case), cal_AVG_IOPS_OSD_util_client(case), cal_Memory_memused_client(case), cal_NIC_rxkB_client(case), cal_NIC_txkB_client(case)])
        result.append(extTable)
    return result
def cal_Throughput_FIO_IOPS_ceph(case):
    global dataObj
    tmpList = []
    if dataObj:
        for key in dataObj["workload"]["fio"]["summary"]:
            tmpList.extend([dataObj["workload"]["fio"]["summary"][key]["read_iops"] + dataObj["workload"]["fio"]["summary"][key]["write_iops"]])
    return sum(tmpList)
def cal_Throughput_FIO_IOPS_client(case):
    pass
def cal_Throughput_FIO_IOPS_vclient(case):
    pass

def cal_Throughput_FIO_BW_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["workload"]["fio"]["summary"]:
            tmpList.extend([dataObj["workload"]["fio"]["summary"][key]["read_bw"] + dataObj["workload"]["fio"]["summary"][key]["write_bw"]])
    return sum(tmpList)
def cal_Throughput_FIO_BW_client(case):
    pass
def cal_Throughput_FIO_BW_vclient(case):
    pass

def cal_Throughput_FIO_Latency_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["workload"]["fio"]["summary"]:
            tmpList.extend([dataObj["workload"]["fio"]["summary"][key]["read_lat"] + dataObj["workload"]["fio"]["summary"][key]["write_lat"]])
    return sum(tmpList)/len(tmpList)
def cal_Throughput_FIO_Latency_client(case):
    pass
def cal_Throughput_FIO_Latency_vclient(case):
    pass

def cal_ThroughputAvg_FIO_IOPS_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["workload"]["fio"]["summary"]:
            tmpList.extend([dataObj["workload"]["fio"]["summary"][key]["read_iops"] + dataObj["workload"]["fio"]["summary"][key]["write_iops"]])
    return sum(tmpList)/len(tmpList)
def cal_ThroughputAvg_FIO_IOPS_client(case):
    pass
def cal_ThroughputAvg_FIO_IOPS_vclient(case):
    pass

def cal_ThroughputAvg_FIO_BW_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["workload"]["fio"]["summary"]:
            tmpList.extend([dataObj["workload"]["fio"]["summary"][key]["read_bw"] + dataObj["workload"]["fio"]["summary"][key]["write_bw"]])
    return sum(tmpList)/len(tmpList)
def cal_ThroughputAvg_FIO_BW_client(case):
    pass
def cal_ThroughputAvg_FIO_BW_vclient(case):
    pass

def cal_ThroughputAvg_FIO_Latency_ceph(case):
    pass
def cal_ThroughputAvg_FIO_Latency_client(case):
    pass
def cal_ThroughputAvg_FIO_Latency_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["workload"]["fio"]["summary"]:
            tmpList.extend([dataObj["workload"]["fio"]["summary"][key]["read_lat"] + dataObj["workload"]["fio"]["summary"][key]["write_lat"]])
    return sum(tmpList)/len(tmpList)

def cal_CPU_user_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["cpu"]["summary"]:
            tmpList.extend(dataObj["ceph"]["cpu"]["summary"][key]["%usr"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_user_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%usr"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_user_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%usr"])
    return sum(tmpList)/len(tmpList)

def cal_CPU_kernel_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["cpu"]["summary"]:
            tmpList.extend(dataObj["ceph"]["cpu"]["summary"][key]["%sys"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_kernel_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%sys"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_kernel_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%sys"])
    return sum(tmpList)/len(tmpList)
    
def cal_CPU_iowait_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["cpu"]["summary"]:
            tmpList.extend(dataObj["ceph"]["cpu"]["summary"][key]["%iowait"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_iowait_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%iowait"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_iowait_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%iowait"])
    return sum(tmpList)/len(tmpList)
    
def cal_CPU_soft_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["cpu"]["summary"]:
            tmpList.extend(dataObj["ceph"]["cpu"]["summary"][key]["%soft"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_soft_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%soft"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_soft_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%soft"])
    return sum(tmpList)/len(tmpList)
    
def cal_CPU_idle_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["cpu"]["summary"]:
            tmpList.extend(dataObj["ceph"]["cpu"]["summary"][key]["%idle"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_idle_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%idle"])
    return sum(tmpList)/len(tmpList)
def cal_CPU_idle_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["cpu"]["summary"]:
            tmpList.extend(dataObj["client"]["cpu"]["summary"][key]["%idle"])
    return sum(tmpList)/len(tmpList)

def cal_CPU_kenelsoft_ceph(case):
    return cal_CPU_kernel_ceph(case) + cal_CPU_soft_ceph(case)
def cal_CPU_kenelsoft_vclient(case):
    return cal_CPU_kernel_vclient(case) + cal_CPU_soft_vclient(case)
def cal_CPU_kenelsoft_client(case):
    return cal_CPU_kernel_client(case) + cal_CPU_soft_client(case)

def cal_AVG_IOPS_Journal_r_ceph(case):
    pass
def cal_AVG_IOPS_Journal_r_client(case):
    pass
def cal_AVG_IOPS_Journal_r_vclient(case):
    pass

def cal_AVG_IOPS_Journal_w_ceph(case):
    pass
def cal_AVG_IOPS_Journal_w_client(case):
    pass
def cal_AVG_IOPS_Journal_w_vclient(case):
    pass

def cal_AVG_IOPS_Journal_rMB_ceph(case):
    pass
def cal_AVG_IOPS_Journal_rMB_client(case):
    pass
def cal_AVG_IOPS_Journal_rMB_vclient(case):
    pass

def cal_AVG_IOPS_Journal_wMB_ceph(case):
    pass
def cal_AVG_IOPS_Journal_wMB_client(case):
    pass
def cal_AVG_IOPS_Journal_wMB_vclient(case):
    pass

def cal_AVG_IOPS_Journal_avgrqsz_ceph(case):
    pass
def cal_AVG_IOPS_Journal_avgrqsz_client(case):
    pass
def cal_AVG_IOPS_Journal_avgrqsz_vclient(case):
    pass

def cal_AVG_IOPS_Journal_avgqusz_ceph(case):
    pass
def cal_AVG_IOPS_Journal_avgqusz_client(case):
    pass
def cal_AVG_IOPS_Journal_avgqusz_vclient(case):
    pass

def cal_AVG_IOPS_Journal_await_ceph(case):
    pass
def cal_AVG_IOPS_Journal_await_client(case):
    pass
def cal_AVG_IOPS_Journal_await_vclient(case):
    pass

def cal_AVG_IOPS_Journal_svtcm_ceph(case):
    pass
def cal_AVG_IOPS_Journal_svtcm_client(case):
    pass
def cal_AVG_IOPS_Journal_svtcm_vclient(case):
    pass

def cal_AVG_IOPS_Journal_util_ceph(case):
    pass
def cal_AVG_IOPS_Journal_util_client(case):
    pass
def cal_AVG_IOPS_Journal_util_vclient(case):
    pass

def cal_AVG_IOPS_OSD_r_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["r/s"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_r_client(case):
    pass
def cal_AVG_IOPS_OSD_r_vclient(case):
    pass

def cal_AVG_IOPS_OSD_w_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["w/s"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_w_client(case):
    pass
def cal_AVG_IOPS_OSD_w_vclient(case):
    pass

def cal_AVG_IOPS_OSD_rMB_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["rMB/s"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_rMB_client(case):
    pass
def cal_AVG_IOPS_OSD_rMB_vclient(case):
    pass

def cal_AVG_IOPS_OSD_wMB_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["wMB/s"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_wMB_client(case):
    pass
def cal_AVG_IOPS_OSD_wMB_vclient(case):
    pass

def cal_AVG_IOPS_OSD_avgrqsz_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["avgrq-sz"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_avgrqsz_client(case):
    pass
def cal_AVG_IOPS_OSD_avgrqsz_vclient(case):
    pass

def cal_AVG_IOPS_OSD_avgqusz_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["avgqu-sz"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_avgqusz_client(case):
    pass
def cal_AVG_IOPS_OSD_avgqusz_vclient(case):
    pass

def cal_AVG_IOPS_OSD_await_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["await"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_await_client(case):
    pass
def cal_AVG_IOPS_OSD_await_vclient(case):
    pass

def cal_AVG_IOPS_OSD_svtcm_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["svctm"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_svtcm_client(case):
    pass
def cal_AVG_IOPS_OSD_svtcm_vclient(case):
    pass

def cal_AVG_IOPS_OSD_util_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["osd"]["summary"]:
            tmpList.extend(dataObj["ceph"]["osd"]["summary"][key]["%util"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_OSD_util_client(case):
    pass
def cal_AVG_IOPS_OSD_util_vclient(case):
    pass

def cal_AVG_IOPS_WAL_r_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["r/s"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["r/s"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_r_client(case):
    pass
def cal_AVG_IOPS_WAL_r_vclient(case):
    pass

def cal_AVG_IOPS_WAL_w_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["w/s"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["w/s"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_w_client(case):
    pass
def cal_AVG_IOPS_WAL_w_vclient(case):
    pass

def cal_AVG_IOPS_WAL_rMB_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["rMB/s"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["rMB/s"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_rMB_client(case):
    pass
def cal_AVG_IOPS_WAL_rMB_vclient(case):
    pass

def cal_AVG_IOPS_WAL_wMB_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["wMB/s"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["wMB/s"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_wMB_client(case):
    pass
def cal_AVG_IOPS_WAL_wMB_vclient(case):
    pass

def cal_AVG_IOPS_WAL_avgrqsz_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["avgrq-sz"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["avgrq-sz"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_avgrqsz_client(case):
    pass
def cal_AVG_IOPS_WAL_avgrqsz_vclient(case):
    pass

def cal_AVG_IOPS_WAL_avgqusz_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["avgqu-sz"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["avgqu-sz"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_avgqusz_client(case):
    pass
def cal_AVG_IOPS_WAL_avgqusz_vclient(case):
    pass

def cal_AVG_IOPS_WAL_await_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["await"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["await"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_await_client(case):
    pass
def cal_AVG_IOPS_WAL_await_vclient(case):
    pass

def cal_AVG_IOPS_WAL_svtcm_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["svctm"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["svctm"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_svtcm_client(case):
    pass
def cal_AVG_IOPS_WAL_svtcm_vclient(case):
    pass

def cal_AVG_IOPS_WAL_util_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["wal"]["summary"]:
            tmpList.extend(dataObj["ceph"]["wal"]["summary"][key]["%util"])
        for key in dataObj["ceph"]["db"]["summary"]:
            tmpList.extend(dataObj["ceph"]["db"]["summary"][key]["%util"])
    return sum(tmpList)/len(tmpList)
def cal_AVG_IOPS_WAL_util_client(case):
    pass
def cal_AVG_IOPS_WAL_util_vclient(case):
    pass

def cal_Memory_kbmemfree_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["memory"]["summary"]:
            tmpList.extend(dataObj["ceph"]["memory"]["summary"][key]["kbmenfree"])
    return sum(tmpList)/len(tmpList)
def cal_Memory_kbmemfree_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["memory"]["summary"]:
            tmpList.extend(dataObj["client"]["memory"]["summary"][key]["kbmenfree"])
    return sum(tmpList)/len(tmpList)
def cal_Memory_kbmemfree_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["memory"]["summary"]:
            tmpList.extend(dataObj["client"]["memory"]["summary"][key]["kbmenfree"])
    return sum(tmpList)/len(tmpList)

def cal_Memory_kbmemused_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["memory"]["summary"]:
            tmpList.extend(dataObj["ceph"]["memory"]["summary"][key]["kbmemused"])
    return sum(tmpList)/len(tmpList)
def cal_Memory_kbmemused_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["memory"]["summary"]:
            tmpList.extend(dataObj["client"]["memory"]["summary"][key]["kbmemused"])
    return sum(tmpList)/len(tmpList)
def cal_Memory_kbmemused_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["memory"]["summary"]:
            tmpList.extend(dataObj["client"]["memory"]["summary"][key]["kbmemused"])
    return sum(tmpList)/len(tmpList)

def cal_Memory_memused_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["memory"]["summary"]:
            tmpList.extend(dataObj["ceph"]["memory"]["summary"][key]["%memused"])
    return sum(tmpList)/len(tmpList)
def cal_Memory_memused_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["memory"]["summary"]:
            tmpList.extend(dataObj["client"]["memory"]["summary"][key]["%memused"])
    return sum(tmpList)/len(tmpList)
def cal_Memory_memused_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["memory"]["summary"]:
            tmpList.extend(dataObj["client"]["memory"]["summary"][key]["%memused"])
    return sum(tmpList)/len(tmpList)

def cal_NIC_rxpck_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["nic"]["summary"]:
            tmpList.extend(dataObj["ceph"]["nic"]["summary"][key]["rxpck/s"])
    return sum(tmpList)/len(tmpList)
def cal_NIC_rxpck_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["nic"]["summary"]:
            tmpList.extend(dataObj["client"]["nic"]["summary"][key]["rxpck/s"])
    return sum(tmpList)/len(tmpList)
def cal_NIC_rxpck_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["nic"]["summary"]:
            tmpList.extend(dataObj["client"]["nic"]["summary"][key]["rxpck/s"])
    return sum(tmpList)/len(tmpList)

def cal_NIC_txpck_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["nic"]["summary"]:
            tmpList.extend(dataObj["ceph"]["nic"]["summary"][key]["txpck/s"])
    return sum(tmpList)/len(tmpList)
def cal_NIC_txpck_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["nic"]["summary"]:
            tmpList.extend(dataObj["client"]["nic"]["summary"][key]["txpck/s"])
    return sum(tmpList)/len(tmpList)
def cal_NIC_txpck_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["nic"]["summary"]:
            tmpList.extend(dataObj["client"]["nic"]["summary"][key]["txpck/s"])
    return sum(tmpList)/len(tmpList)

def cal_NIC_rxkB_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["nic"]["summary"]:
            tmpList.extend(dataObj["ceph"]["nic"]["summary"][key]["rxkB/s"])
    return sum(tmpList)/len(tmpList)
def cal_NIC_rxkB_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["nic"]["summary"]:
            tmpList.extend(dataObj["client"]["nic"]["summary"][key]["rxkB/s"])
    return sum(tmpList)/len(tmpList)
def cal_NIC_rxkB_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["nic"]["summary"]:
            tmpList.extend(dataObj["client"]["nic"]["summary"][key]["rxkB/s"])
    return sum(tmpList)/len(tmpList)

def cal_NIC_txkB_ceph(case):
    tmpList = []
    if dataObj:
        for key in dataObj["ceph"]["nic"]["summary"]:
            tmpList.extend(dataObj["ceph"]["nic"]["summary"][key]["txkB/s"])
    return sum(tmpList)/len(tmpList)
def cal_NIC_txkB_client(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["nic"]["summary"]:
            tmpList.extend(dataObj["client"]["nic"]["summary"][key]["txkB/s"])
    return sum(tmpList)/len(tmpList)
def cal_NIC_txkB_vclient(case):
    tmpList = []
    if dataObj:
        for key in dataObj["client"]["nic"]["summary"]:
            tmpList.extend(dataObj["client"]["nic"]["summary"][key]["txkB/s"])
    return sum(tmpList)/len(tmpList)


def GenExcelFile(eTables, extTables, caseNum):
    dataFile = xlsxwriter.Workbook('summray.xls')
    dataSheet = dataFile.add_worksheet(u'summary')
    for i,eRow in enumerate(eTables):
        for j,eCol in enumerate(eRow):
            if i == 0 and j > 0:
                dataSheet.merge_range(i, 3*j-2, i, 3*j, eCol.split("/")[-1], set_style(dataFile, 'title'))
            else:
                if type(eCol) == list:
                    dataSheet.write(i, j, eCol[0], set_style(dataFile,eCol[1]))
                else:
                    dataSheet.write(i, j, eCol, set_style(dataFile,""))
    
    i += 2
    dataSheet.merge_range(i, 0, i, 5, "general info", set_style(dataFile, "title"))
    i += 1
    dataSheet.merge_range(i, 0, i, 5, "runcase", set_style(dataFile, "title"))
    i += 1
    ei = i
    chartList = []
    for extTable in extTables:
        chartList.append(ei)
        ej = 0
        for extRow in extTable:
            ei = i            
            for extCol in extRow:
                if type(extCol) == list:
                    if extCol[1] > 1:
                        dataSheet.merge_range(ei, ej, ei+extCol[1]-1, ej, extCol[0], set_style(dataFile, extCol[2]))
                    else:
                        dataSheet.write(ei, ej, extCol[0], set_style(dataFile, extCol[2]))
                    ei = ei+extCol[1]
                else:
                    dataSheet.write(ei, ej, extCol, set_style(dataFile, ''))
                    ei += 1
            ej += 1
        i = ei + 1
        dataSheet.merge_range(ei, 0, ei, 5, "", set_style(dataFile, ''))

    
    for ci in chartList:
        tmpChart = dataFile.add_chart({'type': 'column'})
        tmpChart.add_series({
            'name': ['summary', ci, 0],
            'categories': ['summary', ci, 3, ci, 5],
            'values': ['summary', ci+1, 3, ci+3, 5],
            'data_labels': {'value': True},
        })
        tmpChart.set_title ({'name': 'Results of sample analysis'})
        tmpChart.set_x_axis({'name': 'Test number'})
        tmpChart.set_y_axis({'name': 'Sample length (mm)'})
        dataSheet.insert_chart(ci, 6, tmpChart, {'x_offset': 10, 'y_offset': 0})
       
    for k in range(3*caseNum + 1):
        dataSheet.set_column(k, k, 18)

    dataFile.close()

def set_style(fileObj, name):
    titleStyle = fileObj.add_format({'bold': True, 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 1})
    subtitleStyle = fileObj.add_format({'bold': True, 'font_color': 'red', 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 1})
    sstitleStyle = fileObj.add_format({'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 1})
    rtitleStyle = fileObj.add_format({'bold': True, 'font_color': 'red', 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 1})
    contentStyle = fileObj.add_format({'bottom': 1, 'top': 1, 'left': 1, 'right': 1})
    
    if name == "title":
        return titleStyle
    elif name == "subtitle":
        return subtitleStyle
    elif name == "sstitle":
        return sstitleStyle
    elif name == "rtitle":
        return rtitleStyle
    else:
        return contentStyle
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="data path")
    cases = parser.parse_args().split(",")
    eTables = GetETables(cases, "fileStore")
    extTables = GetExtTables(cases, "fileStore")
    GenExcelFile(eTables, extTables, len(cases))