# coding:utf-8
import vplx
import host_initiator
import storage
import consts
import os
import sundry as s

#-m:还需要优化日志收集,将每一部分分开,目录由调用函数传递,建立目录前判断,如果不存在则创建
def collect_debug_log():
    tid = consts.glo_tsc_id()
    local_debug_folder = f'/tmp/{tid}/'
    os.mkdir(local_debug_folder)

    s.prt('Start to collect debug log',0)

    s.prt('Start to collect debug log from Host',1)
    host_dbg = host_initiator.DebugLog()
    host_dbg.collect_debug_sys()
    host_dbg.get_all_log(local_debug_folder)

    s.prt('Start to collect debug log from VersaPLX',1)
    vplx_dbg = vplx.DebugLog()
    vplx_dbg.collect_debug_sys()
    vplx_dbg.collect_debug_drbd()
    vplx_dbg.collect_debug_crm()
    vplx_dbg.get_all_log(local_debug_folder)

    s.prt('Start to collect debug log from Storage',1)
    stor_dbg = storage.DebugLog()
    stor_dbg.get_storage_debug(local_debug_folder)

    s.prt(f'All debug log stor in folder localhost {local_debug_folder}')
    # except Exception as e:
    #     #-m:s.pwl应该加一个warning级别,便于标识出错信息
    #     # s.pwl('Log collection job is not completely successful')
    #     print(e)
    # # print(f'All debug log stor in folder {local_debug_folder}')
    # finally:
    #     print('finally')
    #     return local_debug_folder