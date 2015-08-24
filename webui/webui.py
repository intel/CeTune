import os, sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import common
import web
from web import form
import json

render = web.template.render('templates/')
urls = (
  '/', 'index',
  '/configuration/(.+)', 'configuration',
  '/monitor', 'monitor',
  '/results', 'results'
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

class monitor:
    def GET(self):
        return render.monitor()

class results:
    def GET(self):
        return render.results()


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
