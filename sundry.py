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


def generate_iqn(num):
    lun_id=consts.glo_id()
    iqn=f"iqn.1993-08.org.debian:01:2b129695b8bbmaxhost{lun_id}.{num}"
    consts.append_glo_iqn_list(iqn)


class DebugLog(object):
    def __init__(self, ssh_obj, debug_folder, host):
        # print(debug_folder)
        self.dbg_folder = debug_folder
        self.SSH = ssh_obj
        self.host = host
        self._mk_debug_folder()

    def _mk_debug_folder(self):
        # -m:增加判断,用file命令结果判断,如果已存在,则不创建
        output = self.SSH.execute_command(f'mkdir {self.dbg_folder}')
        self.SSH.execute_command(f'mkdir {self.dbg_folder}/{self.host}')
        if output['sts']:
            pass
        else:
            prt(f'Can not create folder {self.dbg_folder} to stor debug log', 3, 2)
            sys.exit()

    def prepare_debug_log(self, cmd_list):
        for cmd in cmd_list:
            output = self.SSH.execute_command(cmd)
            if output['sts']:
                time.sleep(0.1)
            else:
                prt(f'Collect log command "{cmd}" execute failed.', 3, 2)

    def get_debug_log(self, local_folder):
        dbg_file = f'{self.dbg_folder}.tar'
        self.SSH.execute_command(f'mv {self.dbg_folder}/*.log {self.dbg_folder}/{self.host}')
        self.SSH.execute_command(f'mv {self.dbg_folder}/*.tar {self.dbg_folder}/{self.host}')
        self.SSH.execute_command(f'tar cvf {dbg_file} -C {self.dbg_folder} {self.host}')
        self.SSH.download(dbg_file, local_folder)

class Iscsi(object):
    def __init__(self,ssh_obj,tgt_ip):
        self.SSH = ssh_obj
        self.tgt_ip=tgt_ip

    def create_iscsi_session(self):
        pwl('Check up the status of session', 2, '', 'start')
        if not self.find_session():
            pwl(f'No session found, start to login to {self.tgt_ip}', 3, '', 'start')
            if self.iscsi_login():
                pwl(f'Succeed in logining to {self.tgt_ip}', 4, 'finish')
            else:
                pwce(f'Can not login to {self.tgt_ip}', 4, 2)

        else:
            pwl(f'The iSCSI session already logged in to {self.tgt_ip}', 3)

    def disconnect_iscsi_session(self,tgt_iqn):
        if self.find_session():
            if self.iscsi_logout(tgt_iqn):
                pwl(f'Success in logout {self.tgt_ip}',2,'','finish')
                return True
            else:
                pwce(f'Failed to logout {self.tgt_ip}',4,2)
        else:
            pwl(f'The iSCSI session already logged out to {self.tgt_ip}',3)
            return True
    
    def iscsi_logout(self,tgt_iqn):
        cmd=f'iscsiadm -m node -T {tgt_iqn} --logout '
        oport_ip=get_oprt_id()
        results=get_ssh_cmd(self.SSH,'HuTg1LaQ', cmd, oport_ip)
        if results:
            if results['sts']:
                re_string=f'Logout of.*portal: ({self.tgt_ip}).*successful'
                re_result=re_search(re_string,results['rst'].decode('utf-8'))
                if re_result:
                    return True
            else:
                pwce(f'Can not logout {self.tgt_ip}', 4, 2)
        
        else:
            handle_exception()

    def iscsi_login(self):
        '''
        Discover iSCSI login session, if no, login to vplx
        '''
        func_str = 'rgjfYl3K'
        oprt_id = get_oprt_id()
        cmd = f'iscsiadm -m discovery -t st -p {self.tgt_ip} -l'
        result_iscsi_login = get_ssh_cmd(self.SSH, func_str, cmd, oprt_id)
        if result_iscsi_login:
            if result_iscsi_login['sts']:
                result_iscsi_login = result_iscsi_login['rst'].decode('utf-8')
                re_string = f'Login to.*portal: ({self.tgt_ip}).*successful'
                if re_search(re_string, result_iscsi_login):
                    pwl(f'iSCSI login to {self.tgt_ip} successful',3,'','finish')
                    return True
                else:
                    pwce(f'iSCSI login to {self.tgt_ip} failed',3,warning_level=2)

        else:
            handle_exception()
    # -m:string 和 oprt id 不用传递过来,在内部定义即可
    def find_session(self):
        '''
        Execute the command and check up the status of session
        '''
        func_str = 'V9jGOP1i'
        oprt_id = get_oprt_id()
        cmd = 'iscsiadm -m session'
        result_session = get_ssh_cmd(self.SSH, func_str, cmd, oprt_id)
        if result_session:
            if result_session['sts']:
                result_session = result_session['rst'].decode('utf-8')
                re_session = f'tcp:.*({self.tgt_ip}):.*'
                if re_search(re_session, result_session):
                    return True
        else:
            handle_exception()

    def restart_iscsi(self):
        cmd=f'systemctl restart iscsid open-iscsi'
        oport_id=get_oprt_id()
        results=get_ssh_cmd(self.SSH,'Uksjdkqi',cmd,oport_id)
        if results:
            if results['sts']:
                pwl('Success in restarting iscsi service',2,'','finish')
            else:
                pwe('Failed to restart iscsi service',2,2)
        else:
            handle_exception()


