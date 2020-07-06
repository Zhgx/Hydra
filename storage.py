#  coding: utf-8
import connect
import time

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


if __name__ == '__main__':
    test_stor = Storage('18', 'luntest')
    test_stor.lun_create()
    test_stor.lun_map()
    # test_stor.telnet_conn.close()
    pass
