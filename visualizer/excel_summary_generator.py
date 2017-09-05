import xlsxwriter
import excel_data_frame
import os,sys
import argparse
import collections

def GenExcelFile(dataFile, value, caseNum):
    eTables, extTables = value
    dataSheet = dataFile.add_worksheet(u'Detail')

    for i,eRow in enumerate(eTables):
        for j,eCol in enumerate(eRow):
            if i == 0 and j > 0:
                dataSheet.merge_range(i, 3*j-2, i, 3*j, eCol.split("/")[-1], set_style(dataFile, 'title'))
            else:
                if isinstance(eCol, list):
                    dataSheet.write(i, j, eCol[0], set_style(dataFile,eCol[1]))
                else:
                    fmtStr = "content_b" if j % 3 == 0 else "content"
                    dataSheet.write(i, j, eCol, set_style(dataFile,fmtStr))
    
    i += 2
    dataSheet.merge_range(i, 0, i, 5, "general info", set_style(dataFile, "title"))
    i += 1
    dataSheet.merge_range(i, 0, i, 5, "runcase", set_style(dataFile, "title"))
    i += 1
    ei = i
    chartList = []
    for extTable in extTables:
        chartList.append(i)
        ej = 0
        for extRow in extTable:
            ei = i            
            for extCol in extRow:
                if type(extCol) == list:
                    if ej > 0 and extCol[0] != "" and  type(extTable[0][0]) == list: #for chart's title
                        dataSheet.write(ei, 7, extTable[0][0][0] + " - " + extCol[0])
                    if extCol[1] > 1:
                        dataSheet.merge_range(ei, ej, ei+extCol[1]-1, ej, extCol[0], set_style(dataFile, extCol[2]))
                    else:
                        dataSheet.write(ei, ej, extCol[0], set_style(dataFile, extCol[2]))
                    ei = ei+extCol[1]
                else:
                    dataSheet.write(ei, ej, extCol, set_style(dataFile, 'content'))
                    ei += 1
            ej += 1
        i = ei + 1
        dataSheet.merge_range(ei, 0, ei, 5, "", set_style(dataFile, 'content'))

    for ci in chartList:
        charts = getChart(dataFile, ci)
        for i,chart in enumerate(charts):
            x_offset = i * 380 + 10
            dataSheet.insert_chart(ci + 1, 6, chart, {'x_offset': x_offset, 'y_offset': 0})

    for k in range(3*caseNum + 1):
        dataSheet.set_column(k, k, 18)
    dataSheet.set_row(0, 34)

