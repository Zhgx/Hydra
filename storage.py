#  coding: utf-8
import connect
import time
import sundry as s
import logdb
import consts
import re

# global _TID

host = '10.203.1.231'
port = 23
username = 'root'
password = 'Feixi@123'
timeout = 3


# [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]


class Storage:
    '''
    Create LUN and map to VersaPLX
    '''

    def __init__(self, logger):
        print('--------')

        self.logger = logger
        print('Start to configure LUN on NetApp Storage')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', 'Start to configure LUN on NetApp Storage')
        self._ID = consts.get_id()
        self._STR = consts.get_str()
        self._RPL = consts.get_rpl()
        self._TID = consts.get_tid()
        self.lun_name = f'{self._STR}_{self._ID}'
        if self._RPL == 'no':
            self.telnet_conn = connect.ConnTelnet(host, port, username, password, timeout, logger)
        # print('Connect to storage NetApp')

    def ex_telnet_cmd(self, unique_str, cmd, oprt_id):
        if self._RPL == 'no':
            self.logger.write_to_log('F', 'DATA', 'STR', unique_str, '', oprt_id)
            self.logger.write_to_log('T', 'OPRT', 'cmd', 'telnet', oprt_id, cmd)
            self.telnet_conn.execute_command(cmd)
        elif self._RPL == 'yes':
            db = logdb.LogDB()
            db_id, oprt_id = db.find_oprt_id_via_string(self._TID, unique_str)
            info_start = db.get_info_start(oprt_id)
            if info_start:
                print(info_start)
            # print(db.get_info_start(oprt_id))
            # print(f'  DB ID go to: {db_id}')
            # print(f'  get opration ID: {oprt_id}')
            # result_cmd = db.get_cmd_result(oprt_id)
            # print(db.get_info_finish(oprt_id))
            info_end = db.get_info_finish(oprt_id)
            if info_end:
                print(info_end)
            s.change_pointer(db_id)
            # print(f'  Change DB ID to: {db_id}')
            return True

    def lun_create(self):
        '''
        Create LUN with 10M bytes in size
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'jMPFwXy2'
        cmd = f'lun create -s 10m -t linux /vol/esxi/{self.lun_name}'
        info_msg = f'create lun, name: {self.lun_name}'
        print(f'  Start to {info_msg}')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id, f'  Start to {info_msg}')
        self.ex_telnet_cmd(unique_str, cmd, oprt_id)
        print(f'  Create LUN {self.lun_name} successful')
        self.logger.write_to_log('T', 'INFO', 'info', 'finish', oprt_id, f'  Create LUN {self.lun_name} successful')

    def lun_map(self):
        '''
        Map lun of specified lun_id to initiator group
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '1lvpO6N5'
        info_msg = f'map LUN, LUN name: {self.lun_name}, LUN ID: {self._ID}'
        cmd = f'lun map /vol/esxi/{self.lun_name} hydra {self._ID}'
        print(f'  Start to {info_msg}')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id, f'  Start to {info_msg}')
        self.ex_telnet_cmd(unique_str, cmd, oprt_id)
        print(f'  Finish with {info_msg}')
        self.logger.write_to_log('T', 'INFO', 'info', 'finish', oprt_id, f'  Finish with {info_msg}')

    def lun_create_verify(self):
        pass

    def lun_map_verify(self):
        pass

    def lun_unmap(self, lun_name):
        '''
        Unmap LUN and determine its succeed
        '''
        unmap = f'lun unmap /vol/esxi/{lun_name} hydra'
        unmap_result = self.telnet_conn.execute_command(unmap)
        if unmap_result:
            unmap_re = re.compile(r'unmapped from initiator group hydra')
            re_result = unmap_re.findall(unmap_result)
            if re_result:
                print(f'{lun_name} unmap succeed')
                return True

    def lun_destroy(self, lun_name):
        '''
        delete LUN and determine its succeed
        '''
        destroy_cmd = f'lun destroy /vol/esxi/{lun_name}'
        destroy_result = self.telnet_conn.execute_command(destroy_cmd)
        if destroy_result:
            destroy_re = re.compile(r'destroyed')
            re_result = destroy_re.findall(destroy_result)
            if re_result:
                print(f'{lun_name} destroy succeed')
                return True
            else:
                print(f'{lun_name} destroy failed')

    def _get_all_lun(self):
        lun_show_cmd = 'lun show'
        show_result = self.telnet_conn.execute_command(lun_show_cmd)
        if show_result:
            re_show = re.compile(f'/vol/esxi/({self._STR}_[0-9]{{1,3}})')
            list_of_all_lun = re_show.findall(show_result)
            return list_of_all_lun

    def lun_show(self):
        '''
        Get all luns through regular matching
        '''
        stor_list_todel = self._get_all_lun()
        if stor_list_todel:
            list_of_show_lun = s.getshow(
                self.logger, self._STR, self._ID, stor_list_todel)
            if list_of_show_lun:
                print('storage：')
                print(s.print_format(list_of_show_lun))
            return list_of_show_lun
        else:
            return False

    def start_stor_del(self, stor_show_result):
        for lun_name in stor_show_result:
            self.lun_unmap(lun_name)
            self.lun_destroy(lun_name)


if __name__ == '__main__':
    pass
    # test_stor = Storage('31', 'luntest')
    # test_stor.lun_create()
    # test_stor.lun_map()
    # test_stor.telnet_conn.close()
