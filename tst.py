#  coding: utf-8

import connect
import sundry as s
import time
import sys
import os
import re
import log
import traceback

host = '10.203.1.199'
port = 22
user = 'root'
password = 'password'
timeout = 3

SSH = None
cmd = 'pwd'

l = log.Log(2331)

def init_ssh():
    global SSH
    if not SSH:
        SSH = connect.ConnSSH(host, port, user, password, timeout, l)
    else:
        pass

def f():
    init_ssh()
    w = SSH.execute_command(cmd)



    print(w)

class d(object):
    def __init__(self):
        init_ssh()
        w  = SSH.execute_command('pwd')
        print(w)

class c(object):
    def __init__(self):
        init_ssh()
        print(SSH.execute_command('ls /bin'))


def e():
    try:
        2/0
    except Exception as e:
        print(e)
        print('----')
        print(str(traceback.format_exc()))

if __name__ == "__main__":
    e()
    pass

