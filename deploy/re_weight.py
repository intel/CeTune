import os,sys
lib_path = os.path.abspath(os.path.join('../conf/'))
sys.path.append(lib_path)
from conf import *
import subprocess
import time

class Reweight:
    def __init__(self):
        self.oload = 101
        self.max_change = 0.01
        self.max_change_osds = 2
        self.target = 0.05
        self.max_time_re = 300
        self.max_count_re = 1000
        self.t_start = 0
        self.t_end = 0
        self.count_re = 0
        self.result = []
        self.isFitTarget = False

    def Doreweight(self, oload, max_change, max_change_osds):
        subprocess.Popen("ceph osd reweight-by-pg %s %s %s" % (oload, max_change, max_change_osds), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    def GetPgs(self):
        p = subprocess.Popen("ceph osd df | awk '{print $9}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        tmpList =  [x.replace('\n','') for x in p.stdout.readlines() if x != '\n']
        if 'PGS' in tmpList:
            wightList = [int(x) for x in tmpList[tmpList.index('PGS')+1 : ]]
            return wightList
        else:
            print tmpList
            return []
    
    def GetValueDiff(self, pgs):
        if pgs:
            diff = round((max(pgs)-min(pgs))*1.0/max(pgs),3)
        else:
            diff = -1
        self.result.append([self.count_re, diff])
        print self.count_re, diff, pgs
        return diff
    
    def main(self):
        for i in range(3):
            self.t_start = time.time()
            while True:
                diff = self.GetValueDiff(self.GetPgs())
                self.t_end = time.time()
                self.count_re += 1
                if diff < self.target or self.max_count_re < self.count_re or self.max_time_re < self.t_end - self.t_start:
                    if diff < self.target:
                        self.isFitTarget = True
                        common.printout("LOG", "reweight complete.")
                    break
                else:
                    self.Doreweight(self.oload, self.max_change, self.max_change_osds)
                    time.sleep(0.5)
            if self.isFitTarget:
                break
            else:
                self.target += 0.01
        if not self.isFitTarget:
            common.printout("WARNING", "after reweight, the diff of PGS also too large!")

def do():
    re = Reweight()
    re.main()