def dp(str, arg):
    print(f'{str}---------------------\n{arg}')


def change_id_str_to_list(id_str):
    id_list = []
    id_range_list = [int(i) for i in id_str]
    
    if len(id_range_list) not in [1, 2]:
        pwce('Please verify id format', 2, 2)
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
        pwl('Start to scan SCSI device with normal way', 3, '', 'start')
    elif mode == 'r':
        cmd = '/usr/bin/rescan-scsi-bus.sh -r'
        pwl('Start to scan SCSI device after removing disk', 2, '', 'start')
    elif mode == 'a':
        cmd = '/usr/bin/rescan-scsi-bus.sh -a'
        pwl('Start to scan SCSI device in depth', 3, '', 'start')

    if consts.glo_rpl() == 'no':
        result = ssh.execute_command(cmd)
        if result['sts']:
            return True
        else:
            pwl('Scan SCSI device failed', 4, '', 'finish')
    else:
        return True


def get_lsscsi(ssh, func_str, oprt_id):
    pwl('Start to get the list of all SCSI device',3,oprt_id,'start')
    cmd_lsscsi = 'lsscsi'
    result_lsscsi = get_ssh_cmd(ssh, func_str, cmd_lsscsi, oprt_id)
    if result_lsscsi:
        if result_lsscsi['sts']:
            return result_lsscsi['rst'].decode('utf-8')
        else:
            pwe(f'Failed to excute Command "{cmd_lsscsi}"',4,1)
    else:
        handle_exception()

def re_search(re_string, tgt_string):
    logger = consts.glo_log()
    re_object = re.compile(re_string)
    re_result = re_object.search(tgt_string)
    oprt_id = get_oprt_id()
    logger.write_to_log('T', 'OPRT', 'regular', 'search',
                        oprt_id, {re_string: tgt_string})
    logger.write_to_log('F', 'DATA', 'regular', 'search', oprt_id, re_result)
    return re_result

def get_the_disk_with_lun_id(all_disk):
    lun_id = str(consts.glo_id())
    dict_id_disk = dict(all_disk)
    if lun_id in dict_id_disk.keys():
        disk_dev = dict_id_disk[lun_id]
        return disk_dev


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
            result = None
        if db_id:
            change_pointer(db_id)
        return result



def _compare(name, name_list):
    if name in name_list:
        return name
    elif 'res_' + name in name_list:
        return 'res_' + name


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
                if name.endswith(str_):
                    to_del_list.append(name)
    else:
        to_del_list = name_list
    return to_del_list


