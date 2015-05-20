import os,sys
import argparse
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import common
import os, sys
import time
import pprint
import numpy
import re
from collections import OrderedDict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pyplot

pp = pprint.PrettyPrinter(indent=4)
class Visualizer:
    def __init__(self, result):
        self.result = result
        self.output = []

    def generate_summary_page(self):
        #0. framework
        common.bash("rm -f ../visualizer/include/pic/*")
        output = [] 
        output.append("<div id='tabs'>")
        output.append("<ul>")
        output.append("<li><a href=\"#summary\">Summary</a></li>")
        output.append("<li><a href=\"#fio\">FIO</a></li>")
        output.append("<li><a href=\"#ceph\">Ceph</a></li>")
        output.append("<li><a href=\"#vclient\">VClient</a></li>")
        output.append("<li><a href=\"#client\">Client</a></li>")
        output.append("</ul>")
        #1. summary page
        output.append("<div id='summary'>")
        res = re.search('^(\d+)-(\d+)-(\w+)-(\w+)-(\w+)-\S+-(\w+)$',self.result["session_name"])
        if res:
            print common.bcolors.OKGREEN + "[LOG]Generating summary view" + common.bcolors.ENDC
            output.extend(self.generate_summary_view(res))
        output.append("</div>")

        #1. fio info
        print common.bcolors.OKGREEN + "[LOG]Generating fio view" + common.bcolors.ENDC
        output.extend(self.generate_node_view('fio'))
        #2. ceph info
        print common.bcolors.OKGREEN + "[LOG]Generating ceph view" + common.bcolors.ENDC
        output.extend(self.generate_node_view('ceph'))
        #3. vclient info
        print common.bcolors.OKGREEN + "[LOG]Generating vclient view" + common.bcolors.ENDC
        output.extend(self.generate_node_view('vclient'))
        #3. client info
        print common.bcolors.OKGREEN + "[LOG]Generating client view" + common.bcolors.ENDC
        output.extend(self.generate_node_view('client'))

        output.append("</div>")
        output.append("<script>")
        output.append("$( \"#tabs\" ).tabs();")
        output.append("$( \".cetune_pic\" ).hide();")
        output.append("$( \".cetune_table a\" ).click(function(){$(this).parents('.cetune_table').parent().children('.cetune_pic').hide();var id=$(this).attr('id'); $(this).parents('.cetune_table').parent().children('#'+id+'_pic').fadeIn()});")
        output.append("</script>")
        return self.add_html_framework(output)

    def generate_history_view(self, remote_host, remote_dir, user='root', session_id=""):
        output = []
        stdout, stderr = common.pdsh(user, [remote_host], "cat %s/cetune_history.html" % remote_dir, option="check_return")
        res = common.format_pdsh_return(stdout)
        if res:
            output = res[remote_host]
        print common.bcolors.OKGREEN + "[LOG]Generating history view" + common.bcolors.ENDC
        if output == []:
            stdout, stderr = common.pdsh(user, [remote_host], "cd %s; grep \"cetune_table\" -rl ./ | sort -u | while read file;do awk -v path=\"$file\" 'BEGIN{find=0;}{if(match($1,\"tbody\")&&find==2){find=0;}if(find==2){if(match($1,\"<tr\"))printf(\"<tr href=\"path\">\");else print ;};if(match($1,\"div\")&&match($2,\"summary\"))find=1;if(match($1,\"tbody\")&&find==1){find+=1}}' $file; done" % remote_dir, option="check_return")
        else:
            stdout, stderr = common.pdsh(user, [remote_host], "cd %s/%s; grep \"cetune_table\" -rl ./ | sort -u | while read file;do awk -v path=\"$file\" 'BEGIN{find=0;}{if(match($1,\"tbody\")&&find==2){find=0;}if(find==2){if(match($1,\"<tr\"))printf(\"<tr href=\"path\">\");else print ;};if(match($1,\"div\")&&match($2,\"summary\"))find=1;if(match($1,\"tbody\")&&find==1){find+=1}}' $file; done" % (remote_dir, session_id), option="check_return")
        res = common.format_pdsh_return(stdout)
        if remote_host not in res:
            print common.bcolors.FAIL + "[ERROR]Generating history view failed" + common.bcolors.ENDC
            return False
        if output != []:
            try:
                output = output.split('\n')
                insert_index = output.index("  </tbody>")
                output.insert(insert_index, res[remote_host])
            except:
                stdout, stderr = common.pdsh(user, [remote_host], "cd %s; grep \"cetune_table\" -rl ./ | sort -u | while read file;do awk -v path=\"$file\" 'BEGIN{find=0;}{if(match($1,\"tbody\")&&find==2){find=0;}if(find==2){if(match($1,\"<tr\"))printf(\"<tr href=\"path\">\");else print ;};if(match($1,\"div\")&&match($2,\"summary\"))find=1;if(match($1,\"tbody\")&&find==1){find+=1}}' $file; done" % remote_dir, option="check_return")
                res = common.format_pdsh_return(stdout)
                output = []
        if output == []:
            output.append("<h1>CeTune History Page</h1>")
            output.append("<table class='cetune_table'>")
            output.append(" <thead>")
            output.append(" <tr>")
            output.append(" <th>runid</th>")
            output.append(" <th><a id='runid_op_size' href='#'>op_size</a></th>")
            output.append(" <th><a id='runid_op_type' href='#'>op_type</a></th>")
            output.append(" <th><a id='runid_QD' href='#'>QD</a></th>")
            output.append(" <th><a id='runid_engine' href='#'>engine</a></th>")
            output.append(" <th><a id='runid_serverNum' href='#'>serverNum</a></th>")
            output.append(" <th><a id='runid_clientNum' href='#'>clientNum</a></th>")
            output.append(" <th><a id='runid_rbdNum' href='#'>rbdNum</a></th>")
            output.append(" <th><a id='runid_runtime' href='#'>runtime</a></th>")
            output.append(" <th><a id='runid_fio_iops' href='#'>fio_iops</a></th>")
            output.append(" <th><a id='runid_fio_bw' href='#'>fio_bw</a></th>")
            output.append(" <th><a id='runid_fio_latency' href='#'>fio_latency</a></th>")
            output.append(" <th><a id='runid_osd_iops' href='#'>osd_iops</a></th>")
            output.append(" <th><a id='runid_osd_bw' href='#'>osd_bw</a></th>")
            output.append(" <th><a id='runid_osd_latency' href='#'>osd_latency</a></th>")
            output.append(" <tr>")
            output.append(" </thead>")
            output.append(" <tbody>")
            output.append(res[remote_host])
            output.append(" </tbody>")
            output.append("<script>")
            output.append("$(\".cetune_table tr\").click(function(){var path=$(this).attr('href'); window.location=path})")
            output.append("</script>")
        return self.add_html_framework(output)

    def add_html_framework(self, maindata):
        output = []
        output.append("<html lang='us'>")
        output.append("<head>")
	output.append("<meta charset=\"utf-8\">")
	output.append("<title>CeTune HTML Visualizer</title>")
	output.append("<link href=\"./include/jquery/jquery-ui.css\" rel=\"stylesheet\">")
	output.append("<link href=\"./include/css/common.css\" rel=\"stylesheet\">")
        output.append("<script src=\"./include/jquery/external/jquery/jquery.js\"></script>")
        output.append("<script src=\"./include/jquery/jquery-ui.js\"></script>")
        output.append("</head>")
        output.append("<body>")
        output.extend(maindata)
        output.append("</body>")
        return "\n".join(output)

    def generate_summary_view(self, res):
        data = {}
        data[res.group(1)]=OrderedDict()
        tmp = data[res.group(1)]
        tmp["op_size"] = res.group(4)
        tmp["op_type"] = res.group(3)
        tmp["QD"] = res.group(5)
        tmp["engine"] = res.group(6)
        tmp["serverNum"] = len(self.result["ceph"])
        tmp["clientNum"] = len(self.result["client"])
        tmp["rbdNum"] = res.group(2)
        tmp["runtime"] = "%d sec" % self.result["runtime"]
        tmp["fio_iops"] = 0
        tmp["fio_bw"] = 0
        tmp["fio_latency"] = 0
        tmp["osd_iops"] = 0
        tmp["osd_bw"] = 0
        tmp["osd_latency"] = 0
        rbd_count = len(self.result["fio"])
        osd_node_count = len(self.result["ceph"])
        try:
            for node, node_data in self.result["fio"].items():
                tmp["fio_iops"] += float(node_data["fio"]["iops"])
                tmp["fio_bw"] += float(node_data["fio"]["bw"])
                tmp["fio_latency"] += float(node_data["fio"]["lat"])
            tmp["fio_iops"] = "%.3f" % (tmp["fio_iops"])
            tmp["fio_bw"] = "%.3f MB/s" % (tmp["fio_bw"])
            tmp["fio_latency"] = "%.3f msec" % (tmp["fio_latency"]/rbd_count)
        except:
            pass
        if tmp["op_type"] in ["randread", "seqread"]:
            for node, node_data in self.result["ceph"].items():
                tmp["osd_iops"] += numpy.mean(node_data["osd"]["r/s"])*int(node_data["osd"]["disk_num"])
                tmp["osd_bw"] += numpy.mean(node_data["osd"]["rMB/s"])*int(node_data["osd"]["disk_num"])
                tmp["osd_latency"] += numpy.mean(node_data["osd"]["r_await"])
        if tmp["op_type"] in ["randwrite", "seqwrite"]:
            for node, node_data in self.result["ceph"].items():
                tmp["osd_iops"] += numpy.mean(node_data["osd"]["w/s"])*int(node_data["osd"]["disk_num"])
                tmp["osd_bw"] += numpy.mean(node_data["osd"]["wMB/s"])*int(node_data["osd"]["disk_num"])
                tmp["osd_latency"] += numpy.mean(node_data["osd"]["w_await"])
        tmp["osd_iops"] = "%.3f" % (tmp["osd_iops"])
        tmp["osd_bw"] = "%.3f MB/s" % (tmp["osd_bw"])
        tmp["osd_latency"] = "%.3f msec" % (tmp["osd_latency"]/osd_node_count)
        output = []
        output.extend( self.generate_table_from_json(data,'cetune_table', 'runid') )
        return output

    def generate_node_view(self, node_type):
        output = []
        if node_type == 'ceph':
            node_show_list = ["osd", "journal", "cpu", "memory", "nic", "perfcounter_osd", "perfcounter_filestore", "perfcounter_objecter"]
            #node_show_list = ["osd", "journal", "cpu", "memory", "nic"]
        elif node_type == 'vclient':
            node_show_list = ["vdisk","cpu", "memory", "nic"]
        elif node_type == 'client':
            node_show_list = ["cpu", "memory", "nic"]
        elif node_type == 'fio':
            node_show_list = ["fio"]
        else:
            return False
        
        output.append("<div id='%s'>" % node_type)
        for field in node_show_list:
            if len(self.result[node_type].keys()) == 0:
                break
            data = OrderedDict()
            chart_data = OrderedDict()
            for node in self.result[node_type].keys():
                node_data = OrderedDict()
                if "perfcounter" in field:
                    if not field in self.result[node_type][node]:
                        continue
                    for subnode in self.result[node_type][node][field].keys():
                        data[subnode] = OrderedDict()
                        node_data[subnode] = self.result[node_type][node][field][subnode]
                else:
                    data[node] = OrderedDict()
                    node_data[node] = self.result[node_type][node][field]
                for node, tmp in node_data.items():
                    try:
                        for key, value in tmp.items():
                            if not isinstance(value, list):
                                data[node][key] = value
                            else:
                                data[node][key] = "%.3f" % numpy.mean(value)
                                if key not in chart_data:
                                    chart_data[key] = OrderedDict()
                                chart_data[key][node] = value
                    except:
                        pass
            output.extend( self.generate_table_from_json(data,'cetune_table', field) )
            if node_type == 'ceph':
                append_table = True
            else:
                append_table = False
            output.extend( self.generate_line_chart(chart_data, node_type, field, append_table) )
        output.append("</div>")
        return output

    def generate_line_chart(self, data, node_type, field, append_table=False):
        output = []
        common.bash("mkdir -p ../visualizer/include/pic")
        print common.bcolors.OKGREEN + "[LOG]generate %s line chart" % node_type + common.bcolors.ENDC
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
            if append_table:
                line_table = self.generate_line_table_from_json(field_data,'line_table',field_column)
            output.append("<div class='cetune_pic' id='%s_%s_pic'><img src='./include/pic/%s' alt='%s' style='height:400px; width:1000px'>%s</div>" % (field, re.sub('[/%]','',field_column), pic_name, field_column, "\n".join(line_table)))
        return output

        #4. vclient info
    def generate_table_from_json(self, data, classname, node_type):
        output = []
        output.append("<table class='%s'>" % classname)
        output.append("<thead>")
        output.append("<tr>")
        output.append("<th>%s</th>" % node_type)
        for key in data[data.keys()[0]].keys():
            output.append("<th><a id='%s_%s' href='#'>%s</a></th>" % (node_type, re.sub('[/%]','',key), key))
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

    def generate_line_table_from_json(self, data, classname, node_type):
        output = []
        output.append("<table class='%s'>" % classname)
        output.append("<thead>")
        output.append("<tr>")
        output.append("<th>%s</th>" % node_type)
        for key in data.keys():
            output.append("<th><a id='%s_%s' href='#'>%s</a></th>" % (node_type, re.sub('[/%]','',key), key))
        output.append("<tr>")
        output.append("</thead>")
        output.append("<tbody>")
        for i in range(0, len(data[data.keys()[0]])):
            output.append("<tr>")
            output.append("<td>%s</td>" % i)
            for node, node_data in data.items():
                try:
                    output.append("<td>%s</td>" % node_data[i])
                except:
                    output.append("<td></td>")
            output.append("</tr>")
        output.append("</tbody>")
        output.append("</table>")
        return output

def main(args):
    parser = argparse.ArgumentParser(description='Analyzer tool')
    parser.add_argument(
        'operation',
        )
    args = parser.parse_args(args)
    process = Visualizer({})
    func = getattr(process, args.operation)
    if func:
        func()
if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
