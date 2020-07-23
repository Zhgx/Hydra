#  coding: utf-8
import random
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

import connect

import debug_log


class DebugLog(object):
    def __init__(self, ssh_obj, debug_folder):
        # print(debug_folder)
        self.dbg_folder = debug_folder
        self.SSH = ssh_obj
        self._mk_debug_folder()

    def _mk_debug_folder(self):
        #-m:增加判断,用file命令结果判断,如果已存在,则不创建
        output = self.SSH.execute_command(f'mkdir {self.dbg_folder}')
        if output['sts']:
            pass
        else:
            prt(f'Can not create folder {self.dbg_folder} to stor debug log',3,2)
            sys.exit()

    def prepare_debug_log(self, cmd_list):
        for cmd in cmd_list:
            output = self.SSH.execute_command(cmd)
            if output['sts']:
                time.sleep(0.1)
            else:
                prt(f'Collect log command "{cmd}" execute failed.',3,2)

    def get_debug_log(self, local_folder):
        dbg_file = f'{self.dbg_folder}.tar'
        self.SSH.execute_command(f'tar cvf {dbg_file} -C {self.dbg_folder} .')
        self.SSH.download(dbg_file, local_folder)


def dp(str, arg):
    print(f'{str}---------------------\n{arg}')

def change_id_str_to_list(id_str):
    id_list = []
    id_range_list = [int(i) for i in id_str.split(',')]
    if len(id_range_list) not in [1,2]:
        #-m:提示格式
        pwe('Please verify id format',2,2)
    elif len(id_range_list) == 1:
        id_ = id_range_list[0]
        id_list = [id_]
    elif len(id_range_list) == 2:
        for id_ in range(id_range_list[0], id_range_list[1] + 1):
            id_list.append(id_)
    return id_list



def scsi_rescan(ssh, mode):
    if mode == 'n':
        cmd = '/usr/bin/rescan-scsi-bus.sh'
        pwl('Start to scan SCSI device with normal way',3,'','start')
    elif mode == 'r':
        cmd = '/usr/bin/rescan-scsi-bus.sh -r'
        pwl('Start to scan SCSI device after removing disk',3,'','start')
    elif mode == 'a':
        cmd = '/usr/bin/rescan-scsi-bus.sh -a'
        pwl('Start to scan SCSI device in depth',3,'','start')

    if consts.glo_rpl() == 'no':
        result = ssh.execute_command(cmd)
        if result['sts']:
            return True
        else:
            pwl('Scan SCSI device failed',4,'','finish')
    else:
        return True



def get_lsscsi(ssh, func_str, oprt_id):
    logger = consts.glo_log()
    pwl('Start to get the list of all SCSI device',3,oprt_id,'start')
    cmd_lsscsi = 'lsscsi'
    result_lsscsi = get_ssh_cmd(ssh, func_str, cmd_lsscsi, oprt_id)
    if result_lsscsi['sts']:
        return result_lsscsi['rst'].decode('utf-8')
    else:
        #-m:s.pwl
        print(f'  Command {cmd_lsscsi} execute failed')
        logger.write_to_log('T', 'INFO', 'warning', 'failed', oprt_id,
                            f'  Command "{cmd_lsscsi}" execute failed')

#-m:这代码蠢不,..看你们有没有人指出来
# def get_all_scsi_disk(re_string, lsscsi_result):
#     return re_findall(re_string, lsscsi_result)


def get_the_disk_with_lun_id(all_disk):
    logger = consts.glo_log()
    lun_id = str(consts.glo_id())
    dict_id_disk = dict(all_disk)
    if lun_id in dict_id_disk.keys():
        disk_dev = dict_id_disk[lun_id]
        return disk_dev
    #-m:考虑将意外判断放在外面调用部分
    else:
        #-m:第几级打印? 因为有重试,可能要考虑一下重试打印是否增加级
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
        db = consts.glo_db()
        db_id, oprt_id = db.find_oprt_id_via_string(
            consts.glo_tsc_id(), unique_str)
        result_cmd = db.get_cmd_result(oprt_id)
        if result_cmd:
            result = eval(result_cmd)
        else:
            # pwl(f'Failed to execute command:{cmd}',4)
            result = None
        if db_id:
            change_pointer(db_id)
        return result


