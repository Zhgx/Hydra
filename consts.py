# coding:utf-8

class ReplayExit(Exception):
    "replay时，输出日志中的异常信息后，此次replay事务也随之停止"
    pass


def _init():
    global _global_dict
    _global_dict = {}
    _global_dict['LOG_ID'] = 0
    _global_dict['RPL'] = 'no'
    _global_dict['LOG_SWITCH'] = 'yes'

def set_value(key, value):
    """ 定义一个全局变量 """
    _global_dict[key] = value


def get_value(key, dft_val = None):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        return _global_dict[key]
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

def get_cmd_debug_sys(debug_folder,host):
    cmd_debug_sys = [
            # f'dmesg > {debug_folder}/dmesg.log',
            f'echo -- date&time: >> {debug_folder}/{host}_sys_info.log',
            f'date >> {debug_folder}/{host}_sys_info.log',
            f'echo -- host name: >> {debug_folder}/{host}_sys_info.log',
            f'hostname >> {debug_folder}/{host}_sys_info.log',
            f'echo -- uname -a: >> {debug_folder}/{host}_sys_info.log',
            f'uname -a >> {debug_folder}/{host}_sys_info.log',
            f'echo -- uname -r: >> {debug_folder}/{host}_sys_info.log',
            f'uname -r >> {debug_folder}/{host}_sys_info.log',
            f'echo -- uname -m: >> {debug_folder}/{host}_sys_info.log',
            f'uname -m >> {debug_folder}/{host}_sys_info.log',
            f'echo -- CPU Info: >> {debug_folder}/{host}_sys_info.log',
            f'cat /proc/cpuinfo >> {debug_folder}/{host}_sys_info.log',
            f'echo -- Memory Info: >> {debug_folder}/{host}_sys_info.log',
            f'cat /proc/meminfo >> {debug_folder}/{host}_sys_info.log',
            f'echo -- network setting: >> {debug_folder}/{host}_sys_info.log',
            f'ifconfig >> {debug_folder}/{host}_sys_info.log',
            f'echo -- : >> {debug_folder}/{host}_sys_info.log',
            f'env >> {debug_folder}/{host}_sys_info.log',
            f'uname -a >> {debug_folder}/{host}_sys_info.log',
            f'echo --environment: >> {debug_folder}/{host}_sys_info.log',
            f'env >> {debug_folder}/{host}_sys_info.log',
            f'echo --dmesg: >> {debug_folder}/{host}_sys_info.log',
            f'dmesg >> {debug_folder}/{host}_sys_info.log',
            f'tar cvf {debug_folder}/{host}_syslog.tar /var/log/syslog*'
        ]
    return cmd_debug_sys

def get_cmd_debug_drbd(debug_folder, host):
    cmd_debug_drbd = [
            f'tar -cvf {debug_folder}/{host}_drbd_conf_file.tar /etc/drbd.d/*',
            f'drbdadm status >> {debug_folder}/{host}_drbd.log',
        ]
    return cmd_debug_drbd

def get_cmd_debug_crm(debug_folder, host):
    cmd_debug_crm = [
            f'crm res show >> {debug_folder}/{host}_crm.log'
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

