import os
import math
import json
import xlwt
import argparse

def do(path):
    dataPath = os.path.join(path, "result.json")
    if os.path.exists(dataPath):
        oName = "summary_" + "-".join(dataPath.split("-")[0:2]) + ".xls"
        with open(dataPath) as dataFile:
            jsonObj = json.load(dataFile)
            GenExcel(jsonObj, oName)
    else:
        print "file %s not exists!" % (dataPath)

def GenExcel(jsonObj, oName):
    f = xlwt.Workbook()
    sheet1 = f.add_sheet(u'sheet1',cell_overwrite_ok=True)
    tarList = [["runcase", jsonObj["session_name"]], ["", "Workloads", "OSD", "Client"]]
    
    ############### Throughput/Throughput_avg ####################
    tarList.append(["Throughput", ""])
    fio_iopsList = []
    fio_bwList = []
    fio_latencyList = []
    for obj in jsonObj["workload"]["fio"]["summary"]:
        fio_iopsList.extend([jsonObj["workload"]["fio"]["summary"][obj]["read_iops"] + jsonObj["workload"]["fio"]["summary"][obj]["write_iops"]])
        fio_bwList.extend([jsonObj["workload"]["fio"]["summary"][obj]["read_bw"] + jsonObj["workload"]["fio"]["summary"][obj]["write_bw"]])
        fio_latencyList.extend([jsonObj["workload"]["fio"]["summary"][obj]["read_lat"] + jsonObj["workload"]["fio"]["summary"][obj]["write_lat"]])
    fio_iops = sum(fio_iopsList)
    fio_bw = sum(fio_bwList)
    fio_latency = sum(fio_latencyList)
    
    fio_iops_avg = sum(fio_iopsList)/len(fio_iopsList)
    fio_bw_avg = sum(fio_bwList)/len(fio_bwList)
    fio_latency_avg = sum(fio_latencyList)/len(fio_latencyList)
    
    tarList.append(["FIO_IOPS", "", "", fio_iops])
    tarList.append(["FIO_BW", "", "", fio_bw])
    tarList.append(["FIO_Latency", "", "", fio_latency_avg])
    
    tarList.append(["Throughput_avg", ""])    
    tarList.append(["FIO_IOPS", "", "", fio_iops_avg])
    tarList.append(["FIO_BW", "", "", fio_bw_avg])
    tarList.append(["FIO_Latency", "", "", fio_latency_avg])
    ######################################
    
    
    ############### CPU ####################
    tarList.append(["CPU", ""])
    ceph_userList = []
    ceph_sysList = []
    ceph_iowaitList = []
    ceph_softList = []
    ceph_idleList = []
    for obj in jsonObj["ceph"]["cpu"]["summary"]:
        ceph_userList.extend(jsonObj["ceph"]["cpu"]["summary"][obj]["%usr"])
        ceph_sysList.extend(jsonObj["ceph"]["cpu"]["summary"][obj]["%sys"])
        ceph_iowaitList.extend(jsonObj["ceph"]["cpu"]["summary"][obj]["%iowait"])
        ceph_softList.extend(jsonObj["ceph"]["cpu"]["summary"][obj]["%soft"])
        ceph_idleList.extend(jsonObj["ceph"]["cpu"]["summary"][obj]["%idle"])        
    ceph_user_avg = sum(ceph_userList)/len(ceph_userList)
    ceph_sys_avg = sum(ceph_sysList)/len(ceph_sysList)
    ceph_iowait_avg = sum(ceph_iowaitList)/len(ceph_iowaitList)
    ceph_soft_avg = sum(ceph_softList)/len(ceph_softList)
    ceph_idle_avg = sum(ceph_idleList)/len(ceph_idleList)
    
    client_userList = []
    client_sysList = []
    client_iowaitList = []
    client_softList = []
    client_idleList = []
    for obj in jsonObj["client"]["cpu"]["summary"]:
        client_userList.extend(jsonObj["client"]["cpu"]["summary"][obj]["%usr"])
        client_sysList.extend(jsonObj["client"]["cpu"]["summary"][obj]["%sys"])
        client_iowaitList.extend(jsonObj["client"]["cpu"]["summary"][obj]["%iowait"])
        client_softList.extend(jsonObj["client"]["cpu"]["summary"][obj]["%soft"])
        client_idleList.extend(jsonObj["client"]["cpu"]["summary"][obj]["%idle"])
        
    client_user_avg = sum(client_userList)/len(client_userList)
    client_sys_avg = sum(client_sysList)/len(client_sysList)
    client_iowait_avg = sum(client_iowaitList)/len(client_iowaitList)
    client_soft_avg = sum(client_softList)/len(client_softList)
    client_idle_avg = sum(client_idleList)/len(client_idleList)
    tarList.append(["sar all user%", "", ceph_user_avg, client_user_avg])
    tarList.append(["sar all kernel%", "", ceph_sys_avg, client_sys_avg])
    tarList.append(["sar all iowait%", "", ceph_iowait_avg, client_iowait_avg])
    tarList.append(["sar all soft%", "", ceph_soft_avg, client_soft_avg])
    tarList.append(["sar all idle%", "", ceph_idle_avg, client_idle_avg])
    ######################################
    
    ############### MEM ####################
    tarList.append(["Memory", ""])
    ceph_kbmemfreeList = []
    ceph_kbmemusedList = []
    ceph_memusedList = []
    for obj in jsonObj["ceph"]["memory"]["summary"]:
        ceph_kbmemfreeList.extend(jsonObj["ceph"]["memory"]["summary"][obj]["kbmenfree"])
        ceph_kbmemusedList.extend(jsonObj["ceph"]["memory"]["summary"][obj]["kbmemused"])
        ceph_memusedList.extend(jsonObj["ceph"]["memory"]["summary"][obj]["%memused"])
    ceph_kbmemfree_avg = sum(ceph_kbmemfreeList)/len(ceph_kbmemfreeList)
    ceph_kbmemused_avg = sum(ceph_kbmemusedList)/len(ceph_kbmemusedList)
    ceph_memused_avg = sum(ceph_memusedList)/len(ceph_memusedList)
    
    client_kbmemfreeList = []
    client_kbmemusedList = []
    client_memusedList = []
    for obj in jsonObj["client"]["memory"]["summary"]:
        client_kbmemfreeList.extend(jsonObj["client"]["memory"]["summary"][obj]["kbmenfree"])
        client_kbmemusedList.extend(jsonObj["client"]["memory"]["summary"][obj]["kbmemused"])
        client_memusedList.extend(jsonObj["client"]["memory"]["summary"][obj]["%memused"])
    client_kbmemfree_avg = sum(client_kbmemfreeList)/len(client_kbmemfreeList)
    client_kbmemused_avg = sum(client_kbmemusedList)/len(client_kbmemusedList)
    client_memused_avg = sum(client_memusedList)/len(client_memusedList)
    tarList.append(["kbmemfree", "", ceph_kbmemfree_avg, client_kbmemfree_avg])
    tarList.append(["kbmemused", "", ceph_kbmemused_avg, client_kbmemused_avg])
    tarList.append(["%memused", "", ceph_memused_avg, client_memused_avg])
    ########################################
    
    ############### NIC ####################
    tarList.append(["NIC", ""])
    ceph_rxpckList = []
    ceph_txpckList = []
    ceph_rxkBList = []
    ceph_txkBList = []
    for obj in jsonObj["ceph"]["nic"]["summary"]:
        ceph_rxpckList.extend(jsonObj["ceph"]["nic"]["summary"][obj]["rxpck/s"])
        ceph_txpckList.extend(jsonObj["ceph"]["nic"]["summary"][obj]["txpck/s"])
        ceph_rxkBList.extend(jsonObj["ceph"]["nic"]["summary"][obj]["rxkB/s"])
        ceph_txkBList.extend(jsonObj["ceph"]["nic"]["summary"][obj]["txkB/s"])
    ceph_rxpck_avg = sum(ceph_rxpckList)/len(ceph_rxpckList)
    ceph_txpck_avg = sum(ceph_txpckList)/len(ceph_txpckList)
    ceph_rxkB_avg = sum(ceph_rxkBList)/len(ceph_rxkBList)
    ceph_txkB_avg = sum(ceph_txkBList)/len(ceph_txkBList)
    
    client_rxpckList = []
    client_txpckList = []
    client_rxkBList = []
    client_txkBList = []
    for obj in jsonObj["client"]["nic"]["summary"]:
        client_rxpckList.extend(jsonObj["client"]["nic"]["summary"][obj]["rxpck/s"])
        client_txpckList.extend(jsonObj["client"]["nic"]["summary"][obj]["txpck/s"])
        client_rxkBList.extend(jsonObj["client"]["nic"]["summary"][obj]["rxkB/s"])
        client_txkBList.extend(jsonObj["client"]["nic"]["summary"][obj]["txkB/s"])
    client_rxpck_avg = sum(client_rxpckList)/len(client_rxpckList)
    client_txpck_avg = sum(client_txpckList)/len(client_txpckList)
    client_rxkB_avg = sum(client_rxkBList)/len(client_rxkBList)
    client_txkB_avg = sum(client_txkBList)/len(client_txkBList)
    tarList.append(["rxpck/s", "", ceph_rxpck_avg, client_rxpck_avg])
    tarList.append(["txpck/s", "", ceph_txpck_avg, client_txpck_avg])
    tarList.append(["rxkB/s", "", ceph_rxkB_avg, client_rxkB_avg])
    tarList.append(["txkB/s", "", ceph_txkB_avg, client_txkB_avg])
    ######################################
    
    ############### WAL & DB ####################
    tarList.append(["AVG_IOPS_WAL & DB", ""])
    wal_rList = []
    wal_wList = []
    wal_rMBList = []
    wal_wMBList = []
    wal_avgrq_szList = []
    wal_avgqu_szList = []
    wal_awaitList = []
    wal_svctmList = []
    wal_utilList = []
    for obj in jsonObj["ceph"]["wal"]["summary"]:
        wal_rList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["r/s"])
        wal_wList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["w/s"])
        wal_rMBList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["rMB/s"])
        wal_wMBList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["wMB/s"])
        wal_avgrq_szList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["avgrq-sz"])
        wal_avgqu_szList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["avgqu-sz"])
        wal_awaitList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["await"])
        wal_svctmList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["svctm"])
        wal_utilList.extend(jsonObj["ceph"]["wal"]["summary"][obj]["%util"])
    
    db_rList = []
    db_wList = []
    db_rMBList = []
    db_wMBList = []
    db_avgrq_szList = []
    db_avgqu_szList = []
    db_awaitList = []
    db_svctmList = []
    db_utilList = []
    for obj in jsonObj["ceph"]["db"]["summary"]:
        db_rList.extend(jsonObj["ceph"]["db"]["summary"][obj]["r/s"])
        db_wList.extend(jsonObj["ceph"]["db"]["summary"][obj]["w/s"])
        db_rMBList.extend(jsonObj["ceph"]["db"]["summary"][obj]["rMB/s"])
        db_wMBList.extend(jsonObj["ceph"]["db"]["summary"][obj]["wMB/s"])
        db_avgrq_szList.extend(jsonObj["ceph"]["db"]["summary"][obj]["avgrq-sz"])
        db_avgqu_szList.extend(jsonObj["ceph"]["db"]["summary"][obj]["avgqu-sz"])
        db_awaitList.extend(jsonObj["ceph"]["db"]["summary"][obj]["await"])
        db_svctmList.extend(jsonObj["ceph"]["db"]["summary"][obj]["svctm"])
        db_utilList.extend(jsonObj["ceph"]["db"]["summary"][obj]["%util"])
        
    r_avg = sum(wal_rList + db_rList)/len(wal_rList + db_rList)
    w_avg = sum(wal_wList + db_wList)/len(wal_wList + db_wList)
    rMB_avg = sum(wal_rMBList + db_rMBList)/len(wal_rMBList + db_rMBList)
    wMB_avg = sum(wal_wMBList + db_wMBList)/len(wal_wMBList + db_wMBList)
    avgrq_sz_avg = sum(wal_avgrq_szList + db_avgrq_szList)/len(wal_avgrq_szList + db_avgrq_szList)
    avgqu_sz_avg = sum(wal_avgqu_szList + db_avgqu_szList)/len(wal_avgqu_szList + db_avgqu_szList)
    await_avg = sum(wal_awaitList + db_awaitList)/len(wal_awaitList + db_awaitList)
    svctm_avg = sum(wal_svctmList + db_svctmList)/len(wal_svctmList + db_svctmList)
    util_avg = sum(wal_utilList + db_utilList)/len(wal_utilList + db_utilList)
    
    tarList.append(["r/s", "", r_avg, ""])
    tarList.append(["w/s", "", w_avg, ""])
    tarList.append(["rMB/s", "", rMB_avg, ""])
    tarList.append(["wMB/s", "", wMB_avg, ""])
    tarList.append(["avgrq_sz", "", avgrq_sz_avg, ""])
    tarList.append(["avgqu_sz", "", avgqu_sz_avg, ""])
    tarList.append(["await", "", await_avg, ""])
    tarList.append(["svtcm", "", svctm_avg, ""])
    tarList.append(["%util", "", util_avg, ""])
    ######################################
    
    ############### OSD ####################
    tarList.append(["AVG_IOPS_OSD", ""])
    osd_rList = []
    osd_wList = []
    osd_rMBList = []
    osd_wMBList = []
    osd_avgrq_szList = []
    osd_avgqu_szList = []
    osd_awaitList = []
    osd_svctmList = []
    osd_utilList = []
    for obj in jsonObj["ceph"]["osd"]["summary"]:
        osd_rList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["r/s"])
        osd_wList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["w/s"])
        osd_rMBList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["rMB/s"])
        osd_wMBList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["wMB/s"])
        osd_avgrq_szList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["avgrq-sz"])
        osd_avgqu_szList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["avgqu-sz"])
        osd_awaitList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["await"])
        osd_svctmList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["svctm"])
        osd_utilList.extend(jsonObj["ceph"]["osd"]["summary"][obj]["%util"])
        
    osd_r_avg = sum(osd_rList)/len(osd_rList)
    osd_w_avg = sum(osd_wList)/len(osd_wList)
    osd_rMB_avg = sum(osd_rMBList)/len(osd_rMBList)
    osd_wMB_avg = sum(osd_wMBList)/len(osd_wMBList)
    osd_avgrq_sz_avg = sum(osd_avgrq_szList)/len(osd_avgrq_szList)
    osd_avgqu_sz_avg = sum(osd_avgqu_szList)/len(osd_avgqu_szList)
    osd_await_avg = sum(osd_awaitList)/len(osd_awaitList)
    osd_svctm_avg = sum(osd_svctmList)/len(osd_svctmList)
    osd_util_avg = sum(osd_utilList)/len(osd_utilList)

    
    tarList.append(["r/s", "", osd_r_avg, ""])
    tarList.append(["w/s", "", osd_w_avg, ""])
    tarList.append(["rMB/s", "", osd_rMB_avg, ""])
    tarList.append(["wMB/s", "", osd_wMB_avg, ""])
    tarList.append(["avgrq_sz", "", osd_avgrq_sz_avg, ""])
    tarList.append(["avgqu_sz", "", osd_avgqu_sz_avg, ""])
    tarList.append(["await", "", osd_await_avg, ""])
    tarList.append(["svtcm", "", osd_svctm_avg, ""])
    tarList.append(["%util", "", osd_util_avg, ""])
    ######################################
    
    for ri in range(len(tarList)):
        for ci in range(len(tarList[ri])):
            isSetBG = True if len(tarList[ri]) < 4 else False
            if ci == (len(tarList[ri]) - 1) and len(tarList[ri]) < 4:
                sheet1.write_merge(ri,ri,ci,3,tarList[ri][ci],set_style('Times New Roman',220,True,isSetBG))
            else:
                sheet1.write(ri,ci,tarList[ri][ci],set_style('Times New Roman',220,True,isSetBG))
    col1=sheet1.col(0)
    col2=sheet1.col(1)
    col3=sheet1.col(2)
    col4=sheet1.col(3)
    col1.width = 256*22
    col2.width = 256*20
    col3.width = 256*20
    col4.width = 256*20
    f.save(oName)
    
def set_style(name,height,bold=False,isSetBG=False):
    titleStyle = xlwt.easyxf('pattern: pattern solid, fore_colour pale_blue; font: bold on; borders: left 1, right 1, top 1, bottom 1;')
    contentStyle = xlwt.easyxf('pattern: pattern solid, fore_colour white; borders: left 1, right 1, top 1, bottom 1;')
    if isSetBG:
        return titleStyle
    else:
        return contentStyle

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="data path")
    args = parser.parse_args()
    do(args.path)

