#  coding: utf-8
import connect
import time

host = '10.203.1.231'
port = 23
username = 'root'
password = 'Feixi@123'
timeout = 3


class Storage:
    '''
    Create LUN and map to VersaPLX
    '''

    def __init__(self, unique_id, unique_name):
        self.telnet_conn = connect.ConnTelnet(
            host, port, username, password, timeout)
        # print('Connect to storage NetApp')
        self.lun_name = f'{unique_name}_{unique_id}'
        self.lun_id = unique_id

    def lun_create(self):
        '''
        Create LUN with 10M bytes in size
        '''
        lc_cmd = f'lun create -s 10m -t linux /vol/esxi/{self.lun_name}'
        self.telnet_conn.excute_command(lc_cmd)
        print('Create LUN successful on NetApp Storage')

    def lun_map(self):
        '''
        Map lun of specified lun_id to initiator group
        '''
        lm_cmd = f'lun map /vol/esxi/{self.lun_name} hydra {self.lun_id}'
        self.telnet_conn.excute_command(lm_cmd)
        print('LUN map successful on NetApp Storage')

    def lun_create_verify(self):
        pass

    def lun_map_verify(self):
        pass


class StorageDel(object):
    def __init__(self):
        self.telnet_conn = connect.ConnTelnet(
            host, port, username, password, timeout)

    def lun_unmap(self, lun_name):
        unmap = f'lun unmap {lun_name} hydra'
        self.telnet_conn.excute_command(unmap)

    def lun_destory(self, lun_name):
        destory_cmd = f'lun destroy {lun_name}'
        self.telnet_conn.excute_command(destory_cmd)


if __name__ == '__main__':
    test_stor = Storage('8', 'test')
    test_stor.lun_create()
    test_stor.lun_map()
    test_stor.telnet_conn.close()
    # pass
