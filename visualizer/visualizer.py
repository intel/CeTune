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
        self.result = result
        self.output = []
        if path:
            self.path = path
            self.session_name = os.path.basename(path.strip('/'))
        self.dest_dir_remote_bak = self.all_conf_data.get("dest_dir_remote_bak")
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
            output.append("<li><a href=\"#%s\">%s</a></li>" % (node_type, node_type))
        output.append("</ul>")

        for node_type, node_data in self.result.items():
            if not isinstance(node_data, dict):
                continue
            common.printout("LOG","Generating %s view" % node_type)
            output.extend(self.generate_node_view(node_type))

        output.append("</div>")
        output.append("<script>")
        output.append("$( \"#tabs\" ).tabs();")
        output.append("$( \"button\" ).button();")
        output.append("$( \".cetune_pic\" ).hide();")
        output.append("$( \".cetune_table a\" ).click(function(){$(this).parents('.cetune_table').parent().children('.cetune_pic').hide();var id=$(this).attr('id'); $(this).parents('.cetune_table').parent().children('#'+id+'_pic').fadeIn()});")
        output.append("</script>")
        output = self.add_html_framework(output)
        with open("%s/%s.html" % (self.path, self.result["session_name"]), 'w') as f:
            f.write(output)
        common.bash("cp -r %s %s" % ("../visualizer/include/", self.path))
        common.printout("LOG","Session result generated, copy to remote")
        common.bash("scp -r %s %s" % (self.path, self.dest_dir_remote_bak))

        remote_bak, remote_dir = self.dest_dir_remote_bak.split(':')
        output = self.generate_history_view(remote_bak, remote_dir, self.user)

        common.printout("LOG","History view generated, copy to remote")
        with open("%s/cetune_history.html" % self.path, 'w') as f:
            f.write(output)
        common.bash("scp -r %s/cetune_history.html %s" % (self.path, self.dest_dir_remote_bak))
        common.bash("scp -r ../visualizer/include %s" % (self.dest_dir_remote_bak))

    def generate_history_view(self, remote_host="127.0.0.1", remote_dir="/mnt/data/", user='root', html_format=True):
        common.printout("LOG","Generating history view")
        stdout, stderr = common.pdsh(user, [remote_host], "find %s -name '*.html' | grep -v 'cetune_history'|sort -u | while read file;do session=`echo $file | awk -F/ {'print $(NF-1)'}`; awk -v path=\"$file\" -v session=\"$session\" 'BEGIN{find=0;}{if(match($1,\"tbody\")&&find==2){find=0;}if(find==2){if(match($1,\"<tr\"))printf(\"<tr href=\"path\" id=\"session\">\");else print ;};if(match($1,\"div\")&&match($2,\"summary\"))find=1;if(match($1,\"tbody\")&&find==1){find+=1}}' $file; done" % remote_dir, option="check_return")
        res = common.format_pdsh_return(stdout)
        if remote_host not in res:
            common.printout("ERROR","Generating history view failed")
            return False
        output = []
        #output.append("<h1>CeTune History Page</h1>")
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
        output.append("$('.cetune_table tr').dblclick(function(){var path=$(this).attr('href'); window.location=path})")
        output.append("</script>")
        if html_format:
            return self.add_html_framework(output)
        else:
            return "".join(output)

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
        common.printout("LOG","generate %s line chart" % node_type)
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

    def generate_csv_from_json(self, data, classname, node_type):
        output = []
        output.append(node_type+","+",".join(data.keys()))
        for i in range(0, len(data[data.keys()[0]])):
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
