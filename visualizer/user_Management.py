import os
import sys
import argparse
from create_DB import *

def main(arge):

    parser = argparse.ArgumentParser()

    parser.add_argument('-o',
            action='store',
            dest='simple_value',
            help="[add]:add a new user;[del]:delete a user;[list]:list all user;[up]:update a user role;")

    parser.add_argument('--user_name',
            action='append',
            dest='collection',
            help='the user account')
    parser.add_argument('--passwd',
            action='append',
            dest='collection',
            help='the account password')
    parser.add_argument('--role',
            action='append',
            dest='collection',
            help='set user role [readonly]:only show CeTune configuration and test log. \
                                [admin]:can use CeTune test.')

    params = parser.parse_args()
    dbpath = "../webui/user.db"
    if not os.path.exists(dbpath):
        database.createUserTB(dbpath)
    try:
        if len(params.collection) == 0:
            os.system('python user_Management.py --help')
    except:
        os.system('python user_Management.py --help')
    if params.simple_value == "add":
        try:
            if not database.check_user_exist(params.collection[0],dbpath):
                if len(params.collection) == 3:
                    if len(params.collection[0])>20:
                        print 'WARNNING:The username length cannot be longer than 20 characters.'
                    elif len(params.collection[1])>15:
                        print 'WARNNING:The passwd length cannot be longer than 20 characters.'
                    elif params.collection[2] not in ['admin','readonly']:
                        print "WARNNING:user role must be 'admin' or 'readonly'."
                    else:
                        database.add_User(list(params.collection),dbpath)
                else:
                    print "WARNNING:invalid number of parameters!"
            else:
                print '============================'
                print "userid:'%s' is already exists!"%params.collection[0]
        except:
            print "ERROR:add a new user failed."

    if params.simple_value == "del":
        try:
            if database.check_user_exist(params.collection[0],dbpath):
                database.delete_user(params.collection[0],dbpath)
            else:
                print '============================'
                print "userid:'%s' is not exists!"%params.collection[0]
        except:
            print 'ERROR:delete user by userid failed!'

    if params.simple_value == "list":
        user_list = database.select_user_list(dbpath)
        print '============================'
        print 'user_name:   role:'
        for i in user_list:
            print i[0],'       ',i[1]

    if params.simple_value == "up":
        try:
            if database.check_user_exist(params.collection[0],dbpath):
                if params.collection[1] not in ['admin','readonly']:
                    print "WARNNING:user role must be 'admin' or 'readonly'."
                else:
                    database.update_user_role(params.collection[0],params.collection[1],dbpath)
            else:
                print '============================'
                print "userid:'%s' is not exists!"%params.collection[0]
        except:
            print 'ERROR:update user role failed!'


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
