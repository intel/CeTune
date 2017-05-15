import os, sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
sys.path.append('/usr/local/lib/python2.7/dist-packages/web/')
from conf import *
from workflow import *
import web
from web.contrib.template import render_jinja
import json
from visualizer import *
from login import *
import re
import subprocess
import signal
import markdown2
#import markdown
import codecs
import ConfigParser
import collections
from web import form
from login import *

urls = (
  '/', 'index',
  '/login', 'login',
  '/logout', 'logout',
  '/configuration/(.+)', 'configuration',
  '/monitor/(.+)', 'monitor',
  '/description/(.+)','description',
  '/results/(.+)', 'results',
)

#render = web.template.render('templates/')
render = render_jinja('templates/',encoding = 'utf-8',)
web.config.debug = False
app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})
web.cache = {}
web.cache["tuner_thread"] = None
web.cache["cetune_status"] = "idle"

class index:
    def GET(self):
        if session.get('logged_in',False):
            return render.index(username = session.username)
        raise web.seeother('/login')

class login:
    def GET(self):
        return render.login(error_msg = "")

    def POST(self):
        i = web.input()
        username = i.get('username')
        passwd = i.get('passwd')
        if UserClass.check_account([username,passwd]) == 'true':
            session.logged_in = True
            session.username = username
            session.userrole = UserClass.get_user_role(username)
            web.setcookie('system_mangement', '', 60)
            raise web.seeother('/')
        else:
            return render.login(error_msg = "Failed:username or password is invalid !!")

class logout:
    def GET(self):
        session.logged_in = False
        raise web.seeother("/login")

class configuration:

    def GET(self, function_name = ""):
        print "get_param:%s" % str(web.input())
        return common.eval_args( self, function_name, web.input() )

    def POST(self, function_name = ""):
        print "post_param:%s" % str(web.input())
        return common.eval_args( self, function_name, web.input() )

    def user_role(self):
        output = session.userrole
        web.header("Content-Type","application/json")
        return json.dumps(output)

    def get_group(self,request_type):
        conf = handler.ConfigHandler()
        web.header("Content-Type","application/json")
        return json.dumps(conf.get_group(request_type))

    def get_help(self):
        conf = handler.ConfigHandler()
        web.header("Content-Type","application/json")
        return json.dumps(conf.get_help())
        #return json.dumps(description.get_descripation())

    def get_guide(self):
        input_file = codecs.open("%s/README.md" % lib_path, mode="r", encoding="utf-8")
        text = input_file.read()
        html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables"])
        #html = markdown.markdown(text, 'codehilite')
        return html

    def set_config(self, request_type, key, value):
        if session.get('userrole') == 'admin':
            conf = handler.ConfigHandler()
            web.header("Content-Type","application/json")
            return json.dumps(conf.set_config(request_type, key, value))

    def check_engine(self, engine_list):
        if session.get('userrole') == 'admin':
            conf = handler.ConfigHandler()
            web.header("Content-Type","application/json")
            return json.dumps(conf.check_engine(engine_list.split(',')))

    def check_testcase(self):
        if session.get('userrole') == 'admin':
            conf = handler.ConfigHandler()
            web.header("Content-Type","application/json")
            return json.dumps(conf.check_testcase())

    def del_config(self, request_type, key):
        if session.get('userrole') == 'admin':
            conf = handler.ConfigHandler()
            web.header("Content-Type","application/json")
            return json.dumps(conf.del_config(request_type, key))

    def execute(self):
        if web.cache["tuner_thread"]:
            return "false"
        if session.get('userrole') == 'admin':
            common.clean_console()
            #thread_num = tuner.main(["--by_thread"])
            thread_num = subprocess.Popen("cd ../workflow/; python workflow.py", shell=True)
            if thread_num:
                web.cache["tuner_thread"] = thread_num
                web.cache["cetune_status"] = "running"
                os.system("echo 'execute' > ../conf/execute_op_type.conf")

    def cancel_all(self):
        if session.get('userrole') == 'admin':
            if web.cache["tuner_thread"]:
                pid = web.cache["tuner_thread"].pid
                os.kill((pid+1), signal.SIGINT)
                web.cache["cetune_status"] = "running, caught cancel request, working to close]"
                os.system("echo 'cancel_all' > ../conf/execute_op_type.conf")
                #web.cache["tuner_thread"].wait()
                #web.cache["tuner_thread"] = None
                #web.cache["cetune_status"] = "idle"
                return "true"
            else:
                return "false"

    def cancel_one(self):
        if session.get('userrole') == 'admin':
            if web.cache["tuner_thread"]:
                pid = web.cache["tuner_thread"].pid
                os.kill((pid+1), signal.SIGINT)
                web.cache["cetune_status"] = "running, caught cancel request, working to close]"
                os.system("echo 'cancel_one' > ../conf/execute_op_type.conf")
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
        all_conf = config.Config("../conf/all.conf")
        user = all_conf.get('user')
        controller = all_conf.get('head')
        output = common.get_ceph_health(user, controller)
        output["cetune_status"] = web.cache["cetune_status"]
        web.header("Content-Type","application/json")
        return json.dumps(output)
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

