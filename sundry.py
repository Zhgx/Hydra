
#  coding: utf-8
import sys
import re


def pe(print_str):
    'print and exit'
    print(print_str)
    sys.exit()


def iscsi_about(re_string, result):
    if result:
        result = result.decode('utf-8')
        re_str = re.compile(re_string)
        re_result = re_str.findall(result)
        if re_result:
            return True


def iscsi_login(ip, login_result):
    re_string = f'Login to.*portal: ({ip}).*successful'
    if iscsi_about(re_string, login_result):
        print(f'iscsi login to {ip} succeed')
        return True
    else:
        pe(f'iscsi login to {ip} failed')


def iscsi_logout(ip, logout_result):
    re_string = r'Logout of \w* successful.'
    if iscsi_about(re_string, logout_result):
        return True
    else:
        pe(f'iscsi logout to {ip} failed')


def find_session(ip, session_result):
    re_string = f'tcp:.*({ip}):.*'
    if iscsi_about(re_string, session_result):
        return True


class GetDiskPath(object):
    def __init__(self, lun_id, re_string, lsscsi_result, str_target):
        self.id = str(lun_id)
        self.re_string = re_string
        self.target = str_target
        self.lsscsi_result = lsscsi_result.decode('utf-8')

    def find_device(self):
        '''
        Use re to get the blk_dev_name through lun_id
        '''
        re_find_path_via_id = re.compile(self.re_string)
        re_result = re_find_path_via_id.findall(self.lsscsi_result)
        if re_result:
            dict_stor = dict(re_result)
            if self.id in dict_stor.keys():
                blk_dev_name = dict_stor[self.id]
                return blk_dev_name

    def explore_disk(self):
        '''
            Scan and get the device path from VersaPLX or Host
        '''

        if self.lsscsi_result and self.lsscsi_result is not True:
            dev_path = self.find_device()
            if dev_path:
                return dev_path
            else:
                pe(f'Did not find the new LUN from {self.target}')
        else:
            pe(f'Command "lsscsi" failed on {self.target}')
