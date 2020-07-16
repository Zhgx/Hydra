# coding:utf-8

def _init():  # 初始化
    global _global_dict
    _global_dict = {'LOG_ID': 0}


def set_value(key, value):
    """ 定义一个全局变量 """
    _global_dict[key] = value


def get_value(key, defValue=None):
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
