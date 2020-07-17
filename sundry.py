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

def dp(str, arg):
    print(f'{str}---------------------\n{arg}')

def change_id_str_to_list(id_str):
    id_list = []
    id_range_list = [int(i) for i in id_str.split(',')]
    if len(id_range_list) not in [1,2]:
        pwe('please verify id format')
    elif len(id_range_list) == 1:
        id_ = id_range_list[0]
        id_list = [id_]
    elif len(id_range_list) == 2:
        for id_ in range(id_range_list[0], id_range_list[1] + 1):
            id_list.append(id_)
    return id_list


def scsi_rescan(ssh, mode):
    logger = consts.glo_log()
    oprt_id = get_oprt_id()
    if mode == 'n':
        cmd = '/usr/bin/rescan-scsi-bus.sh'
        logger.write_to_log('T', 'INFO', 'info', 'start',
                            oprt_id, '    Start to scan SCSI device normal')
    elif mode == 'r':
        cmd = '/usr/bin/rescan-scsi-bus.sh -r'
        logger.write_to_log('T', 'INFO', 'info', 'start',
                            oprt_id, '    Start to scan SCSI device with remove')
    elif mode == 'a':
        cmd = '/usr/bin/rescan-scsi-bus.sh -a'
        logger.write_to_log('T', 'INFO', 'info', 'start',
                            oprt_id, '    Start to scan SCSI device deeply')
    result = get_ssh_cmd(ssh, 'N6YwGtRJ', cmd, oprt_id)
    if result['sts']:
        return True
    else:
        print('  Scan SCSI device failed')
        logger.write_to_log('T', 'INFO', 'warning', 'failed',
                            oprt_id, '  Scan SCSI device failed')


def get_lsscsi(ssh, func_str, oprt_id):
    logger = consts.glo_log()
    print('    Start to list all SCSI device')
    logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                        '    Start to list all SCSI device')
    cmd_lsscsi = 'lsscsi'
    # result_lsscsi = SSH.execute_command(cmd_lsscsi)
    result_lsscsi = get_ssh_cmd(ssh, func_str, cmd_lsscsi, oprt_id)
    if result_lsscsi['sts']:
        return result_lsscsi['rst'].decode('utf-8')
    else:
        print(f'  Command {cmd_lsscsi} execute failed')
        logger.write_to_log('T', 'INFO', 'warning', 'failed', oprt_id,
                            f'  Command "{cmd_lsscsi}" execute failed')


def get_all_scsi_disk(re_string, lsscsi_result):
    return re_findall(re_string, lsscsi_result)


def get_the_disk_with_lun_id(all_disk):
    logger = consts.glo_log()
    lun_id = consts.glo_id()
    dict_id_disk = dict(all_disk)
    if str(lun_id) in dict_id_disk.keys():
        blk_dev_name = dict_id_disk[str(lun_id)]
        return blk_dev_name
    else:
        print(f'no disk device with SCSI ID {lun_id} found')
        logger.write_to_log('T', 'INFO', 'warning', 'failed',
                            '', f'no disk device with SCSI ID {lun_id} found')

def get_ssh_cmd(ssh_obj, unique_str, cmd, oprt_id):
    """
    Execute command on ssh connected host.If it is replay mode, get relevant data from the log.
    :param ssh_obj:SSH connection object
    :param unique_str:The specific character described in the method calling this function
    :param cmd:Command to be executed
    :param oprt_id:The unique id for the operation here
    :return:Command execution result
    """
    logger = consts.glo_log()
    global RPL
    RPL = consts.glo_rpl()
    if RPL == 'no':
        logger.write_to_log('F', 'DATA', 'STR', unique_str, '', oprt_id)
        logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd)
        result_cmd = ssh_obj.execute_command(cmd)
        logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_cmd)
        return result_cmd
    elif RPL == 'yes':
        print(f'Replay process of executing command ... {cmd} ...')
        db = consts.glo_db()
        db_id, oprt_id = db.find_oprt_id_via_string(
            consts.glo_tsc_id(), unique_str)
        info_start = db.get_info_start(oprt_id)
        if info_start:
            print(info_start)
        result_cmd = db.get_cmd_result(oprt_id)
        if result_cmd:
            result = eval(result_cmd)
        else:  # 数据库取不到数据
            result = None
        info_end = db.get_info_finish(oprt_id)
        if info_end:
            print(info_end)
        change_pointer(db_id)
        # print(f'  Change DB ID to: {db_id}')
        return result