def pwce(print_str, log_folder):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    :param print_str: Strings to be printed and recorded
    """
    logger = consts.glo_log()
    #-m:这里也是要调用s.prt还是啥,指定级别,不同地方调用要用不同的级别.
    print(print_str)
    logger.write_to_log('T', 'INFO', 'error', 'exit', '', print_str)

    debug_log_folder = debug_log.collect_debug_log()
    logger.write_to_log('T', 'DATA', 'clct', '', '', f'Save debug data to folder {debug_log_folder}')

    sys.exit()

def _compare(name, name_list):
    if name in name_list:
        return name
    elif 'res_'+name in name_list:
        return 'res_'+name

def get_to_del_list(name_list):
    '''
    Get the list of the resource which will be deleted.
    : Get the resource according to the unique_string and unique_id，and check whether it is exist.
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


def prt_res_to_del(str_,res_list):
    print(f'{str_:<15} to be delete:')
    print('-------------------------------------------------------------')
    for i in range(len(res_list)):
        res_name = res_list[i]
        print(f'{res_name:<18}', end='')
        if (i + 1) % 5 == 0:
            print()
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


def iscsi_login(tgt_ip, ssh):
    '''
    Discover iSCSI login session, if no, login to vplx
    '''
    func_str = 'rgjfYl3K'
    oprt_id = get_oprt_id()
    cmd = f'iscsiadm -m discovery -t st -p {tgt_ip} -l'
    result_iscsi_login = get_ssh_cmd(ssh, func_str, cmd, oprt_id)
    if result_iscsi_login['sts']:
        result_iscsi_login = result_iscsi_login['rst'].decode('utf-8')
        re_string = f'Login to.*portal: ({tgt_ip}).*successful'
        if re_findall(re_string, result_iscsi_login):
            pwl(f'iSCSI login to {tgt_ip} successful',3,'','finish')
            return True
        else:
            pwe(f'iSCSI login to {tgt_ip} failed',3,warning_level=2)

#-m:string 和 oprt id 不用传递过来,在内部定义即可
def find_session(tgt_ip, ssh):
    '''
    Execute the command and check up the status of session
    '''
    func_str = 'V9jGOP1i'
    oprt_id = get_oprt_id()
    cmd = 'iscsiadm -m session'
    result_session = get_ssh_cmd(ssh, func_str, cmd, oprt_id)
    if result_session:
        if result_session['sts']:
            result_session = result_session['rst'].decode('utf-8')
            re_session = f'tcp:.*({tgt_ip}):.*'
            if re_findall(re_session, result_session):
                return True
    else:
        raise consts.ReplayExit

def ran_str(num):
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    str_ = ''
    for i in range(num):
        str_ += random.choice(chars)
    return str_


def prt(str, level=0, warning_level=0):
    if isinstance(warning_level,int):
        warning_str = '*' * warning_level
    indent_str = '  ' * level + str
    rpl = consts.glo_rpl()

    if rpl == 'no':
        if level == 0:
            print()
            indent_str = '** ' + str + ' **'
            print(f'{indent_str:-^80}')
        else:
            print(f'|{warning_str:<4}{indent_str:<70}{warning_str:>4}|')


    else:
        if warning_level == 'exception':
            print(' exception infomation '.center(105, '*'))
            print(str)
            print(f'{" exception infomation ":*^105}','\n')
            return

        db = consts.glo_db()
        time = db.get_time_via_str(consts.glo_tsc_id(),str)
        if not time:
            time = ''

        if level == 0:
            indent_str = '** ' + str + ' **'
            print(f'{indent_str:-^105}')
        else:
            print(f'|{warning_str:<4} Re:{time:<20} {indent_str:<70}{warning_str:>4}|')





def pwl(str, level, oprt_id=None, type=None):
    # rpl = 'no'
    rpl = consts.glo_rpl()
    if rpl == 'no':
        logger = consts.glo_log()
        prt(str,level)
        logger.write_to_log('T', 'INFO', 'info', type, oprt_id, str)

    elif rpl == 'yes':
        prt(str,level)

def prt_log(str,level,warning_level):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    logger = consts.glo_log()

    #-m:这里也是要调用s.prt还是啥,指定级别,不同地方调用要用不同的级别.
    prt(str,level,warning_level)
    if warning_level == 1:
        logger.write_to_log('T', 'INFO', 'warning', 'fail', '', str)
    elif warning_level == 2:
        logger.write_to_log('T', 'INFO', 'error', 'exit', '', str)
        # debug_log.collect_debug_log()
        # sys.exit()


def pwe(str,level,warning_level):
    prt_log(str,level,warning_level)
    if warning_level == 2:
        sys.exit()

def pwce(str,level,warning_level):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    prt_log(str,level,warning_level)
    debug_log.collect_debug_log()
    if warning_level == 2:
        sys.exit()


def handle_exception():
    db = consts.glo_db()
    exception_info = db.get_exception_info(consts.glo_tsc_id())
    if exception_info:
        prt('The transaction was interrupted because of an exception',1,warning_level=2)
        prt(exception_info, warning_level='exception')
        raise consts.ReplayExit
    else:
        prt('Unable to get data from the database',3,1)


if __name__ == '__main__':
    pass
    # pwl('3333',0)
    # pwl('3askldjasdasldkjaskdl',1)