def getChart(fileObj, ci):
    chars = []
    #CPU char
    tmpChart1 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart1.add_series({
        'name': ['Detail', ci+1, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 1, 3, ci + 1, 5],
    })
    tmpChart1.add_series({
        'name': ['Detail', ci+2, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 2, 3, ci + 2, 5],
    })
    tmpChart1.add_series({
        'name': ['Detail', ci+3, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 3, 3, ci + 3, 5],
    })
    tmpChart1.set_title ({'name': ['Detail', ci + 1, 7]}) 
    tmpChart1.set_y_axis({'name': 'ratio(100%)'})
    tmpChart1.set_style(12)
    tmpChart1.set_size({'width': 380, 'height': 300})
    tmpChart1.set_legend({'position': 'bottom'})
    chars.append(tmpChart1)
    
    #MEM char
    tmpChart2 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart2.add_series({
        'name': ['Detail', ci + 22, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 22, 3, ci + 22, 5],
    })
    tmpChart2.set_title ({'name': ['Detail', ci + 22, 7]})
    tmpChart2.set_y_axis({'name': 'ratio(100%)'})
    tmpChart2.set_style(12)
    tmpChart2.set_size({'width': 380, 'height': 300})
    tmpChart2.set_legend({'position': 'bottom'})
    chars.append(tmpChart2)
    
    #NIC char
    tmpChart3 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart3.add_series({
        'name': ['Detail', ci + 23, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 23, 3, ci + 23, 5],
    })
    tmpChart3.add_series({
        'name': ['Detail', ci + 24, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 24, 3, ci + 24, 5],
    })
    tmpChart3.set_title ({'name': ['Detail', ci + 23, 7]})
    tmpChart3.set_y_axis({'name': 'BandWidth(KB/s)'})
    tmpChart3.set_style(12)
    tmpChart3.set_size({'width': 380, 'height': 300})
    tmpChart3.set_legend({'position': 'bottom'})
    chars.append(tmpChart3)
    
    #DISK(journal) char
    tmpChart4 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart4.add_series({
        'name': ['Detail', ci + 4, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 4, 3, ci + 4, 5],
    })
    tmpChart4.add_series({
        'name': ['Detail', ci + 5, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 5, 3, ci + 5, 5],
    })
    tmpChart5 = fileObj.add_chart({'type': 'line'})
    tmpChart5.add_series({
        'name': ['Detail', ci + 10, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 10, 3, ci + 10, 5],
        'marker': {'type': 'diamond'},
        'line':   {'width': 1.5},
        'y2_axis':True,
    })
    tmpChart4.combine(tmpChart5)
    tmpChart4.set_title ({'name': ['Detail', ci + 4, 7]})
    tmpChart4.set_y_axis({'name': 'IOPS'})
    tmpChart5.set_y2_axis({'name': 'Latency(ms)'})
    tmpChart4.set_style(12)
    tmpChart4.set_size({'width': 380, 'height': 300})
    tmpChart4.set_legend({'position': 'bottom'})
    chars.append(tmpChart4)
    
    #DISK(journal) char BW
    tmpChart8 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart8.add_series({
        'name': ['Detail', ci + 6, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 6, 3, ci + 6, 5],
    })
    tmpChart8.add_series({
        'name': ['Detail', ci + 7, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 7, 3, ci + 7, 5],
    })
    tmpChart9 = fileObj.add_chart({'type': 'line'})
    tmpChart9.add_series({
        'name': ['Detail', ci + 10, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 10, 3, ci + 10, 5],
        'marker': {'type': 'diamond'},
        'line':   {'width': 1.5},
        'y2_axis':True,
    })
    tmpChart8.combine(tmpChart9)
    tmpChart8.set_title ({'name': ['Detail', ci + 4, 7]})
    tmpChart8.set_y_axis({'name': 'BandWidth(MB/s)'})
    tmpChart9.set_y2_axis({'name': 'Latency(ms)'})
    tmpChart8.set_style(12)
    tmpChart8.set_size({'width': 380, 'height': 300})
    tmpChart8.set_legend({'position': 'bottom'})
    chars.append(tmpChart8)
    
    #DISK(OSD) char
    tmpChart6 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart6.add_series({
        'name': ['Detail', ci + 13, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 13, 3, ci + 13, 5],
    })
    tmpChart6.add_series({
        'name': ['Detail', ci + 14, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 14, 3, ci + 14, 5],
    })
    tmpChart7 = fileObj.add_chart({'type': 'line'})
    tmpChart7.add_series({
        'name': ['Detail', ci + 19, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 19, 3, ci + 19, 5],
        'marker': {'type': 'diamond'},
        'line':   {'width': 1.5},
        'y2_axis':True,
    })
    tmpChart6.combine(tmpChart7)
    tmpChart6.set_title ({'name': ['Detail', ci + 13, 7]})
    tmpChart6.set_y_axis({'name': 'IOPS'})
    tmpChart7.set_y2_axis({'name': 'Latency(ms)'})
    tmpChart6.set_style(12)
    tmpChart6.set_size({'width': 380, 'height': 300})
    tmpChart6.set_legend({'position': 'bottom'})
    chars.append(tmpChart6)

    #DISK(OSD) char BW
    tmpChart10 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart10.add_series({
        'name': ['Detail', ci + 15, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 15, 3, ci + 15, 5],
    })
    tmpChart10.add_series({
        'name': ['Detail', ci + 16, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 16, 3, ci + 16, 5],
    })
    tmpChart11 = fileObj.add_chart({'type': 'line'})
    tmpChart11.add_series({
        'name': ['Detail', ci + 19, 2],
        'categories': ['Detail', ci, 3, ci, 5],
        'values': ['Detail', ci + 19, 3, ci + 19, 5],
        'marker': {'type': 'diamond'},
        'line':   {'width': 1.5},
        'y2_axis':True,
    })
    tmpChart10.combine(tmpChart11)
    tmpChart10.set_title ({'name': ['Detail', ci + 13, 7]})
    tmpChart10.set_legend({'position': 'bottom'})
    tmpChart10.set_y_axis({'name': 'Bandwidth(MB/s)'})
    tmpChart11.set_y2_axis({'name': 'Latency(ms)'})
    tmpChart10.set_style(12)
    tmpChart10.set_size({'width': 380, 'height': 300})
    chars.append(tmpChart10)
    return chars

