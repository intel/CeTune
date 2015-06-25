import os, sys
lib_path = os.path.abspath(os.path.join('..'))
sys.path.append(lib_path)
from conf import common
import web
from web import form

render = web.template.render('templates/')

class index:
    def GET(self):
        return render.index()

    def POST(self):
        return web.data()

class configuration:
    all_conf = common.Config("../conf/all.conf")

    def GET(self):
        cluster_conf = self.all_conf.get_all()
        return self.dict_to_input_table(cluster_conf)

    def dict_to_input_table(self, data):
        output = []
        output.append("<table class='CeTune_config'>")
        output.append("<thead>")
        output.append("<tr><th>all.conf</th><th>Cluster Configuration</th></tr>")
        output.append("</thead>")
        output.append("<tbody>")
        for key, value in data.items():
            if isinstance(value, list):
                temp = []
                for subvalue in value:
                    temp.append("<li style='display:inline; margin:auto 20px auto 0px;  white-space:nowrap;'>"+subvalue+"</li>") 
                value = "\n".join(temp)
            output.append("<tr><th>"+key+"</th><td>"+str(value)+"</td></tr>")
        output.append("</tbody>")
        return "\n".join(output)

class monitor:
    def GET(self):
        return render.monitor()

class results:
    def GET(self):
        return render.results()

urls = (
  '/', 'index',
  '/configuration', 'configuration',
  '/monitor', 'monitor',
  '/results', 'results'
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
