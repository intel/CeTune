#/usr/bin/python
import ConfigParser
import os
import collections

class UserClass(object):
    @classmethod
    def read_conf_to_dict(self):
        self.cf = ConfigParser.ConfigParser()
        self.dict = collections.OrderedDict()
        if os.path.exists("account.conf"):
            self.cf.read("account.conf")
            self.data = self.cf.items("account")
            self.data = sorted(self.data)
            for i in range(len(self.data)):
                self.dict[self.data[i][0]]=self.data[i][1]
        else:
            print "ERROR:account.conf not exists."
        return self.dict

    @classmethod
    def get_all_account(self):
        return UserClass.read_conf_to_dict()

    @classmethod
    def check_account(self,key=[' ',' ']):
        result = 'false'
        if key[0] in UserClass.read_conf_to_dict().keys():
            if UserClass.read_conf_to_dict()[key[0]] == key[1]:
                result = 'true'
                return result
            return result
        else:
            print "ERROR:user not exists."
            return result
