import xlsxwriter

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
    dataSheet.set_row(0, 25)
    dataFile.close()

def getChart(fileObj, ci):
    chars = []
    tmpChart1 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart1.add_series({
        'name': ['summary', ci+1, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 1, 3, ci + 1, 5],
    })
    tmpChart1.add_series({
        'name': ['summary', ci+2, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 2, 3, ci + 2, 5],
    })
    tmpChart1.add_series({
        'name': ['summary', ci+3, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 3, 3, ci + 3, 5],
    })
    tmpChart1.set_title ({'name': ['summary', ci + 1, 7]}) 
    tmpChart1.set_style(12)
    tmpChart1.set_size({'width': 380, 'height': 300})
    chars.append(tmpChart1)
    
    tmpChart2 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart2.add_series({
        'name': ['summary', ci + 13, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 13, 3, ci + 13, 5],
    })
    tmpChart2.set_title ({'name': ['summary', ci + 13, 7]})
    tmpChart2.set_style(12)
    tmpChart2.set_size({'width': 380, 'height': 300})
    chars.append(tmpChart2)
    
    tmpChart3 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart3.add_series({
        'name': ['summary', ci + 14, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 14, 3, ci + 14, 5],
    })
    tmpChart3.add_series({
        'name': ['summary', ci + 15, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 15, 3, ci + 15, 5],
    })
    tmpChart3.set_title ({'name': ['summary', ci + 14, 7]})
    tmpChart3.set_style(12)
    tmpChart3.set_size({'width': 380, 'height': 300})
    chars.append(tmpChart3)
    
    tmpChart4 = fileObj.add_chart({'type': 'column', 'subtype': 'stacked'})
    tmpChart4.add_series({
        'name': ['summary', ci + 6, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 6, 3, ci + 6, 5],
    })
    tmpChart4.add_series({
        'name': ['summary', ci + 7, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 7, 3, ci + 7, 5],
    })
    tmpChart5 = fileObj.add_chart({'type': 'line'})
    tmpChart5.add_series({
        'name': ['summary', ci + 10, 2],
        'categories': ['summary', ci, 3, ci, 5],
        'values': ['summary', ci + 10, 3, ci + 10, 5],
        'marker': {'type': 'diamond'},
        'line':   {'width': 1.5},
    })
    tmpChart4.combine(tmpChart5)
    tmpChart4.set_title ({'name': ['summary', ci + 4, 7]})
    tmpChart4.set_style(12)
    tmpChart4.set_size({'width': 380, 'height': 300})
    chars.append(tmpChart4)
    
    return chars

def set_style(fileObj, name):
    styleObj = {
        'title': {'bold': True, 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 2, 'right': 2, 'valign': 'vcenter'},
        'subtitle': {'bold': True, 'font_color': 'red', 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 1},
        'subtitle_b': {'bold': True, 'font_color': 'red', 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 2},
        'sstitle': {'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 2},
        'rtitle': {'bold': True, 'font_color': 'red', 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 1},
        'rtitle_b': {'bold': True, 'font_color': 'red', 'bg_color': '#BFEFFF', 'bottom': 1, 'top': 1, 'left': 1, 'right': 2},
        'content': {'bottom': 1, 'top': 1, 'left': 1, 'right': 1},
        'content_b': {'bottom': 1, 'top': 1, 'left': 1, 'right': 2},
    }
    return fileObj.add_format(styleObj[name]) if name in styleObj else fileObj.add_format({})
