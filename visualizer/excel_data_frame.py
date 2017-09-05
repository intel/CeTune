import os
import json

def get_float(value):
    try:
        if isinstance(value, list):
            return float(value[0])
        else:
            return float(value)
    except:
        return 0

class ExcelDataFrame:
    def __init__(self, cases, storeType, benchType):
        self.cases = {}
        for case in cases:
            self.cases[case] = self.GetDataObj(case)
        self.storeType = storeType
        self.benchmark_type = benchType

    def GetDataObj(self, case):
        dataPath = os.path.join(case, "result.json")
        if os.path.exists(dataPath):
            with open(dataPath) as dataFile:
                return json.load(dataFile)

    def GetDataObjByRunid(self, basepath, runid):
        dataObj = {}
        if os.path.exists(basepath):
            for case in os.listdir(basepath):
                if case.startswith(str(runid) + "-"):
                    dataPath = os.path.join(basepath, case, "result.json")
                    if os.path.exists(dataPath):
                        with open(dataPath) as dataFile:
                            dataObj = json.load(dataFile)
                    break
        return dataObj

    def GetExcelData(self, basepath, volume_runids, pd_runids):
        e_table_data = self.GetETables()
        if basepath and volume_runids and pd_runids:
            return [e_table_data, self.GetExtTables(e_table_data), self.GetScalingTables("volume", basepath, volume_runids), self.GetScalingTables("pd", basepath, pd_runids)]
        else:
            return [e_table_data, self.GetExtTables(e_table_data), [], []]

    def GetETables(self):
        eTables = [[["runcase", "title"]],
                  [""],
                  [["Throughput", "subtitle_b"]],
                  [["FIO_IOPS", "sstitle"]],
                  [["FIO_BW", "sstitle"]],
                  [["FIO_Latency", "sstitle"]],
                  [["FIO_Latency_99.99th", "sstitle"]],
                  [["Throughput_avg", "subtitle_b"]],
                  [["FIO_IOPS", "sstitle"]],
                  [["FIO_BW", "sstitle"]],
                  [["CPU", "subtitle_b"]],
                  [["sar all user%", "sstitle"]],
                  [["sar all kernel%", "sstitle"]],
                  [["sar all iowait%", "sstitle"]],
                  [["sar all soft%", "sstitle"]],
                  [["sar all idle%", "sstitle"]],
                  [["DISK_OTHER_AVG", "subtitle_b"]],
                  [["r/s", "sstitle"]],
                  [["w/s", "sstitle"]],
                  [["rMB/s", "sstitle"]],
                  [["wMB/s", "sstitle"]],
                  [["avgrq-sz", "sstitle"]],
                  [["avgqu-sz", "sstitle"]],
                  [["await", "sstitle"]],
                  [["svtcm", "sstitle"]],
                  [["%util", "sstitle"]],
                  [["DISK_OSD_AVG", "subtitle_b"]],
                  [["r/s", "sstitle"]],
                  [["w/s", "sstitle"]],
                  [["rMB/s", "sstitle"]],
                  [["wMB/s", "sstitle"]],
                  [["avgrq-sz", "sstitle"]],
                  [["avgqu-sz", "sstitle"]],
                  [["await", "sstitle"]],
                  [["svtcm", "sstitle"]],
                  [["%util", "sstitle"]],
                  [["Memory", "subtitle_b"]],
                  [["kbmemfree", "sstitle"]],
                  [["kbmemused", "sstitle"]],
                  [["%memused", "sstitle"]],
                  [["NIC", "subtitle_b"]],
                  [["rxpck/s", "sstitle"]],
                  [["txpck/s", "sstitle"]],
                  [["rxkB/s", "sstitle"]],
                  [["txkB/s", "sstitle"]]]
        if self.storeType == "filestore" and self.benchmark_type == "fiorbd":
            for case, case_data in self.cases.items():
                self.dataObj = case_data
                eTables[0].append(case)
                eTables[1].extend(["ceph", "vclient", "client"])
                eTables[2].extend([["from iostat", "rtitle"], ["from FIO", "rtitle"], ["from iostat", "rtitle_b"]])
                eTables[3].extend(["", "", self.cal_Throughput_FIO_IOPS_client(case)])
                eTables[4].extend(["", "", self.cal_Throughput_FIO_BW_client(case)])
                eTables[5].extend(["", "", self.cal_Throughput_FIO_Latency_client(case)])
                eTables[6].extend(["", "", self.cal_Throughput_FIO_Latency_tail_client(case)])
                eTables[7].extend([["", "rtitle"], ["", "rtitle"], ["", "rtitle_b"]])
                eTables[8].extend(["", "", self.cal_ThroughputAvg_FIO_IOPS_client(case)])
                eTables[9].extend(["", "", self.cal_ThroughputAvg_FIO_BW_client(case)])
                eTables[10].extend([["", "rtitle"], ["", "rtitle"], ["", "rtitle_b"]])
                eTables[11].extend([self.cal_CPU_user_ceph(case), "", self.cal_CPU_user_client(case)])
                eTables[12].extend([self.cal_CPU_kernel_ceph(case), "", self.cal_CPU_kernel_client(case)])
                eTables[13].extend([self.cal_CPU_iowait_ceph(case), "", self.cal_CPU_iowait_client(case)])
                eTables[14].extend([self.cal_CPU_soft_ceph(case), "", self.cal_CPU_soft_client(case)])
                eTables[15].extend([self.cal_CPU_idle_ceph(case), "", self.cal_CPU_idle_client(case)])
                eTables[16].extend([["Journal", "rtitle"], ["vclient_iostat", "rtitle"], ["client_iostat", "rtitle_b"]])
                eTables[17].extend([self.cal_AVG_IOPS_Journal_r_ceph(case), "", ""])
                eTables[18].extend([self.cal_AVG_IOPS_Journal_w_ceph(case), "", ""])
                eTables[19].extend([self.cal_AVG_IOPS_Journal_rMB_ceph(case), "", ""])
                eTables[20].extend([self.cal_AVG_IOPS_Journal_wMB_ceph(case), "", ""])
                eTables[21].extend([self.cal_AVG_IOPS_Journal_avgrqsz_ceph(case), "", ""])
                eTables[22].extend([self.cal_AVG_IOPS_Journal_avgqusz_ceph(case), "", ""])
                eTables[23].extend([self.cal_AVG_IOPS_Journal_await_ceph(case), "", ""])
                eTables[24].extend([self.cal_AVG_IOPS_Journal_svtcm_ceph(case), "", ""])
                eTables[25].extend([self.cal_AVG_IOPS_Journal_util_ceph(case), "", ""])
                eTables[26].extend([["Data", "rtitle"], ["vclient_iostat", "rtitle"], ["client_iostat", "rtitle_b"]])
                eTables[27].extend([self.cal_AVG_IOPS_OSD_r_ceph(case), "", ""])
                eTables[28].extend([self.cal_AVG_IOPS_OSD_w_ceph(case), "", ""])
                eTables[29].extend([self.cal_AVG_IOPS_OSD_rMB_ceph(case), "", ""])
                eTables[30].extend([self.cal_AVG_IOPS_OSD_wMB_ceph(case), "", ""])
                eTables[31].extend([self.cal_AVG_IOPS_OSD_avgrqsz_ceph(case), "", ""])
                eTables[32].extend([self.cal_AVG_IOPS_OSD_avgqusz_ceph(case), "", ""])
                eTables[33].extend([self.cal_AVG_IOPS_OSD_await_ceph(case), "", ""])
                eTables[34].extend([self.cal_AVG_IOPS_OSD_svtcm_ceph(case), "", ""])
                eTables[35].extend([self.cal_AVG_IOPS_OSD_util_ceph(case), "", ""])
                eTables[36].extend([["", "rtitle"], ["", "rtitle"], ["", "rtitle_b"]])
                eTables[37].extend([self.cal_Memory_kbmemfree_ceph(case), "", self.cal_Memory_kbmemfree_client(case)])
                eTables[38].extend([self.cal_Memory_kbmemused_ceph(case), "", self.cal_Memory_kbmemused_client(case)])
                eTables[39].extend([self.cal_Memory_memused_ceph(case), "", self.cal_Memory_memused_client(case)])
                eTables[40].extend([["", "rtitle"], ["", "rtitle"], ["", "rtitle_b"]])
                eTables[41].extend([self.cal_NIC_rxpck_ceph(case), "", self.cal_NIC_rxpck_client(case)])
                eTables[42].extend([self.cal_NIC_txpck_ceph(case), "", self.cal_NIC_txpck_client(case)])
                eTables[43].extend([self.cal_NIC_rxkB_ceph(case), "", self.cal_NIC_rxkB_client(case)])
                eTables[44].extend([self.cal_NIC_txkB_ceph(case), "", self.cal_NIC_txkB_client(case)])

        elif self.storeType == "bluestore" and self.benchmark_type == "fiorbd":
            for case, case_data in self.cases.items():
                self.dataObj = case_data
                eTables[0].append(case)
                eTables[1].extend([["ceph", "rtitle"], ["vclient", "rtitle"], ["client", "rtitle_b"]])
                eTables[2].extend([["from iostat", "rtitle"], ["from FIO", "rtitle"], ["from iostat", "rtitle_b"]])
                eTables[3].extend(["", "", self.cal_Throughput_FIO_IOPS_client(case)])
                eTables[4].extend(["", "", self.cal_Throughput_FIO_BW_client(case)])
                eTables[5].extend(["", "", self.cal_Throughput_FIO_Latency_client(case)])
                eTables[6].extend(["", "", self.cal_Throughput_FIO_Latency_tail_client(case)])
                eTables[7].extend([["", "rtitle"], ["", "rtitle"], ["", "rtitle_b"]])
                eTables[8].extend(["", "", self.cal_ThroughputAvg_FIO_IOPS_client(case)])
                eTables[9].extend(["", "", self.cal_ThroughputAvg_FIO_BW_client(case)])
                eTables[10].extend([["", "rtitle"], ["", "rtitle"], ["", "rtitle_b"]])
                eTables[11].extend([self.cal_CPU_user_ceph(case), "", self.cal_CPU_user_client(case)])
                eTables[12].extend([self.cal_CPU_kernel_ceph(case), "", self.cal_CPU_kernel_client(case)])
                eTables[13].extend([self.cal_CPU_iowait_ceph(case), "", self.cal_CPU_iowait_client(case)])
                eTables[14].extend([self.cal_CPU_soft_ceph(case), "", self.cal_CPU_soft_client(case)])
                eTables[15].extend([self.cal_CPU_idle_ceph(case), "", self.cal_CPU_idle_client(case)])
                eTables[16].extend([["WAL&DB", "rtitle"], ["vclient_total", "rtitle"], ["client_total", "rtitle_b"]])
                eTables[17].extend([self.cal_AVG_IOPS_WAL_r_ceph(case), "", ""])
                eTables[18].extend([self.cal_AVG_IOPS_WAL_w_ceph(case), "", ""])
                eTables[19].extend([self.cal_AVG_IOPS_WAL_rMB_ceph(case), "", ""])
                eTables[20].extend([self.cal_AVG_IOPS_WAL_wMB_ceph(case), "", ""])
                eTables[21].extend([self.cal_AVG_IOPS_WAL_avgrqsz_ceph(case), "", ""])
                eTables[22].extend([self.cal_AVG_IOPS_WAL_avgqusz_ceph(case), "", ""])
                eTables[23].extend([self.cal_AVG_IOPS_WAL_await_ceph(case), "", ""])
                eTables[24].extend([self.cal_AVG_IOPS_WAL_svtcm_ceph(case), "", ""])
                eTables[25].extend([self.cal_AVG_IOPS_WAL_util_ceph(case), "", ""])
                eTables[26].extend([["Data", "rtitle"], ["vclient_average", "rtitle"], ["client_average", "rtitle_b"]])
                eTables[27].extend([self.cal_AVG_IOPS_OSD_r_ceph(case), "", ""])
                eTables[28].extend([self.cal_AVG_IOPS_OSD_w_ceph(case), "", ""])
                eTables[29].extend([self.cal_AVG_IOPS_OSD_rMB_ceph(case), "", ""])
                eTables[30].extend([self.cal_AVG_IOPS_OSD_wMB_ceph(case), "", ""])
                eTables[31].extend([self.cal_AVG_IOPS_OSD_avgrqsz_ceph(case), "", ""])
                eTables[32].extend([self.cal_AVG_IOPS_OSD_avgqusz_ceph(case), "", ""])
                eTables[33].extend([self.cal_AVG_IOPS_OSD_await_ceph(case), "", ""])
                eTables[34].extend([self.cal_AVG_IOPS_OSD_svtcm_ceph(case), "", ""])
                eTables[35].extend([self.cal_AVG_IOPS_OSD_util_ceph(case), "", ""])
                eTables[36].extend([["", "rtitle"], ["", "rtitle"], ["", "rtitle_b"]])
                eTables[37].extend([self.cal_Memory_kbmemfree_ceph(case), "", self.cal_Memory_kbmemfree_client(case)])
                eTables[38].extend([self.cal_Memory_kbmemused_ceph(case), "", self.cal_Memory_kbmemused_client(case)])
                eTables[39].extend([self.cal_Memory_memused_ceph(case), "", self.cal_Memory_memused_client(case)])
                eTables[40].extend([["", "rtitle"], ["", "rtitle"], ["", "rtitle_b"]])
                eTables[41].extend([self.cal_NIC_rxpck_ceph(case), "", self.cal_NIC_rxpck_client(case)])
                eTables[42].extend([self.cal_NIC_txpck_ceph(case), "", self.cal_NIC_txpck_client(case)])
                eTables[43].extend([self.cal_NIC_rxkB_ceph(case), "", self.cal_NIC_rxkB_client(case)])
                eTables[44].extend([self.cal_NIC_txkB_ceph(case), "", self.cal_NIC_txkB_client(case)])
        return eTables

    def GetExtTables(self, r_table_data):
        result = []
        tid = 0
        for case, case_data in self.cases.items():
            tmp = case.split("-")
            extTable = [[["%s-%s" % (tmp[0].split('/')[-1], tmp[3]), 25, 'title']],
                        [["", 1, 'title'],
                         ["CPU", 3, 'title'],
                         ["OTHER", 9, 'title'],
                         ["DATA", 9, 'title'],
                         ["Memory", 1, 'title'],
                         ["NIC", 2, 'title']]]
            extTable.append(["",
                             "user%",
                             "kernel%+soft%",
                             "iowait%",
                             "r/s",
                             "w/s",
                             "rMB/s",
                             "wMB/s",
                             "requsz",
                             "queue-sz",
                             "await",
                             "svctm",
                             "%util",
                             "r/s",
                             "w/s",
                             "rMB/s",
                             "wMB/s",
                             "requsz",
                             "queue-sz",
                             "await",
                             "svctm",
                             "%util",
                             "used%",
                             "rxkB/s",
                             "txkB/s"])
            extTable.append(["Ceph",
                    get_float(r_table_data[11][tid + 1]),
                    get_float(r_table_data[12][tid + 1]) + get_float(r_table_data[14][1]),
                    get_float(r_table_data[13][tid + 1]),

                    get_float(r_table_data[17][tid + 1]),
                    get_float(r_table_data[18][tid + 1]),
                    get_float(r_table_data[19][tid + 1]),
                    get_float(r_table_data[20][tid + 1]),
                    get_float(r_table_data[21][tid + 1]),
                    get_float(r_table_data[22][tid + 1]),
                    get_float(r_table_data[23][tid + 1]),
                    get_float(r_table_data[24][tid + 1]),
                    get_float(r_table_data[25][tid + 1]),

                    get_float(r_table_data[27][tid + 1]),
                    get_float(r_table_data[28][tid + 1]),
                    get_float(r_table_data[29][tid + 1]),
                    get_float(r_table_data[30][tid + 1]),
                    get_float(r_table_data[31][tid + 1]),
                    get_float(r_table_data[32][tid + 1]),
                    get_float(r_table_data[33][tid + 1]),
                    get_float(r_table_data[34][tid + 1]),
                    get_float(r_table_data[35][tid + 1]),

                    get_float(r_table_data[39][tid + 1]),

                    get_float(r_table_data[43][tid + 1]),
                    get_float(r_table_data[44][tid + 1])
                    ])
            extTable.append(["VM",
                    get_float(r_table_data[11][tid + 2]),
                    get_float(r_table_data[12][tid + 2]) + get_float(r_table_data[14][2]),
                    get_float(r_table_data[13][tid + 2]),

                    get_float(r_table_data[17][tid + 2]),
                    get_float(r_table_data[18][tid + 2]),
                    get_float(r_table_data[19][tid + 2]),
                    get_float(r_table_data[20][tid + 2]),
                    get_float(r_table_data[21][tid + 2]),
                    get_float(r_table_data[22][tid + 2]),
                    get_float(r_table_data[23][tid + 2]),
                    get_float(r_table_data[24][tid + 2]),
                    get_float(r_table_data[25][tid + 2]),

                    get_float(r_table_data[27][tid + 2]),
                    get_float(r_table_data[28][tid + 2]),
                    get_float(r_table_data[29][tid + 2]),
                    get_float(r_table_data[30][tid + 2]),
                    get_float(r_table_data[31][tid + 2]),
                    get_float(r_table_data[32][tid + 2]),
                    get_float(r_table_data[33][tid + 2]),
                    get_float(r_table_data[34][tid + 2]),
                    get_float(r_table_data[35][tid + 2]),

                    get_float(r_table_data[39][tid + 2]),

                    get_float(r_table_data[43][tid + 2]),
                    get_float(r_table_data[44][tid + 2])
                    ])
            extTable.append(["Client",
                    get_float(r_table_data[11][tid + 3]),
                    get_float(r_table_data[12][tid + 3]) + get_float(r_table_data[14][1]),
                    get_float(r_table_data[13][tid + 3]),

                    get_float(r_table_data[17][tid + 3]),
                    get_float(r_table_data[18][tid + 3]),
                    get_float(r_table_data[19][tid + 3]),
                    get_float(r_table_data[20][tid + 3]),
                    get_float(r_table_data[21][tid + 3]),
                    get_float(r_table_data[22][tid + 3]),
                    get_float(r_table_data[23][tid + 3]),
                    get_float(r_table_data[24][tid + 3]),
                    get_float(r_table_data[25][tid + 3]),

                    get_float(r_table_data[27][tid + 3]),
                    get_float(r_table_data[28][tid + 3]),
                    get_float(r_table_data[29][tid + 3]),
                    get_float(r_table_data[30][tid + 3]),
                    get_float(r_table_data[31][tid + 3]),
                    get_float(r_table_data[32][tid + 3]),
                    get_float(r_table_data[33][tid + 3]),
                    get_float(r_table_data[34][tid + 3]),
                    get_float(r_table_data[35][tid + 3]),

                    get_float(r_table_data[39][tid + 3]),

                    get_float(r_table_data[43][tid + 3]),
                    get_float(r_table_data[44][tid + 3])
                    ])
            result.append(extTable)
            tid += 3
        return result

    def GetScalingTables(self, scalingfield, basepath, runids):
        if scalingfield == "volume":
            scalingTables = [[["qd=64", 0, 6]],
                             [["volume", 0, 1], "", 1, 5, 10, 50, 100],
                             [["Seq_Write_64K", 1, 0], "BW (MB/s)"],
                             ["", "average latency (ms)"],
                             [["Seq_Read_64K", 1, 0], "BW (MB/s)"],
                             ["", "average latency (ms)"],
                             [["Seq_Write_4K", 1, 0], "IOPS"],
                             ["", "average latency (ms)"],
                             [["Seq_Read_4K", 1, 0], "IOPS"],
                             ["", "average latency (ms)"]]

            scalingTables[2].extend([self.cal_BW_ByRunid(basepath, runids[0]),
                                     self.cal_BW_ByRunid(basepath, runids[1]),
                                     self.cal_BW_ByRunid(basepath, runids[2]),
                                     self.cal_BW_ByRunid(basepath, runids[3]),
                                     self.cal_BW_ByRunid(basepath, runids[4])
                                     ])
            scalingTables[3].extend([self.cal_AvgLat_ByRunid(basepath, runids[0]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[1]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[2]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[3]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[4])
                                     ])
            scalingTables[4].extend([self.cal_BW_ByRunid(basepath, runids[5]),
                                     self.cal_BW_ByRunid(basepath, runids[6]),
                                     self.cal_BW_ByRunid(basepath, runids[7]),
                                     self.cal_BW_ByRunid(basepath, runids[8]),
                                     self.cal_BW_ByRunid(basepath, runids[9])
                                     ])
            scalingTables[5].extend([self.cal_AvgLat_ByRunid(basepath, runids[5]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[6]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[7]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[8]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[9])
                                     ])
            scalingTables[6].extend([self.cal_IOPS_ByRunid(basepath, runids[10]),
                                     self.cal_IOPS_ByRunid(basepath, runids[11]),
                                     self.cal_IOPS_ByRunid(basepath, runids[12]),
                                     self.cal_IOPS_ByRunid(basepath, runids[13]),
                                     self.cal_IOPS_ByRunid(basepath, runids[14])
                                     ])
            scalingTables[7].extend([self.cal_AvgLat_ByRunid(basepath, runids[10]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[11]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[12]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[13]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[14])
                                     ])
            scalingTables[8].extend([self.cal_IOPS_ByRunid(basepath, runids[15]),
                                     self.cal_IOPS_ByRunid(basepath, runids[16]),
                                     self.cal_IOPS_ByRunid(basepath, runids[17]),
                                     self.cal_IOPS_ByRunid(basepath, runids[18]),
                                     self.cal_IOPS_ByRunid(basepath, runids[19])
                                     ])
            scalingTables[9].extend([self.cal_AvgLat_ByRunid(basepath, runids[15]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[16]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[17]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[18]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[19])
                                     ])
        elif scalingfield == "pd":
            scalingTables = [[["volume=100", 0, 9]],
                             [["QD", 0, 1], "", 1, 2, 4, 8, 16, 32, 64, 128],
                             [["Seq_Write_64K", 1, 0], "BW (MB/s)"],
                             ["", "average latency (ms)"],
                             [["Seq_Read_64K", 1, 0], "BW (MB/s)"],
                             ["", "average latency (ms)"],
                             [["Seq_Write_4K", 1, 0], "IOPS"],
                             ["", "average latency (ms)"],
                             [["Seq_Read_4K", 1, 0], "IOPS"],
                             ["", "average latency (ms)"]]

            scalingTables[2].extend([self.cal_BW_ByRunid(basepath, runids[0]),
                                     self.cal_BW_ByRunid(basepath, runids[1]),
                                     self.cal_BW_ByRunid(basepath, runids[2]),
                                     self.cal_BW_ByRunid(basepath, runids[3]),
                                     self.cal_BW_ByRunid(basepath, runids[4]),
                                     self.cal_BW_ByRunid(basepath, runids[5]),
                                     self.cal_BW_ByRunid(basepath, runids[6]),
                                     self.cal_BW_ByRunid(basepath, runids[7])
                                     ])
            scalingTables[3].extend([self.cal_AvgLat_ByRunid(basepath, runids[0]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[1]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[2]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[3]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[4]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[5]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[6]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[7])
                                     ])
            scalingTables[4].extend([self.cal_BW_ByRunid(basepath, runids[8]),
                                     self.cal_BW_ByRunid(basepath, runids[9]),
                                     self.cal_BW_ByRunid(basepath, runids[10]),
                                     self.cal_BW_ByRunid(basepath, runids[11]),
                                     self.cal_BW_ByRunid(basepath, runids[12]),
                                     self.cal_BW_ByRunid(basepath, runids[13]),
                                     self.cal_BW_ByRunid(basepath, runids[14]),
                                     self.cal_BW_ByRunid(basepath, runids[15])
                                     ])
            scalingTables[5].extend([self.cal_AvgLat_ByRunid(basepath, runids[8]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[9]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[10]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[11]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[12]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[13]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[14]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[15])
                                     ])
            scalingTables[6].extend([self.cal_IOPS_ByRunid(basepath, runids[16]),
                                     self.cal_IOPS_ByRunid(basepath, runids[17]),
                                     self.cal_IOPS_ByRunid(basepath, runids[18]),
                                     self.cal_IOPS_ByRunid(basepath, runids[19]),
                                     self.cal_IOPS_ByRunid(basepath, runids[20]),
                                     self.cal_IOPS_ByRunid(basepath, runids[21]),
                                     self.cal_IOPS_ByRunid(basepath, runids[22]),
                                     self.cal_IOPS_ByRunid(basepath, runids[23])
                                     ])
            scalingTables[7].extend([self.cal_AvgLat_ByRunid(basepath, runids[16]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[17]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[18]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[19]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[20]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[21]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[22]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[23])
                                     ])
            scalingTables[8].extend([self.cal_IOPS_ByRunid(basepath, runids[24]),
                                     self.cal_IOPS_ByRunid(basepath, runids[25]),
                                     self.cal_IOPS_ByRunid(basepath, runids[26]),
                                     self.cal_IOPS_ByRunid(basepath, runids[27]),
                                     self.cal_IOPS_ByRunid(basepath, runids[28]),
                                     self.cal_IOPS_ByRunid(basepath, runids[29]),
                                     self.cal_IOPS_ByRunid(basepath, runids[30]),
                                     self.cal_IOPS_ByRunid(basepath, runids[31])
                                     ])
            scalingTables[9].extend([self.cal_AvgLat_ByRunid(basepath, runids[24]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[25]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[26]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[27]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[28]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[29]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[30]),
                                     self.cal_AvgLat_ByRunid(basepath, runids[31])
                                     ])
        return scalingTables

    def cal_Throughput_FIO_IOPS_client(self, case):
        try:
            if self.dataObj:
                for key, value in self.dataObj["summary"]["run_id"].items():
                    return value["IOPS"]
        except:
            pass

    def cal_Throughput_FIO_BW_client(self, case):
        try:
            if self.dataObj:
                for key, value in self.dataObj["summary"]["run_id"].items():
                    return value["BW(MB/s)"]
        except:
            pass

    def cal_Throughput_FIO_Latency_client(self, case):
        try:
            if self.dataObj:
                for key, value in self.dataObj["summary"]["run_id"].items():
                    return value["Latency(ms)"]
        except:
            pass

    def cal_Throughput_FIO_Latency_tail_client(self, case):
        try:
            if self.dataObj:
                for key, value in self.dataObj["summary"]["run_id"].items():
                    return value["99.99% Latency(ms)"]
        except:
            pass

    def cal_ThroughputAvg_FIO_IOPS_client(self, case):
        try:
            if self.dataObj:
                worker_num = len(self.dataObj["workload"]["fio"]["summary"].keys())
                for key, value in self.dataObj["summary"]["run_id"].items():
                    total_iops = 0
                    if ',' in value["IOPS"]:
                        for s in value["IOPS"].split(','):
                            total_iops += float(s)
                    else:
                        total_iops = float(value["IOPS"])
                    return "%.3f" % (total_iops / worker_num)
        except:
            pass

    def cal_ThroughputAvg_FIO_BW_client(self, case):
        try:
            if self.dataObj:
                worker_num = len(self.dataObj["workload"]["fio"]["summary"].keys())
                for key, value in self.dataObj["summary"]["run_id"].items():
                    total_iops = 0
                    if ',' in value["BW(MB/s)"]:
                        for s in value["BW(MB/s)"].split(','):
                            total_iops += float(s)
                    else:
                        total_iops = float(value["BW(MB/s)"])
                    return "%.3f" % (total_iops / worker_num)
        except:
            pass

    def cal_ThroughputAvg_FIO_Latency_client(self, case):
        try:
            if self.dataObj:
                for key, value in self.dataObj["summary"]["run_id"].items():
                    return value["Latency(ms)"]
        except:
            pass

    def cal_CPU_user_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["cpu"]["summary"].items():
                    tmpList.extend(value["%usr"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_kernel_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["cpu"]["summary"].items():
                    tmpList.extend(value["%sys"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_iowait_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["cpu"]["summary"].items():
                    tmpList.extend(value["%iowait"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_soft_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["cpu"]["summary"].items():
                    tmpList.extend(value["%soft"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_idle_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["cpu"]["summary"].items():
                    tmpList.extend(value["%idle"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_user_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["client"]["cpu"]["summary"].items():
                    tmpList.extend(value["%usr"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_kernel_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["client"]["cpu"]["summary"].items():
                    tmpList.extend(value["%sys"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_iowait_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["client"]["cpu"]["summary"].items():
                    tmpList.extend(value["%iowait"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_soft_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["client"]["cpu"]["summary"].items():
                    tmpList.extend(value["%soft"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_CPU_idle_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["client"]["cpu"]["summary"].items():
                    tmpList.extend(value["%idle"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_Journal_r_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["r/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_Journal_w_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["w/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_Journal_rMB_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["rMB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_Journal_wMB_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["wMB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_Journal_avgrqsz_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["avgrq-sz"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_Journal_avgqusz_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["avgqu-sz"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_Journal_await_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["await"])
            return sum(tmpList) / len(tmpList) * 1000
        except:
            pass

    def cal_AVG_IOPS_Journal_svtcm_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["svctm"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_Journal_util_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["journal"]["summary"].items():
                    tmpList.extend(value["%util"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_OSD_r_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["r/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_OSD_w_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["w/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_OSD_rMB_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["rMB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_OSD_wMB_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["wMB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_OSD_avgrqsz_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["avgrq-sz"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_OSD_avgqusz_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["avgqu-sz"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_OSD_await_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["await"])
            return sum(tmpList) / len(tmpList) * 1000
        except:
            pass

    def cal_AVG_IOPS_OSD_svtcm_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["svctm"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_OSD_util_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key, value in self.dataObj["ceph"]["osd"]["summary"].items():
                    tmpList.extend(value["%util"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_AVG_IOPS_WAL_r_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["r/s"])
                ret = sum(tmpList) / len(tmpList)
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["r/s"])
                ret += sum(tmpList) / len(tmpList)
            return ret
        except:
            pass

    def cal_AVG_IOPS_WAL_w_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["w/s"])
                ret = sum(tmpList) / len(tmpList)
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["w/s"])
                ret += sum(tmpList) / len(tmpList)
            return ret
        except:
            pass

    def cal_AVG_IOPS_WAL_rMB_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["rMB/s"])
                ret = sum(tmpList) / len(tmpList)
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["rMB/s"])
                ret += sum(tmpList) / len(tmpList)
            return ret
        except:
            pass

    def cal_AVG_IOPS_WAL_wMB_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["wMB/s"])
                ret = sum(tmpList) / len(tmpList)
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["wMB/s"])
                ret += sum(tmpList) / len(tmpList)
            return ret
        except:
            pass

    def cal_AVG_IOPS_WAL_avgrqsz_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["avgrq-sz"])
                ret = sum(tmpList) / len(tmpList)
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["avgrq-sz"])
                ret += sum(tmpList) / len(tmpList)
            return ret
        except:
            pass

    def cal_AVG_IOPS_WAL_avgqusz_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["avgqu-sz"])
                ret = sum(tmpList) / len(tmpList)
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["avgqu-sz"])
                ret += sum(tmpList) / len(tmpList)
            return ret
        except:
            pass

    def cal_AVG_IOPS_WAL_await_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["await"])
                ret = sum(tmpList) / len(tmpList) * 1000
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["await"])
                ret += sum(tmpList) / len(tmpList) * 1000
            return ret
        except:
            pass

    def cal_AVG_IOPS_WAL_svtcm_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["svctm"])
                ret = sum(tmpList) / len(tmpList)
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["svctm"])
                ret += sum(tmpList) / len(tmpList)
            return ret
        except:
            pass

    def cal_AVG_IOPS_WAL_util_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["wal"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["wal"]["summary"][key]["%util"])
                ret = sum(tmpList) / len(tmpList)
                tmpList = []
                for key in self.dataObj["ceph"]["db"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["db"]["summary"][key]["%util"])
                ret += sum(tmpList) / len(tmpList)
            return ret
        except:
            pass

    def cal_Memory_kbmemfree_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["memory"]["summary"][key]["kbmenfree"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_Memory_kbmemfree_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["memory"]["summary"][key]["kbmenfree"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_Memory_kbmemfree_vclient(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["memory"]["summary"][key]["kbmenfree"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_Memory_kbmemused_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["memory"]["summary"][key]["kbmemused"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_Memory_kbmemused_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["memory"]["summary"][key]["kbmemused"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_Memory_kbmemused_vclient(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["memory"]["summary"][key]["kbmemused"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_Memory_memused_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["memory"]["summary"][key]["%memused"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_Memory_memused_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["memory"]["summary"][key]["%memused"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_Memory_memused_vclient(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["memory"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["memory"]["summary"][key]["%memused"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_rxpck_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["nic"]["summary"][key]["rxpck/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_rxpck_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["nic"]["summary"][key]["rxpck/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_rxpck_vclient(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["nic"]["summary"][key]["rxpck/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_txpck_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["nic"]["summary"][key]["txpck/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_txpck_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["nic"]["summary"][key]["txpck/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_txpck_vclient(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["nic"]["summary"][key]["txpck/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_rxkB_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["nic"]["summary"][key]["rxkB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_rxkB_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["nic"]["summary"][key]["rxkB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_rxkB_vclient(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["nic"]["summary"][key]["rxkB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_txkB_ceph(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["ceph"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["ceph"]["nic"]["summary"][key]["txkB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_txkB_client(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["nic"]["summary"][key]["txkB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_NIC_txkB_vclient(self, case):
        try:
            tmpList = []
            if self.dataObj:
                for key in self.dataObj["client"]["nic"]["summary"]:
                    tmpList.extend(self.dataObj["client"]["nic"]["summary"][key]["txkB/s"])
            return sum(tmpList) / len(tmpList)
        except:
            pass

    def cal_BW_ByRunid(self, basepath, runid):
        try:
            dataObj = self.GetDataObjByRunid(basepath, runid)
            if dataObj:
                for key, value in dataObj["summary"]["run_id"].items():
                    return get_float(value["BW(MB/s)"])
        except:
            pass

    def cal_AvgLat_ByRunid(self, basepath, runid):
        try:
            dataObj = self.GetDataObjByRunid(basepath, runid)
            if dataObj:
                for key, value in dataObj["summary"]["run_id"].items():
                    return get_float(value["Latency(ms)"])
        except:
            pass

    def cal_IOPS_ByRunid(self, basepath, runid):
        try:
            dataObj = self.GetDataObjByRunid(basepath, runid)
            if dataObj:
                for key, value in dataObj["summary"]["run_id"].items():
                    return get_float(value["IOPS"])
        except:
            pass