def GenScalingSheet(dataFile, value):
    volumeScalingTables, qdScalingTables = value
    volumeScalingSheet = dataFile.add_worksheet(u'Volume Scaling')
    qdScalingSheet = dataFile.add_worksheet(u'QD Scaling')
    vm_chartList = []
    for vi, vsRow in enumerate(volumeScalingTables):
        if len(vsRow) > 1 and vsRow[0] == "chartinfo":
            vm_chartList.append([vsRow[1], vsRow[2]])
            continue
        for vj, vsCol in enumerate(vsRow):
            if type(vsCol) == list:
                volumeScalingSheet.merge_range(vi, vj, vi + vsCol[2], vj + vsCol[1], vsCol[0], set_style(dataFile, 'content'))
            else:
                volumeScalingSheet.write(vi, vj, vsCol, set_style(dataFile, 'content'))

    for vm_ci in vm_chartList:
        for vci, vchart in enumerate(getScalingChart(dataFile, "Volume Scaling", vm_ci[0], 2, vm_ci[0] + 2, 2, vm_ci[0] + vm_ci[1])):
            x_offset = vci * 500 + 10
            volumeScalingSheet.insert_chart(vm_ci[0], 10, vchart, {'x_offset': x_offset, 'y_offset': 0})

    qd_chartList = []
    for qi, qdRow in enumerate(qdScalingTables):
        if len(qdRow) > 1 and qdRow[0] == "chartinfo":
            qd_chartList.append([qdRow[1], qdRow[2]])
            continue
        for qj, qdCol in enumerate(qdRow):
            if type(qdCol) == list:
                qdScalingSheet.merge_range(qi, qj, qi + qdCol[2], qj + qdCol[1], qdCol[0], set_style(dataFile, 'content'))
            else:
                qdScalingSheet.write(qi, qj, qdCol, set_style(dataFile, 'content'))
    for qd_ci in qd_chartList:
        for qci, qchart in enumerate(getScalingChart(dataFile, "QD Scaling", qd_ci[0], 2, qd_ci[0] + 2, 2, qd_ci[0] + qd_ci[1])):
            x_offset = qci * 500 + 10
            qdScalingSheet.insert_chart(qd_ci[0], 10, qchart, {'x_offset': x_offset, 'y_offset': 0})

    for l in range(10):
        if l < 2 or l % 2 == 0:
            volumeScalingSheet.set_column(l, l, 10)
        else:
            volumeScalingSheet.set_column(l, l, 18)

    for m in range(10):
        if m < 2 or m % 2 == 0:
            qdScalingSheet.set_column(m, m, 10)
        else:
            qdScalingSheet.set_column(m, m, 18)

def getScalingChart(fileObj, sheetName, name_row, name_col, s_row, s_col, e_row):
    chars = []
    tmpChart1 = fileObj.add_chart({'type': 'scatter', 'subtype': 'straight_with_markers'})
    tmpChart1.add_series({
        'name': [sheetName, name_row, name_col + 4],
        'categories': [sheetName, s_row, s_col + 4, e_row, s_col + 4],
        'values': [sheetName, s_row, s_col + 5, e_row, s_col + 5],
        'marker': {'type': 'circle'},
        'line': {'width': 1},
    })
    tmpChart1.add_series({
        'name': [sheetName, name_row, name_col + 6],
        'categories': [sheetName, s_row, s_col + 6, e_row, s_col + 6],
        'values': [sheetName, s_row, s_col + 7, e_row, s_col + 7],
        'marker': {'type': 'circle'},
        'line': {'width': 1},
    })
    tmpChart1.set_title({'name': '4K Random Read & Write Performance Configuration-80 OSDs, QD=64', 'name_font': {'size': 14}})
    tmpChart1.set_x_axis({'name': 'IOPS'})
    tmpChart1.set_y_axis({'name': 'Latency(ms)'})
    tmpChart1.set_legend({'position': 'bottom'})
    chars.append(tmpChart1)
    tmpChart2 = fileObj.add_chart({'type': 'scatter', 'subtype': 'straight_with_markers'})
    tmpChart2.add_series({
        'name': [sheetName, name_row, name_col],
        'categories': [sheetName, s_row, s_col, e_row, s_col],
        'values': [sheetName, s_row, s_col + 1, e_row, s_col + 1],
        'marker': {'type': 'circle'},
        'line': {'width': 1},
    })
    tmpChart2.add_series({
        'name': [sheetName, name_row, name_col + 2],
        'categories': [sheetName, s_row, s_col + 2, e_row, s_col + 2],
        'values': [sheetName, s_row, s_col + 3, e_row, s_col + 3],
        'marker': {'type': 'circle'},
        'line': {'width': 1},
    })
    tmpChart2.set_title({'name': '64K Sequential Read & Write Performance Configuration-80 OSDs, QD=64', 'name_font': {'size': 14}})
    tmpChart2.set_x_axis({'name': 'BW(MB/s)'})
    tmpChart2.set_y_axis({'name': 'Latency(ms)'})
    tmpChart2.set_legend({'position': 'bottom'})
    chars.append(tmpChart2)
    return chars

