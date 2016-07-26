#!/usr/bin/python

import sqlite3

class database(object):
    @classmethod
    def createTB(self,dbpath):
        conn = sqlite3.connect(dbpath)
        print "Opened database successfully";

        conn.execute('''create table tb_report
                (runid_tr varchar(300) primary key not null,
                runid int not null,
                timestamp varchar(50) not null,
                status varchar(15) not null,
                description varchar(50) not null,
                opsize varchar(10) not null,
                optype varchar(20) not null,
                qd varchar(10) not null,
                driver varchar(10) not null,
                snnumber int not null,
                cnnumber int not null,
                worker int not null,
                runtime int not null,
                iops float not null,
                bw float not null,
                latency float not null,
                sniops float not null,
                snbw float not null,
                snlatency float not null
                );''')
        print"tb_report created successfully."

        conn.close()
        print "Closed database successfully";

    @classmethod
    def insert_to_TB(self,data,dbpath):
        rowdata = data
        conn = sqlite3.connect(dbpath)
        print "Opened database successfully";
        if rowdata[2] == '':
            rowdata[2] =='None'
        if rowdata[4] == '':
            rowdata[4] = 'None'
        sqlstr = "insert into tb_report (runid,runid_tr,timestamp,status,description,opsize,optype,qd,driver,snnumber,cnnumber,worker,runtime,iops,bw,latency,sniops,snbw,snlatency) values ("+rowdata[1]+",'"+rowdata[0]+"','"+rowdata[2]+"','"+rowdata[3]+"','"+rowdata[4]+"','"+rowdata[5]+"','"+rowdata[6]+"','"+rowdata[7]+"','"+rowdata[8]+"',"+rowdata[9]+","+rowdata[10]+","+rowdata[11]+","+rowdata[12]+",'"+rowdata[13]+"','"+rowdata[14]+"','"+rowdata[15]+"','"+rowdata[16]+"','"+rowdata[17]+"','"+rowdata[18]+"')"
        #sqlstr = "insert into tb_report (runid,runid_tr,utatus,description,opsize,optype,qd,driver,snnumber,cnnumber,worker,runtime,iops,bw,latency,sniops,snbw,snlatency) values (%d,'%s','%s','%s','%s','%s','%s','%s',%d,%d,%d,%d,%f,%f,%f,%f,%f,%f)"%(rowdata[1],rowdata[0],rowdata[2],rowdata[3],rowdata[4],rowdata[5],rowdata[6],rowdata[7],rowdata[8],rowdata[9],rowdata[10],rowdata[11],rowdata[12],rowdata[13],rowdata[14],rowdata[15],rowdata[16],rowdata[17])
        conn.execute(sqlstr)
        conn.commit()
        print "Add data to TB successfully."
        conn.close()
        print "Closed database successfully";

    @classmethod
    def select_report_list(self,dbpath):
        conn = sqlite3.connect(dbpath)
        print "Opened database successfully";

        data = conn.execute("select * from tb_report")
        report_list =[]
        for i in data:
            report_list.append(i)
        conn.close()
        print "Closed database successfully";
        return report_list

    @classmethod
    def check_case_exist(self,runid,dbpath):
        conn = sqlite3.connect(dbpath)
        print "Opened database successfully";
        sqlstr = "select * from tb_report where runid_tr = '%s'"%(runid)
        data = conn.execute(sqlstr)
        list_data = []
        for i in data:
            list_data.append(i)
        conn.close()
        print "Closed database successfully";
        if len(list_data) == 0:
            return False
        else:
            return True

    @classmethod
    def delete_case_by_runid(self,runid,dbpath):
        conn = sqlite3.connect(dbpath)
        print "Opened database successfully";

        sqlstr = "delete from tb_report where runid_tr = '%s'"%(runid)
        data = conn.execute(sqlstr)
        conn.commit()
        conn.close()
        print "Closed database successfully";

    @classmethod
    def get_runid_list(self,dbpath):
        conn = sqlite3.connect(dbpath)
        print "Opened database successfully";

        sqlstr = "select runid_tr from tb_report"
        data = conn.execute(sqlstr)
        runid_list =[]
        for i in data:
            runid_list.extend(list(i))
        conn.close()
        print "Closed database successfully";
        return runid_list

    @classmethod
    def update_by_runid(self,runid,column,value,dbpath):
        conn = sqlite3.connect(dbpath)
        print "Opened database successfully";

        if database.check_case_exist(runid,dbpath):
            sqlstr = "update tb_report set "+column+" = '"+value+"' where runid_tr = '%s'"%(runid)
            conn.execute(sqlstr)
            print "Update "+runid+":"+column+" successfully";
            conn.commit()
            print "Closed database successfully";
            conn.close()
            return True
        else:
            conn.close()
            print "Closed database successfully";
            return False





