# coding:utf-8

def _init():  # 初始化
    global _global_dict
    _global_dict = {'ID': 0}


def set_value(key, value):
    """ 定义一个全局变量 """
    _global_dict[key] = value


def get_value(key, defValue=0):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        return _global_dict[key]
    except KeyError:
        return defValue

def set_glo_str(value):
    set_value('STR_ONE', value)

def set_glo_id(value):
    set_value('ID', value)

def set_glo_rpl(value):
    set_value('RPL', value)

def set_glo_tid(value):
    set_value('TID', value)

def glo_str():
    return get_value('str_one')

def glo_id():
    return get_value('id_one')

def glo_rpl():
    return get_value('RPL')

def glo_tid():
    return get_value('tid')