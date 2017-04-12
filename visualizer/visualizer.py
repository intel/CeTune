import os,sys
import argparse
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import *
import os, sys
import time
import pprint
import re
from collections import OrderedDict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pyplot
import json
import yaml
import numpy
from create_DB import *

pp = pprint.PrettyPrinter(indent=4)
class Visualizer:
    def __init__(self, result, path=None):
        if not path:
            all_path = "../conf/"
        else:
            if os.path.isdir('%s/%s' % ( path, 'conf' )):
                all_path = '%s/%s' % ( path, 'conf' )
            else:
                all_path = path
        self.all_conf_data = config.Config("%s/all.conf" % all_path)
        self.db_path = self.all_conf_data.get("dest_dir")
        self.result = result
        self.output = []
        if path:
            self.path = path
            self.session_name = os.path.basename(path.strip('/'))
        self.dest_dir_remote_bak = self.all_conf_data.get("dest_dir_remote_bak", dotry = True)
        self.user = self.all_conf_data.get("user")

    def generate_summary_page(self):
        #0. framework
        common.bash("rm -f ../visualizer/include/pic/*")
        common.bash("rm -f ../visualizer/include/csv/*")
        output = []
        output.append("<div id='tabs'>")
        output.append("<ul>")
        for node_type, node_data in self.result.items():
            if not isinstance(node_data, dict):
                continue
            output.append("<li><a href=\"#\">%s</a></li>" % (node_type))
        output.append("</ul>")

        for node_type, node_data in self.result.items():
            if not isinstance(node_data, dict):
                continue
            common.printout("LOG","Generating %s view" % node_type,log_level="LVL5")
            output.extend(self.generate_node_view(node_type))

        output.append("</div>")
        output.append("<script>")
        output.append("$(\"#tabs ul li a\").click(function(){   $(\"#tabs ul li\").removeClass(\"tabs_li_click\");  $(this).parent().addClass(\"tabs_li_click\"); var tabsName = $(this).text();  var div_id = \"#\" + tabsName;    $(\"#tabs\").children('div').hide();  $(div_id).show(); });")
        output.append("$( \".cetune_pic\" ).hide();")
        output.append("$( \".cetune_table a\" ).click(function(){$(this).parents('.cetune_table').parent().children('.cetune_pic').hide();var id=$(this).attr('id'); $(this).parents('.cetune_table').parent().children('#'+id+'_pic').fadeIn()});")
        output.append("$(\"#tabs ul li a\").first().click()")
        output.append("</script>")
        output = self.add_html_framework(output)
        with open("%s/%s.html" % (self.path, self.result["session_name"]), 'w') as f:
            f.write(output)
        common.bash("cp -r %s %s" % ("../visualizer/include/", self.path))

        if self.dest_dir_remote_bak == "":
            return

        # Copy local result to remote dir
        common.printout("LOG","Session result generated, copy to remote",log_level="LVL5")
        common.bash("scp -r %s %s" % (self.path, self.dest_dir_remote_bak))

        remote_bak, remote_dir = self.dest_dir_remote_bak.split(':')
        output = self.generate_history_view(remote_bak, remote_dir, self.user)

        common.printout("LOG","History view generated, copy to remote",log_level="LVL5")
        with open("%s/cetune_history.html" % self.path, 'w') as f:
            f.write(output)
        common.bash("scp -r %s/cetune_history.html %s" % (self.path, self.dest_dir_remote_bak))
        common.bash("scp -r ../visualizer/include %s" % (self.dest_dir_remote_bak))

    def dataparse(self,data):
        #print data
        rows = []
        list_data = []
        for i in data.keys():
            list_data.append(data[i])
        for i in list_data:
            row = []
            row.extend(re.findall('id=(.*?)>',re.search('(<tr.*?>)', i, re.S).group(1),re.S))
            row.extend(re.findall('<td .*?>(.*?)</td>', i, re.S))
            for i in range(len(row)):
                row[i] = row[i].strip()
            rows.append(row)
        return rows

    def parse_to_html(self,data):
        lines = {}
        for i in data:
            i =list(i)
            line = ''
            for j in range(len(i)):
                if j == 0:
                    line += "<tr href=%s/%s.html id=%s>"%(i[j],i[j],i[j])
                    line += "<td><input type='checkbox' class = 'checkbox_configuration_class' id='checkbox_configuration_%s' name='checkbox_%s'></td>"%(j,j)
                else:
                    if type(i[j]) == float:
                        line += "<td title='%.3f'>%.3f</td>\n"%(i[j],i[j])
                    elif type(i[j]) == int:
                        line += "<td title='%d'>%d</td>\n"%(i[j],i[j])
                    else:
                        line += "<td title='%s'>%s</td>\n"%(i[j],i[j])
            if line != '':
                line += "</tr>\n"
            lines[i[1]] = line
        return lines


    def get_column_nu_and_ind(self,file_ph):
        f = open(file_ph,'r+')
        ft = f.read()
        tr = re.findall('<tr>(.*?)</tr>', ft, re.S)
        th = re.findall('<th>(.*?)</th>', tr[0], re.S)
        f.close()
        ind = 0
        ind1 = 0
        num = 0
        for i in range(len(th)):
            if "Description" in th[i]:
                ind = i
                break
        if ind!=0:
            f1 = open(file_ph,'r+')
            data = f1.readlines()
            for i in range(len(data)):
                if '</td>' in data[i]:
                    if ind1 == ind:
                        num = i
                        break
                    ind1 += 1
        if num != 0:
            return num


    def edit_html(self,file_path,num,new_description):
        f = open(file_path,'r+')
        ft = f.readlines()
        ft[num] = "<td>"+new_description+"</td>\n"
        f = open(file_path,'w+')
        f.writelines(ft)
        f.close()

    def update_report_list_db(self,tr_id,new_description):
        db_path = os.path.join(self.db_path,"cetune_report.db")
        if os.path.exists(db_path):
            database.update_by_runid(tr_id,'description',new_description,db_path)
            file_path = self.db_path+tr_id+"/conf/description"
            if os.path.exists(file_path):
                os.remove(file_path)
                f = open(file_path, 'w')
                f.write(new_description)
                f.close()
            else:
                f = open(file_path, 'w')
                f.write(new_description)
                f.close()
            html_path = os.path.join(self.db_path,tr_id,tr_id+".html")
            nu = self.get_column_nu_and_ind(html_path)
            if nu != 0:
                self.edit_html(html_path,nu,new_description)
        else:
            print "Error:database -/mnt/data/cetune_report.db not exist."

    def check_DB_case_list(self,re_dir,dbpath):
        if os.path.exists(dbpath):
            output = os.popen("ls "+re_dir)
            li = output.readlines()
            local_list = []
            for i in li:
                if os.path.exists(os.path.join(re_dir,i.strip('\n'),i.strip('\n')+'.html')):
                    local_list.append(i.strip('\n'))
            #local_case_list = []
            #for i in local_list:
            #    if i != 'cetune_report.db':
            #        local_case_list.append(i)
            DB_list = database.get_runid_list(dbpath)
            local_list.sort()
            DB_list.sort()
            if local_list == DB_list:
                return True
            else:
                return False
        else:
            return False

    def generate_history_view(self, remote_host="127.0.0.1", remote_dir="/mnt/data/", user='root', html_format=True):
        common.printout("LOG","Generating history view",log_level="LVL5")
        dbpath = os.path.join(self.db_path,"cetune_report.db")
        if not self.check_DB_case_list(self.db_path,dbpath):
            #stdout, stderr = common.pdsh(user, [remote_host], "find %s -name '*.html' | grep -v 'cetune_history'|sort -u | while read file;do session=`echo $file | awk -F/ {'print $(NF-1)'}`; awk -v session=\"$session\" 'BEGIN{find=0;}{if(match($1,\"tbody\")&&find==2){find=0;}if(find==2){if(match($1,\"<tr\"))printf(\"<tr href=\"session\"/\"session\".html id=\"session\">\");else print ;};if(match($1,\"div\")&&match($2,\"summary\"))find=1;if(match($1,\"tbody\")&&find==1){find+=1}}' $file; done" % remote_dir, option="check_return")
            #res = common.format_pdsh_return(stdout)
            #if remote_host not in res:
            #    common.printout("ERROR","Generating history view failed")
            #    return False
            # some modification in greped trs
            stdout = common.bash("find %s -name '*.html' | grep -v 'cetune_history'|sort -u | while read file;do session=`echo $file | awk -F/ {'print $(NF-1)'}`; awk -v session=\"$session\" 'BEGIN{find=0;}{if(match($1,\"tbody\")&&find==2){find=0;}if(find==2){if(match($1,\"<tr\"))printf(\"<tr href=\"session\"/\"session\".html id=\"session\">\");else print ;};if(match($1,\"div\")&&match($2,\"summary\"))find=1;if(match($1,\"tbody\")&&find==1){find+=1}}' $file; done" % remote_dir,loglevel="LVL6")
            res_tmp = stdout;
            formated_report = {}
            report_lines = re.findall('(<tr.*?</tr>)',res_tmp,re.S)
            for line in report_lines:
                tr_start = re.search('(<tr.*?>)', line, re.S).group(1)
                data = re.findall('<td>(.*?)</td>', line, re.S)

                #runid = int(data[0])
                runid = re.findall('id=(.*?)>', tr_start, re.S)[0]
                if len(data) < 18:
                    data.insert(2, "")
                formated_report[runid] = tr_start
                for block in data:
                    formated_report[runid] += "<td title='%s'>%s</td>\n" % (block, block)
                formated_report[runid] += "</tr>\n"

            #create DB and create TB
            if not os.path.exists(dbpath):
                database.createTB(dbpath)
            rows = self.dataparse(formated_report)
            runid_list = []
            while [] in rows:
                rows.remove([])
            for i in rows:
                runid_list.append(i[0])
                if not database.check_case_exist(i[0],dbpath):
                    if len(i) < 19:
                        i.insert(2, "Unknown")
                    database.insert_to_TB(i,dbpath)
            #delete case from DB which is not exist
            diff_case_list = [ i for i in database.get_runid_list(dbpath) if i not in runid_list ]
            if len(diff_case_list) != 0:
                for i in diff_case_list:
                    database.delete_case_by_runid(i,dbpath)
        lines = self.parse_to_html(database.select_report_list(dbpath))
        output = []
        #output.append("<h1>CeTune History Page</h1>")
        #output.append("<input type='button' style='width:100%;height:5px;' onmouseover='this.style.backgroundColor=#286090;' onmouseout='this.style.backgroundColor=#FFF;'></input>")
        output.append("<input id='down_button' type='button' onclick='mouse_on()'></input>")
        output.append("<div id='result_report_top'><div id='result_report_dropdown_title'><h4 class='modal-title'>Delete the selected item</h4></div><div id='div_Configuration_right_top_button'><div><input id='result_report_delete_Cancel' class='btn btn-primary' type='button' value='Cancel' onclick ='Cancel_delete()'/><input id='result_report_delete' class='btn btn-primary' type='button' value='Delete' data-toggle='modal'  data-target='#DeleteResultReportModal' data-whatever='@mdo'/></div></div></div>")
        output.append("<table id='report_list' class='cetune_table'>")
        #output.append(" <thead>")
        output.extend( self.getSummaryTitle() )
        #output.append(" </thead>")
        #output.append(" <tbody>")
        #output.append(res_tmp)
        for runid in sorted(lines.keys()):
            output.append(lines[runid])
        #output.append(" </tbody>")
        output.append(" </table>")
        output.extend(self.getscripthtml())
        output.append("<script>")
        output.append("$('.cetune_table tr').dblclick(function(){var path=$(this).attr('href'); window.location=path})")
        output.append("</script>")
        if html_format:
            return self.add_html_framework(output)
        else:
            return "".join(output)


    def getscripthtml(self):
        output = []
        output.append("<script type='text/javascript'>")
        #output.append("$(function(){")
        output.append("$('#report_list').resizableColumns({store: store});")
        output.append("$('#report_list').xlsTableFilter();")
        #output.append("});")
        output.append("</script>")
        return output

    def getSummaryTitle(self):
        output = []
        output.append(" <tr id = 'result_report_title' z-index='0'>")
        output.append(" <th data-resizable-column-id='0'>Del</th>")
        #output.append(" <th data-resizable-column-id='0'><input id='result_report_delete'  z-index='1' class='btn btn-primary' type='button' value='Del'/></th>")
        output.append(" <th data-resizable-column-id='1'>runid</th>")
        output.append(" <th data-resizable-column-id='2'><a title='Timestamp' id='runid_timestamp' href='#'>Timestamp</a></th>")
        output.append(" <th data-resizable-column-id='3'><a title='CeTune Status' id='runid_status' href='#'>Status</a></th>")
        output.append(" <th data-resizable-column-id='4'><a title='Testcase description' id='runid_description' href='#'>Description</a></th>")
        output.append(" <th data-resizable-column-id='5'><a title='Size of Op Request' id='runid_op_size' href='#'>Op_Size</a></th>")
        output.append(" <th data-resizable-column-id='6'><a title='Type of Op Request' id='runid_op_type' href='#'>Op_Type</a></th>")
        output.append(" <th data-resizable-column-id='7'><a title='Queue_depth/Container Number' id='runid_QD' href='#'>QD</a></th>")
        output.append(" <th data-resizable-column-id='8'><a title='Type of Workload' id='runid_engine' href='#'>Driver</a></th>")
        output.append(" <th data-resizable-column-id='9'><a title='Storage Node Number' id='runid_serverNum' href='#'>SN_Number</a></th>")
        output.append(" <th data-resizable-column-id='10'><a title='Client Node Number' id='runid_clientNum' href='#'>CN_Number</a></th>")
        output.append(" <th data-resizable-column-id='11'><a title='Workers Number/Objects Number' id='runid_rbdNum' href='#'>Worker</a></th>")
        output.append(" <th data-resizable-column-id='12'><a title='Test Time be Profiled' id='runid_runtime' href='#'>Runtime(sec)</a></th>")
        output.append(" <th data-resizable-column-id='13'><a title='Benchmarked IOPS' id='runid_fio_iops' href='#'>IOPS</a></th>")
        output.append(" <th data-resizable-column-id='14'><a title='Benchmarked Bandwidth' id='runid_fio_bw' href='#'>BW(MB/s)</a></th>")
        output.append(" <th data-resizable-column-id='15'><a title='Benchmarked Latency' id='runid_fio_latency' href='#'>Latency(ms)</a></th>")
        output.append(" <th data-resizable-column-id='16'><a title='Benchmarked Latency 99.00' id='runid_fio_latency_99' href='#'>99.00% Latency(ms)</a></th>")
        output.append(" <th data-resizable-column-id='17'><a title='Storage Node IOPS' id='runid_osd_iops' href='#'>SN_IOPS</a></th>")
        output.append(" <th data-resizable-column-id='18'><a title='Storage Node Bandwidth' id='runid_osd_bw' href='#'>SN_BW(MB/s)</a></th>")
        output.append(" <th data-resizable-column-id='19'><a title='Storage Node Latency' id='runid_osd_latency' href='#'>SN_Latency(ms)</a></th>")
        output.append(" </tr>")
        return output

    def add_html_framework(self, maindata):
        output = []
        output.append("<html lang='us'>")
        output.append("<head>")
        output.append("<meta charset=\"utf-8\">")
        output.append("<title>CeTune HTML Visualizer</title>")
        output.append("<link rel=\"stylesheet\" type=\"text/css\" href=\"./include/css/Style.css\">")
        output.append("<link rel=\"stylesheet\" type=\"text/css\" href=\"./include/css/TableStyle.css\">")
        output.append("<link rel=\"stylesheet\" type=\"text/css\" href=\"./include/css/bootstrap.min.css\">")
        output.append("<script src=\"./include/jquery.js\"></script>")