def prt_res_to_del(str_, res_list):
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
    re_object = re.compile(re_string)
    re_result = re_object.findall(tgt_string)
    oprt_id = get_oprt_id()
    logger.write_to_log('T', 'OPRT', 'regular', 'findall',
                        oprt_id, {re_string: tgt_string})
    logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, re_result)
    return re_result





def ran_str(num):
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    str_ = ''
    for i in range(num):
        str_ += random.choice(chars)
    return str_


def prt(str, level=0, warning_level=0):
    if isinstance(warning_level, int):
        warning_str = '*' * warning_level
    else:
        warning_str = ''
    indent_str = '  ' * level + str
    title_str = '---- ' + str + ' '
    rpl = consts.glo_rpl()

    if rpl == 'no':
        if level == 0:
            print()
            print(f'{title_str:-<80}')
        else:
            print(f'|{warning_str:<4}{indent_str:<70}{warning_str:>4}|')

    else:
        if warning_level == 'exception':
            print(' exception infomation '.center(105, '*'))
            print(str)
            print(f'{" exception infomation ":*^105}', '\n')
            return

        db = consts.glo_db()
        time = db.get_time_via_str(consts.glo_tsc_id(), str)
        if not time:
            time = ''

        if level == 0:
            print(f'{title_str:-<105}')
        else:
            print(f'|{warning_str:<4} Re:{time:<20} {indent_str:<70}{warning_str:>4}|')


def pwl(str, level, oprt_id=None, type=None):
    # rpl = 'no'
    rpl = consts.glo_rpl()
    if rpl == 'no':
        logger = consts.glo_log()
        prt(str, level)
        logger.write_to_log('T', 'INFO', 'info', type, oprt_id, str)

    elif rpl == 'yes':
        prt(str, level)


def prt_log(str, level, warning_level):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    logger = consts.glo_log()

    #-m:这里也是要调用s.prt还是啥,指定级别,不同地方调用要用不同的级别.
    rpl = consts.glo_rpl()
    format_width = 80
    if rpl == 'yes':
        format_width = 105
        db = consts.glo_db()
        oprt_id = db.get_oprt_id_via_db_id(consts.glo_tsc_id(), consts.glo_log_id())
        prt(str + f'.oprt_id:{oprt_id}', level, warning_level)
    elif rpl == 'no':
        prt(str, level, warning_level)

    if warning_level == 1:
        logger.write_to_log('T', 'INFO', 'warning', 'fail', '', str)
    elif warning_level == 2:
        logger.write_to_log('T', 'INFO', 'error', 'exit', '', str)
        # print(f'{"":-^{format_width}}','\n')
        # sys.exit()


def pwe(str, level, warning_level):
    rpl = consts.glo_rpl()
    prt_log(str, level, warning_level)

    if warning_level == 2:
        if rpl == 'no':
            sys.exit()
        else:
            raise consts.ReplayExit

def pwce(str, level, warning_level):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    rpl = consts.glo_rpl()
    prt_log(str,level,warning_level)
    if rpl == 'no':
        debug_log.collect_debug_log()
        print('debug')
    if warning_level == 2:
        if rpl == 'no':
            sys.exit()
        else:
            raise consts.ReplayExit


def handle_exception(str='',level=0,warning_level=0):
    rpl = consts.glo_rpl()
    if rpl == 'yes':
        db = consts.glo_db()
        exception_info = db.get_exception_info(consts.glo_tsc_id())
        if exception_info:
            prt('The transaction was interrupted because of an exception',1,warning_level=2)
            prt(exception_info, warning_level='exception')
            raise consts.ReplayExit
        else:
            oprt_id = db.get_oprt_id_via_db_id(consts.glo_tsc_id(),consts.glo_log_id())
            prt(f'Unable to get data from the logfile.oprt_id:{oprt_id}',3,2)
            raise consts.ReplayExit

    else:
        pwce(str,level,warning_level)


if __name__ == '__main__':
    pass
    # pwl('3333',0)
    # pwl('3askldjasdasldkjaskdl',1)