def pwe(print_str):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    logger = consts.glo_log()
    print(print_str)
    logger.write_to_log('T', 'INFO', 'error', 'exit', '', print_str)
    sys.exit()

def pwce(print_str):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    :param print_str: Strings to be printed and recorded
    """
    logger = consts.glo_log()
    print(print_str)
    logger.write_to_log('T', 'INFO', 'error', 'exit', '', print_str)
    log_file = clct_env(consts.glo_tid())
    logger.write_to_log('T', 'DATA', 'clct', '', '', f'Save debug data to file /var/log/{log_file}')
    sys.exit()

def _compare(name, name_list):
    if name in name_list:
        return name
    elif 'res_'+name in name_list:
        return 'res_'+name

def get_to_del_list(name_list):
    '''
    Generate some names with a range of id values and determine whether these names exist。
        name is lun name /resource name
        list_name is used to return the list value
        ???????????
    '''
    uni_str = consts.glo_str()
    id_list = consts.glo_id_list()
    to_del_list = []

    if uni_str and id_list:
        for id_ in id_list:
            str_ = f'{uni_str}_{id_}'
            name = _compare(str_, name_list)
            if name:
                to_del_list.append(name)
    elif uni_str:
        for name in name_list:
            if uni_str in name:
                to_del_list.append(name)
    elif id_list:
        for id_ in id_list:
            str_ = f'_{id_}'
            for name in name_list:
                if str_ in name:
                    to_del_list.append(name)
    else:
        to_del_list = name_list
    return to_del_list

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

def prt_res_to_del(str_,res_list):
    print(f'{str_:<15} to be delete:')
    print('-------------------------------------------------------------')
    if res_list:
        for i in range(len(res_list)):
            res_name = res_list[i]
            print(f'{res_name:<18}', end='')
            if (i + 1) % 5 == 0:
                print()
    else:
        print('None')
    print()

# def getshow(unique_str, id_list, name_list):
#     '''
#     Determine the lun to be deleted according to regular matching
#     '''
#     if id_list:
#         list_name = get_list_name(logger, unique_str, id_list, name_list)
#         return list_name
#     else:
#         return name_list


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


def change_pointer(new_id):
    consts.set_glo_log_id(new_id)



def re_findall(re_string, tgt_string):
    logger = consts.glo_log()
    re_login = re.compile(re_string)
    re_result = re_login.findall(tgt_string)
    oprt_id = get_oprt_id()
    logger.write_to_log('T', 'OPRT', 'regular', 'findall',
                        oprt_id, {re_string: tgt_string})
    logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, re_result)
    return re_result


def iscsi_login(tgt_ip, ssh, func_str, oprt_id):
    '''
    Discover iSCSI login session, if no, login to vplx
    '''
    logger = consts.glo_log()
    cmd = f'iscsiadm -m discovery -t st -p {tgt_ip} -l'
    result_iscsi_login = get_ssh_cmd(ssh, func_str, cmd, oprt_id)
    if result_iscsi_login['sts']:
        result_iscsi_login = result_iscsi_login['rst'].decode('utf-8')
        re_string = f'Login to.*portal: ({tgt_ip}).*successful'
        if re_findall(re_string, result_iscsi_login):
            print(f'  iSCSI login to {tgt_ip} successful')
            logger.write_to_log('T', 'INFO', 'info', 'finish',
                                '', f'  iSCSI login to {tgt_ip} successful')
            return True
        else:
            pwe(f'  iSCSI login to {tgt_ip} failed')


def find_session(tgt_ip, ssh, func_str, oprt_id):
    '''
    Execute the command and check up the status of session
    '''
    logger = consts.glo_log()
    # self.logger.write_to_log('INFO', 'info', '', 'start to execute the command and check up the status of session')
    cmd = 'iscsiadm -m session'
    logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                        '    Execute the command and check up the status of session')
    result_session = get_ssh_cmd(ssh, func_str, cmd, oprt_id)
    if result_session['sts']:
        result_session = result_session['rst'].decode('utf-8')
        re_session = re.compile(f'tcp:.*({tgt_ip}):.*')
        if re_findall(re_session, result_session):
            # print('    iSCSI already login to VersaPLX')
            logger.write_to_log('T', 'INFO', 'info', 'finish',
                                oprt_id, f'    ISCSI already login to {tgt_ip}')
            return True
        else:
            print('  iSCSI not login to VersaPLX, Try to login')
            logger.write_to_log('T', 'INFO', 'warning', 'failed', oprt_id,
                                '  ISCSI not login to VersaPLX, Try to login')


if __name__ == 'main':
    pass
    # get_disk_dev()
