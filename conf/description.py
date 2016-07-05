#/usr/bin/python
import ConfigParser
import os
import collections

class Description(object):
    @classmethod
    def read_conf_to_dict(self):
        self.cf = ConfigParser.ConfigParser()
        self.dict = collections.OrderedDict()
        if os.path.exists("../conf/help.conf"):
            self.cf.read("../conf/help.conf")
            self.data = self.cf.items("help")
            self.data = sorted(self.data)
            for i in range(len(self.data)):
                self.dict[self.data[i][0]]=self.data[i][1]
        else:
            print "ERROR:help.conf not exists."
        return self.dict

    @classmethod
    def get_all_description(self):
        return Description.read_conf_to_dict()

    @classmethod
    def get_description_by_key(self,key):
	if key in Description.read_conf_to_dict().keys():
            return Description.read_conf_to_dict()[key]
        else:
            print "the key is not exists."
            return ""

class DefaultValue(object):
    @classmethod
    def read_defaultvalue_to_dict(self):
        self.cf = ConfigParser.ConfigParser()
        self.dict = collections.OrderedDict()
        if os.path.exists("../conf/default_value.conf"):
            self.cf.read("../conf/default_value.conf")
            self.data = self.cf.items("default_value")
            self.data = sorted(self.data)
            for i in range(len(self.data)):
                self.dict[self.data[i][0]]=self.data[i][1]
        else:
            print "ERROR:default_value.conf not exists."
        return self.dict

    @classmethod
    def get_defaultvalue_by_key(self,key):
        if key in DefaultValue.read_defaultvalue_to_dict().keys():
            return DefaultValue.read_defaultvalue_to_dict()[key]
        else:
            print "the key is not exists."
            return
