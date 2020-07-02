#  coding: utf-8
import connect
import time
import sundry as s
import re
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

    def lun_unmap(self, lun_name):
        '''
        Unmap LUN and determine its succeed
        '''
        unmap = f'lun unmap /vol/esxi/{lun_name} hydra'
        unmap_result = self.telnet_conn.excute_command(unmap)
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
        destroy_result = self.telnet_conn.excute_command(destroy_cmd)
        if destroy_result:
            destroy_re = re.compile(r'destroyed')
            re_result = destroy_re.findall(destroy_result)
            if re_result:
                print(f'{lun_name} destory succeed')
                return True
            else:
                print(f'{lun_name} destory failed')

    def all_lun(self, unique_str):
        '''
        Get all luns through regular matching
        '''
        show_cmd = 'lun show'
        show_result = self.telnet_conn.excute_command(show_cmd)
        if show_result:
            show_re = re.compile(f'{unique_str}_[0-9]*')
            re_result = show_re.findall(show_result)
            if re_result:
                return re_result
            else:
                s.pe('lun is not found')

    def have_uid(self, unique_str, unique_id):
        '''
        Distinguish whether the lun id is a range value or a single value and then perform regular matching
        '''
        show_result = self.all_lun(unique_str)
        if len(unique_id) == 2:
            lun_ids = s.range_uid(unique_str, unique_id, show_result)
            return lun_ids

        if len(unique_id) == 1:
            lun_ids = s.one_uid(unique_str, unique_id, show_result)
            return lun_ids
        else:
            s.pe('please enter a valid value')

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
    test_stor = Storage('1', 'luntest')
    # test_stor.telnet_conn.excute_command('lun show')
    test_stor.stor_del('asdfaf', [201])
    # test_stor.lun_create()
    # test_stor.lun_map()
    # test_stor.telnet_conn.close()
    # pass
