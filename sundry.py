#  coding: utf-8
import sundry
import consts
import logdb

import sys
import re
import time
import os
import getpass
import traceback
import socket
from random import shuffle
import log


def get_ssh_cmd(ssh_obj, unique_str, cmd, oprt_id):
    gloabl RPL
    RPL = consts._rpl()
    if RPL == 'no':
        logger.write_to_log('F', 'DATA', 'STR', unique_str, '', oprt_id)
        logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd)
        result_cmd = ssh_obj.execute_command(cmd)
        logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_cmd)
        return result_cmd
    elif RPL == 'yes':

        db_id, oprt_id = DB.find_oprt_id_via_string(consts.get_tid(), unique_str)
        info_start = DB.get_info_start(oprt_id)
        if info_start:
            print(info_start)
        result_cmd = DB.get_cmd_result(oprt_id)
        if result_cmd:
            result = eval(result_cmd)
        else:# 数据库取不到数据
            result = None
        info_end = db.get_info_finish(oprt_id)
        if info_end:
            print(info_end)
        s.change_pointer(db_id)
        # print(f'  Change DB ID to: {db_id}')
        return result

def pwe(logger, print_str):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    print(print_str)
    logger.write_to_log('T', 'INFO', 'error', 'exit', '', print_str)
    sys.exit()


def iscsi_about(re_string, result):
    if result:
        result = result.decode('utf-8')
        re_str = re.compile(re_string)
        re_result = re_str.findall(result)
        if re_result:
            return True


def iscsi_login(logger, ip, login_result):
    re_string = f'Login to.*portal: ({ip}).*successful'
    if iscsi_about(re_string, login_result):
        print(f'iscsi login to {ip} succeed')
        return True
    else:
        pwe(logger, f'iscsi login to {ip} failed')


def find_session(ip, session_result):
    re_string = f'tcp:.*({ip}):.*'
    if iscsi_about(re_string, session_result):
        return True


def compare(name, show_result):
    if name in show_result:
        return name
    elif 'res_'+name in show_result:
        return 'res_'+name


def get_list_name(logger, unique_str, ids, show_result):
    '''
    Generate some names with a range of id values and determine whether these names exist。
        name is lun name /resource name
        list_name is used to return the list value
    '''
    if len(ids) == 2:
        list_name = []
        for i in range(ids[0], ids[1]):
            name = f'{unique_str}_{i}'
            list_name.append(compare(name, show_result))
        return list_name
    elif len(ids) == 1:
        name = f'{unique_str}_{ids[0]}'
        return [compare(name, show_result)]
    else:
        pwe(logger, 'please enter a valid value')


def print_format(list_name):
    '''
    Data alignment and division every ten name rows
    '''
    name = ''
    for i in range(len(list_name)):
        if list_name[i]:
            name = name.ljust(4)+list_name[i]+'  '
        if i % 10 == 9:
            name = name+'\n' + ''.ljust(4)
    return name


def getshow(logger, unique_str, list_id, show_result):
    '''
    Determine the lun to be deleted according to regular matching
    '''
    if list_id:
        list_name = get_list_name(logger, unique_str, list_id, show_result)
        return list_name
    else:
        return show_result


def get_disk_dev(lun_id, re_string, lsscsi_result, dev_label, logger):
    '''
    Use re to get the blk_dev_name through lun_id
    '''
    # print(lsscsi_result)
    # self.logger.write_to_log('GetDiskPath','host','find_device',self.logger.host)
    re_find_path_via_id = re.compile(re_string)
    # self.logger.write_to_log('GetDiskPath','regular_before','find_device',lsscsi_result)
    re_result = re_find_path_via_id.findall(lsscsi_result)
    oprt_id = sundry.get_oprt_id()
    logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {re_string: lsscsi_result})
    logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, re_result)
    if re_result:
        dict_id_disk = dict(re_result)
        if lun_id in dict_id_disk.keys():
            blk_dev_name = dict_id_disk[lun_id]
            return blk_dev_name
        else:
            print(f'no disk device with SCSI ID {lun_id} found')
            logger.write_to_log('T', 'INFO', 'warning', 'failed', '', f'no disk device with SCSI ID {lun_id} found')

    else:
        print(f'no equal {dev_label} disk device found')
        logger.write_to_log('T', 'INFO', 'warning', 'failed',
                            '', f'no equal {dev_label} disk device found')


def record_exception(func):
    """
    Decorator
    Get exception, throw the exception after recording
    :param func:Command binding function
    """

    def wrapper(self, *args):
        try:
            return func(self, *args)
        except Exception as e:
            self.logger.write_to_log('F', 'DATA', 'debug', 'exception', '', str(traceback.format_exc()))
            raise e

    return wrapper


def get_transaction_id():
    return int(time.time())


def get_oprt_id():
    time_stamp = str(get_transaction_id())
    str_list = list(time_stamp)
    shuffle(str_list)
    return ''.join(str_list)


def get_username():
    return getpass.getuser()


def get_hostname():
    return socket.gethostname()


# Get the path of the program


def get_path():
    return os.getcwd()


def change_pointer(new_id):
    consts.set_value('LID', new_id)


if __name__ == 'main':
    get_disk_dev()