#        output.append("<link href=\"./include/jquery/jquery-ui.css\" rel=\"stylesheet\">")
#        output.append("<link href=\"./include/css/common.css\" rel=\"stylesheet\">")
#        output.append("<script src=\"./include/jquery/jquery-ui.js\"></script>")
        output.append("</head>")
        output.append("<body>")
        output.extend(maindata)
        output.append("</body>")
        return "\n".join(output)

    def generate_node_view(self, node_type):
        output = []
        if len(self.result[node_type].keys()) == 0:
            return output
        output.append("<div id='%s'>" % node_type)
        for field_type, field_data in self.result[node_type].items():
            data = OrderedDict()
            chart_data = OrderedDict()
            for node, node_data in field_data.items():
                if node not in data:
                    data[node] = OrderedDict()
                for key, value in node_data.items():
                    if not isinstance(value, list):
                        data[node][key] = value
                    else:
                        data[node][key] = "%.3f" % numpy.mean(value)
                        if key not in chart_data:
                            chart_data[key] = OrderedDict()
                        chart_data[key][node] = value
            output.extend( self.generate_table_from_json(data,'cetune_table', field_type) )
            output.extend( self.generate_line_chart(chart_data, node_type, field_type ) )
        output.append("</div>")
        return output

    def generate_line_chart(self, data, node_type, field, append_table=True):
        output = []
        common.bash("mkdir -p ../visualizer/include/pic")
        common.bash("mkdir -p ../visualizer/include/csv")
        common.printout("LOG","generate %s line chart" % node_type,log_level="LVL5")
        for field_column, field_data in data.items():
            pyplot.figure(figsize=(9, 4))
            for node, node_data in field_data.items():
                pyplot.plot(node_data, label=node)
            pyplot.xlabel("time(sec)")
            pyplot.ylabel("%s" % field_column)
            # Shrink current axis's height by 10% on the bottom
            pyplot.legend(loc = 'center left', bbox_to_anchor = (1, 0.5), prop={'size':6})
            pyplot.grid(True)
            pyplot.suptitle("%s" % field_column)
            pic_name = '%s_%s_%s.png' % (node_type, field, re.sub('[/%]','',field_column))
            pyplot.savefig('../visualizer/include/pic/%s' % pic_name) 
            pyplot.close()
            line_table = []
            csv = self.generate_csv_from_json(field_data,'line_table',field_column)
            csv_name = '%s_%s_%s.csv' % (node_type, field, re.sub('[/%]','',field_column))
            with open( '../visualizer/include/csv/%s' % csv_name, 'w' ) as f:
                f.write( csv )
