#/usr/bin/python
import ConfigParser
import os
import sys
import collections
sys.path.append("../visualizer/")
from create_DB import *

class UserClass(object):
    @classmethod
    def get_user_role(self,username):
        dbpath = "user.db"
        user_role = '1'
        if os.path.exists("user.db"):
            user_role = database.get_user_role(username,dbpath)
        return user_role


    @classmethod
    def check_account(self,key=[' ',' ']):
        dbpath = "user.db"
        result = 'false'
        if os.path.exists("user.db"):
            if database.check_user_exist(key[0],dbpath):
                if database.check_user_mdfive_exist(key[0],dbpath):
                    if database.check_user_passwd(key[0],key[1],dbpath):
                        result = 'true'
                        md = os.popen("echo -n %s | md5sum")
                        mdfive = md.read()
                        database.save_user_mdfive(key[0],mdfive,dbpath)
                    else:
                        result = 'false'
                else:
                    md = os.popen("echo -n %s | md5sum")
                    mdfive = md.read()
                    if database.check_user_mdfive(key[0],mdfive,dbpath):
                        result = 'true'
                    else:
                        resulte = 'false'
            else:
                result = 'false'
        else:
            result = 'false'
        return result

