
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
    re_string = f'Logout of.*portal: {ip}.*successful'
    if iscsi_about(re_string, logout_result):
        return True
    else:
        pe(f'iscsi logout to {ip} failed')


def find_session(ip, session_result):
    re_string = f'tcp:.*({ip}):.*'
    if iscsi_about(re_string, session_result):
        return True

def range_uid(unique_str,unique_id, show_result,re_string=''):
    list_name = []
    list_none=[]
    for i in range(unique_id[0], unique_id[1]+1):
        name = f'{re_string}{unique_str}_{i}'
        re_show = re.compile(name)
        re_name = re_show.findall(
            str(show_result))
        if re_name:
            list_name.append(re_name[0])
            print(f'{name} already found')
        else:
            print(f'{name} not found')
            list_none.append(list_none)
            if (unique_id[1]+1-unique_id[0])==len(list_none):
                pe('No lun needs to be deleted')
    return list_name

def one_uid(unique_str, unique_id, res_show_result,re_string=''):
    name = f'{re_string}{unique_str}_{unique_id[0]}'
    re_show = re.compile(name)
    re_name = re_show.findall(
        str(res_show_result))
    if re_name:
        print(f'{name} already found')
        return re_name
    else:
        pe(f'{name} not found')


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