#output.append("<div class='cetune_pic' id='%s_%s_pic'><button><a href='./include/csv/%s'>Download detail csv table</a></button><img src='./include/pic/%s' alt='%s' style='height:400px; width:1000px'></div>" % (field, re.sub('[/%]','',field_column), csv_name, pic_name, field_column))
            output.append("<div class='cetune_pic' id='%s_%s_pic'><img src='./include/pic/%s' alt='%s' style='height:400px; width:1000px'><button><a href='./include/csv/%s'>Download detail csv table</a></button></div>" % (field, re.sub('[/%]','',field_column), pic_name, field_column, csv_name))
        return output

        #4. vclient info
    def generate_table_from_json(self, data, classname, node_type):
        output = []
        if len(data) == 0:
            return output
        output.append("<table class='%s'>" % classname)
        output.append("<thead>")
        output.append("<tr>")
        output.append("<th>%s</th>" % node_type)
        max_col_key = data.keys()[0]
        max_col_count = 0
        for key, value in data.items():
            tmp = len(value.keys())
            if tmp > max_col_count:
                max_col_count = tmp
                max_col_key = key
        for key in data[max_col_key].keys():
            output.append("<th><a id='%s_%s' href='#%s_%s'>%s</a></th>" % (node_type, re.sub('[/%]','',key), node_type, re.sub('[/%]','',key), key))
        output.append("<tr>")
        output.append("</thead>")
        output.append("<tbody>")
        for node, node_data in data.items():
            output.append("<tr>")
            output.append("<td>%s</td>" % node)
            for key, value in node_data.items():
                output.append("<td>%s</td>" % value)
            output.append("</tr>")
        output.append("</tbody>")
        output.append("</table>")
        return output

    def generate_csv_from_json(self, data, classname, node_type):
        output = []
        output.append(node_type+","+",".join(data.keys()))
        list_max = common.get_largest_list_len(data)
        for i in range(0, list_max):
            tmp = []
            tmp.append(str(i))
            for node, node_data in data.items():
                try:
                    tmp.append(str(node_data[i]))
                except:
                    tmp.append("Null")
            output.append( ",".join(tmp) )
        return "\n".join( output )

def main(args):
    parser = argparse.ArgumentParser(description='Analyzer tool')
    parser.add_argument(
        'operation',
        )
    parser.add_argument(
        '--path',
        )
    args = parser.parse_args(args)
    result = OrderedDict()
    if args.path:
        result.update(json.load(open('%s/result.json' % args.path), object_pairs_hook=OrderedDict))
    process = Visualizer(result, args.path)
    func = getattr(process, args.operation)
    if func:
        func()
if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
