# coding:utf-8

def _init():  # 初始化
    global _global_dict
    _global_dict = {'LOG_ID': 0}


def set_value(key, value):
    """ 定义一个全局变量 """
    _global_dict[key] = value


def get_value(key, defValue=0):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        return _global_dict[key]
    except KeyError:
        return defValue

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

def glo_log(value):
    return get_value('LOG')

def glo_db(value):
    return get_value('DB')

def glo_str(value):
    return get_value('STR')

def glo_id(value):
    return get_value('ID')

def glo_rpl(value):
    return get_value('RPL')

def glo_tsc_id(value):
    return get_value('TSC_ID')

def glo_log_id(value):
    return get_value('LOG_ID')
