import os, sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import *
from tuner import *
import web
import json
from visualizer import *
import re
import subprocess
import signal

render = web.template.render('templates/')
urls = (
  '/', 'index',
  '/configuration/(.+)', 'configuration',
  '/monitor/(.+)', 'monitor',
  '/results/(.+)', 'results'
)

web.cache = {}
web.cache["tuner_thread"] = None
web.cache["cetune_status"] = "idle"

class index:
    def GET(self):
        web.seeother('/static/index.html')

class configuration:

    def GET(self, function_name = ""):
        print "get_param:%s" % str(web.input())
        return common.eval_args( self, function_name, web.input() )

    def POST(self, function_name = ""):
        print "post_param:%s" % str(web.input())
        return common.eval_args( self, function_name, web.input() )

    def get_group(self,request_type):
        conf = handler.ConfigHandler()
        web.header("Content-Type","application/json")
        return json.dumps(conf.get_group(request_type))

    def set_config(self, request_type, key, value):
        conf = handler.ConfigHandler()
        web.header("Content-Type","application/json")
        return json.dumps(conf.set_config(request_type, key, value))

    def del_config(self, request_type, key):
        conf = handler.ConfigHandler()
        web.header("Content-Type","application/json")
        return json.dumps(conf.del_config(request_type, key))

    def execute(self):
        if web.cache["tuner_thread"]:
            return "false"
        common.clean_console()
        #thread_num = tuner.main(["--by_thread"])
        thread_num = subprocess.Popen("cd ../tuner/; python tuner.py", shell=True)
        if thread_num:
            web.cache["tuner_thread"] = thread_num
            web.cache["cetune_status"] = "running"

    def cancel(self):
        if web.cache["tuner_thread"]:
            pid = web.cache["tuner_thread"].pid
            os.kill((pid+1), signal.SIGINT)
            web.cache["cetune_status"] = "running, caught cancel request, working to close]"
            web.cache["tuner_thread"].wait()
            web.cache["tuner_thread"] = None
            web.cache["cetune_status"] = "idle"
            return "true"
        else:
            return "false"

class monitor:
    def GET(self, function_name = ""):
        return common.eval_args( self, function_name, web.input() )
    def POST(self, function_name = ""):
        print web.input()
        return common.eval_args( self, function_name, web.input() )
    def cetune_status(self):
        if web.cache["tuner_thread"]:
            if web.cache["tuner_thread"].poll() != None:
                web.cache["tuner_thread"] = None
                web.cache["cetune_status"] = "idle"
        cetune_status = web.cache["cetune_status"]
        return "CeTune Status:%s    Ceph Status: %s" % (cetune_status, common.get_ceph_health())
    def tail_console(self, timestamp=None):
        if timestamp == "undefined":
            timestamp = None
        output = common.read_file_after_stamp("../conf/cetune_console.log", timestamp)
        res = {}
        if len(output) == 0:
            return json.dumps(res)

        res["content"] = []
        re_res = re.search('\[(.+)\]\[',output[-1])
        if re_res:
            res["timestamp"] = re_res.group(1)
        for line in output[1:]:
            color = "#999"
            if "[LOG]" in line:
                #color = "#CCFF99"
                color = "#009900"
            if "[WARNING]" in line:
                #color = "yellow"
                color = "#FFA500"
            if "[ERROR]" in line:
                #color = "red"
                color = "#DC143C"
            res["content"].append("<div style='color:%s'>%s</div>" % (color, line))
        res["content"] = "".join(res["content"])
        web.header("Content-Type","application/json")
        return json.dumps(res)

class results:
    def GET(self, function_name = ""):
        return common.eval_args( self, function_name, web.input() )
    def POST(self, function_name = ""):
        print web.input()
        return common.eval_args( self, function_name, web.input() )

    def get_summary(self):
        view = visualizer.Visualizer({})
        output = view.generate_history_view("127.0.0.1","/mnt/data/","root",False)
        if not output:
            return ""
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
        web.header("Content-Type", "text/plain")
        return html

    def get_detail_pic(self, session_name, pic_name):
        web.header("Content-Type", "images/png")
        path = "%s/%s/include/pic/%s" % ("/mnt/data", session_name, pic_name)
        print path
        return open( path, "rb" ).read()

    def get_detail_csv(self, session_name, csv_name):
        web.header("Content-Type", "text/csv")
        path = "%s/%s/include/csv/%s" % ("/mnt/data", session_name, csv_name)
        print path
        web.header('Content-disposition', 'attachment; filename=%s_%s' % (session_name, csv_name))
        return open( path, "r" ).read()

class defaults_pic:
    def GET(self):
        return None

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