class description:
    def GET(self, function_name = ""):
        return common.eval_args( self, function_name, web.input() )

    def POST(self, function_name = ""):
        data = web.input()
        tr_id = data["tr_id"]
        new_description = data["celltext"]
        if session.get('userrole')== 'admin':
            view = visualizer.Visualizer({})
            view.update_report_list_db(tr_id,new_description)
        #return common.eval_args( self, function_name, web.input() )

    def update(self):
        data = web.input()
        tr_id = data["tr_id"]
        new_description = data["celltext"]
        if session.get('userrole')=='admin':
            view = visualizer.Visualizer({})
            view.update_report_list_db(tr_id,new_description)

    def get_help(self):
	view = visualizer.Visualizer({})
        output = view.generate_description_view(False)
        if not output:
            return ""
        html = ""
        for line in output.split('\n'):
            html += line.rstrip('\n')
        return html

class results:
    def GET(self, function_name = ""):
        return common.eval_args( self, function_name, web.input() )
    def POST(self, function_name = ""):
        print web.input()
        return common.eval_args( self, function_name, web.input() )

    def delete_result(self, request_type,key):
        if session.get('userrole') == 'admin':
            conf = config.Config("../conf/all.conf")
            dest_dir = conf.get("dest_dir")
            os.system("rm -rf %s/%s-*"%(dest_dir,key))

    def get_summary(self):
        view = visualizer.Visualizer({})
        conf = config.Config("../conf/all.conf")
        dest_dir = conf.get("dest_dir",loglevel="LVL6")
        output = view.generate_history_view("127.0.0.1",dest_dir,"root",False)
        if not output:
            return ""
        html = ""
        for line in output.split('\n'):
            html += line.rstrip('\n')
        return html

    def get_detail(self, session_name):
        conf = config.Config("../conf/all.conf")
        dest_dir = conf.get("dest_dir")
        path = "%s/%s/%s.html" % (dest_dir, session_name, session_name)
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
        conf = config.Config("../conf/all.conf")
        dest_dir = conf.get("dest_dir")
        path = "%s/%s/include/pic/%s" % (dest_dir, session_name, pic_name)
        print path
        return open( path, "rb" ).read()

    def get_detail_csv(self, session_name, csv_name):
        web.header("Content-Type", "text/csv")
        conf = config.Config("../conf/all.conf")
        dest_dir = conf.get("dest_dir")
        path = "%s/%s/include/csv/%s" % (dest_dir, session_name, csv_name)
        print path
        web.header('Content-disposition', 'attachment; filename=%s_%s' % (session_name, csv_name))
        return open( path, "r" ).read()

    def get_detail_zip(self, session_name, detail_type="conf"):
        web.header("Content-Type", "application/zip")
        web.header('Content-disposition', 'attachment; filename=%s_%s.zip' % (session_name, detail_type))
        conf = config.Config("../conf/all.conf")
        dest_dir = conf.get("dest_dir")
        path = "%s/%s/" % (dest_dir, session_name)
        if not os.path.isfile("%s/%s_%s.zip" % ( path, session_name, detail_type)):
            common.bash("cd %s; zip %s_%s.zip -r %s;" % (path, session_name, detail_type, detail_type))
        return open( "%s/%s_%s.zip" % ( path, session_name, detail_type), "rb" ).read()

class defaults_pic:
    def GET(self):
        return None

if __name__ == "__main__":
    app.run()