def set_style(fileObj, name):
    styleObj = {
        'title': {'bold': True, 'bg_color': '#5B9BD5', 'bottom': 1, 'top': 1, 'left': 2, 'right': 2, 'valign': 'vcenter'},
        'subtitle': {'bold': True, 'bg_color': '#5B9BD5', 'bottom': 1, 'top': 1, 'left': 1, 'right': 1},
        'subtitle_b': {'bold': True, 'bg_color': '#5B9BD5', 'bottom': 1, 'top': 1, 'left': 1, 'right': 2},
        'sstitle': {'bg_color': '#FFFFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 2},
        'rtitle': {'bold': True, 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 1},
        'rtitle_b': {'bold': True, 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 2},
        'content': {'bottom': 1, 'top': 1, 'left': 1, 'right': 1},
        'content_b': {'bottom': 1, 'top': 1, 'left': 1, 'right': 2},
    }
    return fileObj.add_format(styleObj[name]) if name in styleObj else fileObj.add_format({})

def classifyRunids(edf, basepath, runids, volume, qd):
    vm_runids = []
    qd_runids = []
    for runid in runids:
        dataObj = edf.GetDataObjByRunid(basepath, runid)
        if dataObj and dataObj["summary"]["run_id"][str(runid)]["Worker"] == str(volume):
            vm_runids.append(runid)
        if dataObj and dataObj["summary"]["run_id"][str(runid)]["QD"] == "qd" + str(qd):
            qd_runids.append(runid)
    return vm_runids,qd_runids

def get_volume_group(runids):
    result = collections.OrderedDict()
    for runid in runids:
        if getBenchType(runid) != "fiorbd":
            continue
        tmpVM = getVolume(runid)
        tmpQD = getQD(runid)
        tmpType = getType(runid)
        if tmpVM not in result:
            result[tmpVM] = {}
        if tmpQD not in result[tmpVM]:
            result[tmpVM][tmpQD] = {}
        if tmpType not in  result[tmpVM][tmpQD]:
            result[tmpVM][tmpQD][tmpType] = runid
    return result

def get_qd_group(runids):
    result = collections.OrderedDict()
    for runid in runids:
        if getBenchType(runid) != "fiorbd":
            continue
        tmpQD = getQD(runid)
        tmpVM = getVolume(runid)
        tmpType = getType(runid)
        if tmpQD not in result:
            result[tmpQD] = {}
        if tmpVM not in result[tmpQD]:
            result[tmpQD][tmpVM] = {}
        if tmpType not in result[tmpQD][tmpVM]:
            result[tmpQD][tmpVM][tmpType] = runid
    return result

def getBenchType(runid):
    return runid.split("/")[-1].split("-")[2]
def getType(runid):
    return runid.split("/")[-1].split("-")[3] + "-" + runid.split("/")[-1].split("-")[4]
def getVolume(runid):
    return int(runid.split("/")[-1].split("-")[1])
def getQD(runid):
    return int(runid.split("/")[-1].split("-")[5][2:])

def main(args):
    parser = argparse.ArgumentParser(description='Analyzer tool')
    parser.add_argument(
        '--path',nargs='*',
    )
    parser.add_argument(
        '--dest_dir',
    )
    parser.add_argument(
        '--type',
    )
    parser.add_argument(
        '--bench_type',
    )

    args = parser.parse_args(args)
    cases = args.path
    storeType = args.type
    if args.bench_type != None:
        benchType = args.bench_type
    else:    
        benchType = "fiorbd"
    if args.dest_dir != None:
        dest_dir = args.dest_dir
    else:    
        dest_dir = "./"
    edf = excel_data_frame.ExcelDataFrame(cases, storeType, benchType)
    dataFile = xlsxwriter.Workbook('%s/summary.xlsx' % dest_dir)
    GenExcelFile(dataFile, edf.GetExcelData(), len(cases))
    GenScalingSheet(dataFile, edf.GetScalingSheetData(get_qd_group(cases), get_volume_group(cases)))
    dataFile.close()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
