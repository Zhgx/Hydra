#  coding: utf-8
import sundry
import sys
import re
import time
import os
import getpass
import traceback
import socket
from random import shuffle
import log


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


def range_uid(logger, unique_str, ids, show_result, resource_name):
    '''
    Generate some names with a range of id values and determine whether these names exist。
        name is lun name /resource name
        list_name is used to return the list value
    '''
    list_name = []
    string = decide_string(resource_name)
    for i in range(ids[0], ids[1]):
        name = f'{string}{unique_str}_{i}'
        if name in show_result:
            list_name.append(name)
    print(f'{resource_name}:')
    print(print_format(list_name))
    return list_name


def print_format(list_name):
    '''
    Data alignment and division every ten name rows
    '''
    name = ''
    for i in range(len(list_name)):
        name = name.ljust(4)+list_name[i]+'  '
        if i % 10 == 9:
            name = name+'\n' + ''.ljust(4)
    return name


def decide_string(resource_name):
    '''
    Determine name is resource name or lun name
    '''
    if resource_name == 'storage':
        return ''
    else:
        return 'res_'


def one_uid(logger, unique_str, unique_id, show_result, resource_name):
    '''
    Generate a name with a fixed id value and determine whether these names exist。
        name is lun name /resource name
    '''
    string = decide_string(resource_name)
    name = f'{string}{unique_str}_{unique_id[0]}'
    if name in show_result:
        name = [name]
        print(f'{resource_name}:')
        print(print_format(name))
        return name
    else:
        print(logger, f'{name} not found')


def re_getshow(logger, unique_str, list_id, re_string, show_result, resource_name):
    '''
    Determine the lun to be deleted according to regular matching
    '''
    re_show = re.compile(re_string)
    re_result = re_show.findall(show_result)
    # print(re_result)
    if re_result:
        if list_id:
            if len(list_id) == 2:
                return range_uid(logger, unique_str, list_id, re_result, resource_name)
            elif len(list_id) == 1:
                return one_uid(logger, unique_str, list_id, re_result, resource_name)
            else:
                pwe(logger, 'please enter a valid value')
        else:
            print(f'{resource_name}:')
            print(print_format(re_result))
            return re_result


def get_disk_dev(lun_id, re_string, lsscsi_result, dev_label, logger):
    '''
    Use re to get the blk_dev_name through lun_id
    '''
    # print(lsscsi_result)
    # self.logger.write_to_log('GetDiskPath','host','find_device',self.logger.host)
    re_find_path_via_id = re.compile(re_string)
    # self.logger.write_to_log('GetDiskPath','regular_before','find_device',lsscsi_result)
    re_result = re_find_path_via_id.findall(lsscsi_result)
    # self.logger.write_to_log('DATA', 'output', 're_result', re_result)
    oprt_id = sundry.get_oprt_id()
    logger.write_to_log('T', 'OPRT', 'regular', 'findall',
                        oprt_id, {re_find_path_via_id: re_string})
    logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, re_result)
    if re_result:
        dict_id_disk = dict(re_result)
        if lun_id in dict_id_disk.keys():
            blk_dev_name = dict_id_disk[lun_id]
            # self.logger.write_to_log('GetDiskPath','return','find_device',blk_dev_name)
            return blk_dev_name
        else:
            print(f'no disk device with SCSI ID {lun_id} found')
            logger.write_to_log('T', 'INFO', 'warning', 'failed',
                                '', f'no disk device with SCSI ID {lun_id} found')

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
            self.logger.write_to_log(
                'F', 'DATA', 'debug', 'exception', '', str(traceback.format_exc()))
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
