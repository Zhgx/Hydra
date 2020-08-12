# coding:utf-8

class ReplayExit(Exception):
    "replay时，输出日志中的异常信息后，此次replay事务也随之停止"
    pass


def _init():
    global _GLOBAL_DICT
    _GLOBAL_DICT = {}
    _GLOBAL_DICT['LOG_ID'] = 0
    _GLOBAL_DICT['RPL'] = 'no'
    _GLOBAL_DICT['LOG_SWITCH'] = 'yes'
    _GLOBAL_DICT['IQN_LIST'] = []

def set_value(key, value):
    """ 定义一个全局变量 """
    _GLOBAL_DICT[key] = value


def get_value(key, dft_val = None):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        return _GLOBAL_DICT[key]
    except KeyError:
        return dft_val

def set_glo_log(value):
    set_value('LOG', value)


def set_glo_db(value):
    set_value('DB', value)


def set_glo_str(value):
    set_value('STR', value)


def set_glo_id(value):
    set_value('ID', value)


def set_glo_rpl(value):
    set_value('RPL', value)


def set_glo_tsc_id(value):
    set_value('TSC_ID', value)


def set_glo_log_id(value):
    set_value('LOG_ID', value)


def set_glo_log_switch(value):
    set_value('LOG_SWITCH', value)


def set_glo_id_list(value):
    set_value('ID_LIST', value)

def append_glo_iqn_list(value):
    _GLOBAL_DICT['IQN_LIST'].append(value)

def set_glo_iqn_list(value):
    set_value('IQN_LIST', value)

def set_glo_iqn(value):
    set_value('IQN', value)

def set_glo_cap(value):
    set_value('CAP',value)


def glo_log():
    return get_value('LOG')


def glo_db():
    return get_value('DB')


def glo_str():
    return get_value('STR')


def glo_id():
    return get_value('ID')


def glo_rpl():
    return get_value('RPL')


def glo_tsc_id():
    return get_value('TSC_ID')


def glo_log_id():
    return get_value('LOG_ID')


def glo_log_switch():
    return get_value('LOG_SWITCH')


def glo_id_list():
    return get_value('ID_LIST')

def glo_iqn_list():
    return get_value('IQN_LIST')

def glo_iqn():
    return get_value('IQN')

def glo_cap():
    return get_value('CAP')

def get_cmd_debug_sys(debug_folder,host):
    cmd_debug_sys = [
            # f'dmesg > {debug_folder}/dmesg.log',
            f'echo -- date&time: >> {debug_folder}/sys_info.log',
            f'date >> {debug_folder}/sys_info.log',
            f'echo -- host name: >> {debug_folder}/sys_info.log',
            f'hostname >> {debug_folder}/sys_info.log',
            f'echo -- uname -a: >> {debug_folder}/sys_info.log',
            f'uname -a >> {debug_folder}/sys_info.log',
            f'echo -- uname -r: >> {debug_folder}/sys_info.log',
            f'uname -r >> {debug_folder}/sys_info.log',
            f'echo -- uname -m: >> {debug_folder}/sys_info.log',
            f'uname -m >> {debug_folder}/sys_info.log',
            f'echo -- CPU Info: >> {debug_folder}/sys_info.log',
            f'cat /proc/cpuinfo >> {debug_folder}/sys_info.log',
            f'echo -- Memory Info: >> {debug_folder}/sys_info.log',
            f'cat /proc/meminfo >> {debug_folder}/sys_info.log',
            f'echo -- network setting: >> {debug_folder}/sys_info.log',
            f'ifconfig >> {debug_folder}/sys_info.log',
            f'echo -- : >> {debug_folder}/sys_info.log',
            f'env >> {debug_folder}/sys_info.log',
            f'uname -a >> {debug_folder}/sys_info.log',
            f'echo --environment: >> {debug_folder}/sys_info.log',
            f'env >> {debug_folder}/sys_info.log',
            f'echo --dmesg: >> {debug_folder}/sys_info.log',
            f'dmesg >> {debug_folder}/sys_info.log',
            f'tar cvf {debug_folder}/syslog.tar /var/log/syslog*'
        ]
    return cmd_debug_sys

def get_cmd_debug_drbd(debug_folder, host):
    cmd_debug_drbd = [
            f'tar -cvf {debug_folder}/drbd_conf_file.tar -C /etc drbd.d',
            f'drbdadm status >> {debug_folder}/drbd.log',
        ]
    return cmd_debug_drbd

def get_cmd_debug_crm(debug_folder, host):
    cmd_debug_crm = [
            f'crm res show >> {debug_folder}/crm.log'
        ]
    return cmd_debug_crm

def get_cmd_debug_stor():
    cmd_debug = [
            'lun show',
            'lun show -m',
            'iscsi status',
            'iscsi session show',
            'iscsi initiator show'
        ]
    return cmd_debug

