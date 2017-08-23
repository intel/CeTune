import xlsxwriter
import excel_data_frame
import os,sys
import argparse

def GenExcelFile(dest_dir, value, caseNum):
    eTables, extTables = value
    dataFile = xlsxwriter.Workbook('%s/summary.xlsx' % dest_dir)
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
    dataFile.close()

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
    print args.path
    cases = args.path
    storeType = args.type
    if args.bench_type != None:
        benchType = args.bench_type
    else:    
        benchType = "fiorbd"
    dest_dir = args.dest_dir
    print dest_dir
    if args.dest_dir != None:
        dest_dir = args.dest_dir
    else:    
        dest_dir = "./"
    edf = excel_data_frame.ExcelDataFrame(cases, storeType, benchType)
    GenExcelFile( dest_dir, edf.GetExcelData(), len(cases))

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
