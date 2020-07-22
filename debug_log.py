# coding:utf-8
import vplx
import host_initiator

#-m:还需要优化日志收集,将每一部分分开,目录由调用函数传递,建立目录前判断,如果不存在则创建
def collect_debug_log(self):
    # consts.set_glo_tsc_id(s.ran_str(6))
    tid = consts.glo_tsc_id()
    local_debug_folder = f'/tmp/{tid}/'
    os.mkdir(local_debug_folder)
    try:
        vplx_dbg = vplx.DebugLog()
        #-m:s.prt
        print('Start to collect debug log from VersaPLX')
        vplx_dbg.collect_debug_sys()
        vplx_dbg.collect_debug_drbd()
        vplx_dbg.collect_debug_crm()
        vplx_dbg.get_all_log(local_debug_folder)

        host_dbg = host_initiator.DebugLog()
        print('Start to collect debug log from Host')
        host_dbg.collect_debug_sys()
        host_dbg.get_all_log(local_debug_folder)

        stor_dbg = storage.DebugLog()
        print('Start to collect debug log from Storage')
        stor_dbg.get_storage_debug(local_debug_folder)
    except:
        #-m:s.pwl应该加一个warning级别,便于标识出错信息
        s.pwl('Log collection job is not completely successful')
    # print(f'All debug log stor in folder {local_debug_folder}')
    finally:
        return local_debug_folder