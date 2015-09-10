import os, sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import common
import web
from web import form
import json
from visualizer import *
import re

render = web.template.render('templates/')
urls = (
  '/', 'index',
  '/configuration/(.+)', 'configuration',
  '/monitor/(.+)', 'monitor',
  '/results/(.+)', 'results'
)

class index:
    def GET(self):
        web.seeother('/static/index.html')

class configuration:
    all_conf = common.Config("../conf/all.conf")

    def GET(self, function_name = ""):
        return common.eval_args( self, function_name, web.input() )

    def get_group(self,request_type):
        request_type_list = ["workflow","cluster","system","ceph","benchmark","analyzer"]
        if request_type in request_type_list:
            return self.all_conf.get_group(request_type)

    def get_group_list(self):
        return self.all_conf.get_group_list()

    def set_conf(self, key, value):
        return self.all_conf.set_conf(key, value)

    def check_conf(self, key, value):
        return self.all_conf.check_conf(key, value)

class monitor:
    def GET(self, function_name = ""):
        return common.eval_args( self, function_name, web.input() )

    def tail_console(self, timestamp=None):
        output = common.read_file_after_stamp("../conf/cetune_console.log", timestamp)
        res = {}
        re_res = re.search('\[(.+)\]\[',output[-1])
        if re_res:
            res["timestamp"] = re_res.group(1)
        res["content"] = []
        for line in output[1:]:
            color = "#999"
            if "[LOG]" in line:
                color = "#CCFF99"
            if "[WARNING]" in line:
                color = "yellow"
            if "[ERROR]" in line:
                color = "red"
            res["content"].append("<div style='color:%s'>%s</div>" % (color, line))
        res["content"] = "".join(res["content"])
        return res

class results:
    def GET(self, function_name = ""):
        return common.eval_args( self, function_name, web.input() )

    def get_summary(self):
        view = visualizer.Visualizer({})
        output = view.generate_history_view("127.0.0.1","/mnt/data/","root",False)
        html = ""
        for line in output.split('\n'):
            html += line.rstrip('\n')
        return html

    def get_detail(self, session_name):
        path = "%s/%s/%s.html" % ("/mnt/data", session_name, session_name)
        output = False
        html = ""
        with open( path, 'r') as f:
            for line in f.readlines():
                if "<body>" in line:
                    output = True
                    continue
                if "</body>" in line:
                    output = False
                    break
                if output:
                    html += line.rstrip('\n')
        return html

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
