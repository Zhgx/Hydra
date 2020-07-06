#  coding: utf-8
import connect
import time
import re
import sundry as s

global ID
global STRING

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

    def __init__(self,logger):
        self.logger = logger
        print('Start to configure LUN on NetApp Storage')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', 'Start to configure LUN on NetApp Storage')
        self.telnet_conn = connect.ConnTelnet(host, port, username, password, timeout,logger)
        # print('Connect to storage NetApp')
        self.lun_name = f'{STRING}_{ID}'


    def lun_create(self):
        '''
        Create LUN with 10M bytes in size
        '''
        # self.logger.write_to_log('INFO','info','',f'start to create lun {self.lun_name}')
        info_msg = f'create lun, name: {self.lun_name}'
        # [time],[transaction_id],[s],[INFO],[info],[start],[d2],[info_msg]
        lc_cmd = f'lun create -s 10m -t linux /vol/esxi/{self.lun_name}'
        # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
        print(f'  Start to {info_msg}')
        self.logger.write_to_log('T','INFO','info','start','',f'  Start to {info_msg}')
        self.telnet_conn.execute_command(lc_cmd)
        print(f'  Create LUN {self.lun_name} successful')
        self.logger.write_to_log('T','INFO','info','finish','',f'  Create LUN {self.lun_name} successful')
        # self.logger.write_to_log('INFO','info','',('Create LUN successful on NetApp Storage'))
        # [time],[transaction_id],[s],[INFO],[info],[finish],[d2],[f'create lun, name: {self.lun_name}']

    def lun_map(self):
        '''
        Map lun of specified lun_id to initiator group
        '''
        info_msg = f'map LUN, LUN name: {self.lun_name}, LUN ID: {ID}'
        # self.logger.write_to_log('INFO','info','',f'start to map lun {self.lun_name}')
        lm_cmd = f'lun map /vol/esxi/{self.lun_name} hydra {ID}'
        print(f'  Start to {info_msg}')
        self.logger.write_to_log('T','INFO','info','start','',f'  Start to {info_msg}')
        self.telnet_conn.execute_command(lm_cmd)
        print(f'  Finish with {info_msg}')
        self.logger.write_to_log('T','INFO','info','finish','',f'  Finish with {info_msg}')
        # self.logger.write_to_log('INFO', 'info', '', ('LUN map successful on NetApp Storage'))

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
            else:
                print(f'{lun_name} unmap failed')

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

    def all_lun(self, unique_str):
        '''
        Get all luns through regular matching
        '''
        show_cmd = 'lun show'
        show_result = self.telnet_conn.execute_command(show_cmd)
        if show_result:
            show_re = re.compile(f'{unique_str}_[0-9]*')
            re_result = show_re.findall(show_result)
            if re_result:
                return re_result
            else:
                s.pwe(self.logger,'lun is not found')

    def have_uid(self, unique_str, unique_id):
        '''
        Distinguish whether the lun id is a range value or a single value and then perform regular matching
        '''
        show_result = self.all_lun(unique_str)
        if len(unique_id) == 2:
            lun_ids = s.range_uid(self.logger,unique_str, unique_id, show_result)
            return lun_ids

        if len(unique_id) == 1:
            lun_ids = s.one_uid(self.logger,unique_str, unique_id, show_result)
            return lun_ids
        else:
            s.pwe(self.logger,'please enter a valid value')

    def lun_getname(self, unique_str, unique_id):
        if unique_id:
            return self.have_uid(unique_str, unique_id)
        else:
            return self.all_lun(unique_str)

    def stor_del(self, unique_str, unique_id=''):
        '''
        Call the function method to delete
        '''
        del_name = self.lun_getname(unique_str, unique_id)
        for lun_name in del_name:
            self.lun_unmap(lun_name)
            self.lun_destroy(lun_name)
            time.sleep(0.25)


if __name__ == '__main__':
    pass
    # test_stor = Storage('18', 'luntest')
    # test_stor.lun_create()
    # test_stor.lun_map()
    # test_stor.telnet_conn.close()
    # pass
