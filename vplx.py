#  coding: utf-8

import connect
import sundry as s
import time
import sys
import os
import re


host = '10.203.1.199'
port = 22
user = 'root'
password = 'password'
timeout = 3

Netapp_ip = '10.203.1.231'
target_iqn = "iqn.2020-06.com.example:test-max-lun"
initiator_iqn = "iqn.1993-08.org.debian:01:885240c2d86c"
target_name = 't_test'


class VplxDrbd(object):
    '''
    Integrate LUN in DRBD resources
    '''

    def __init__(self, unique_id, unique_name):
        self.ssh = connect.ConnSSH(host, port, user, password, timeout)
        self.id = unique_id
        self.res_name = f'res_{unique_name}_{unique_id}'
        self.blk_dev_name = None
        self.drbd_device_name = f'drbd{unique_id}'

    # def _find_blk_dev(self, id, ls_result):
    #     '''
    #     Use re to get the blk_dev_name through id
    #     '''
    #     re_vplx_id_path = re.compile(
    #         r'''\:(\d*)\].*NETAPP[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})''')
    #     stor_result = re_vplx_id_path.findall(ls_result)
    #     if stor_result:
    #         dict_stor = dict(stor_result)
    #         if str(id) in dict_stor.keys():
    #             blk_dev_name = dict_stor[str(id)]
    #             return blk_dev_name

    def discover_new_lun(self):
        '''
        Scan and find the disk from NetApp
        '''
        if self.ssh.excute_command('/usr/bin/rescan-scsi-bus.sh'):
            lsscsi_result = self.ssh.excute_command('lsscsi')
        else:
            s.pe(f'Scan new LUN failed on NetApp')
        re_find_id_dev = r'\:(\d*)\].*NETAPP[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
        self.blk_dev_name = s.GetDiskPath(
            self.id, re_find_id_dev, lsscsi_result, 'NetApp').explore_disk()
        print(f'Find device {self.blk_dev_name} for LUN id {self.id}')

    def start_discover(self):
        if not self.vplx_session():
            self.vplx_login()
        self.discover_new_lun()

    def prepare_config_file(self):
        '''
        Prepare DRDB resource config file
        '''
        context = [rf'resource {self.res_name} {{',
                   rf'\ \ \ \ on maxluntarget {{',
                   rf'\ \ \ \ \ \ \ \ device /dev/{self.drbd_device_name}\;',
                   rf'\ \ \ \ \ \ \ \ disk {self.blk_dev_name}\;',
                   rf'\ \ \ \ \ \ \ \ address 10.203.1.199:7789\;',
                   rf'\ \ \ \ \ \ \ \ node-id 0\;',
                   rf'\ \ \ \ \ \ \ \ meta-disk internal\;',
                   r'\ \ \ \}',
                   r'}']

        # for echo_command in context:
        #     echo_result = self.ssh.excute_command(
        #         f'echo {echo_command} >> /etc/drbd.d/{self.res_name}.res')
        #     if echo_result is True:
        #         continue
        #     else:
        #         s.pe('fail to prepare drbd config file..')

        for i in range(len(context)):
            if i == 0:
                echo_result = self.ssh.excute_command(
                    f'echo {context[i]} > /etc/drbd.d/{self.res_name}.res')
            else:
                echo_result = self.ssh.excute_command(
                    f'echo {context[i]} >> /etc/drbd.d/{self.res_name}.res')
            if echo_result is True:
                continue
            else:
                s.pe('fail to prepare drbd config file..')
        print(f'Create DRBD config file "{self.res_name}.res" done')

    def _drbd_init(self):
        '''
        Initiakize DRBD resource
        '''
        init_cmd = f'drbdadm create-md {self.res_name}'
        drbd_init = self.ssh.excute_command(init_cmd)

        if drbd_init:
            drbd_init = drbd_init.decode('utf-8')
            re_drbd = re.compile(
                'New drbd meta data block successfully created')
            re_init = re_drbd.findall(drbd_init)
            if re_init:
                print(f'{self.res_name} initialize success')
                return True
            else:
                s.pe(f'drbd resource {self.res_name} initialize failed')

        else:
            s.pe(f'drbd resource {self.res_name} initialize failed')

    def _drbd_up(self):
        '''
        Start DRBD resource
        '''
        up_cmd = f'drbdadm up {self.res_name}'
        drbd_up = self.ssh.excute_command(up_cmd)
        if drbd_up is True:
            print(f'{self.res_name} up success')
            return True
        else:
            s.pe(f'drbd resource {self.res_name} up failed')

    def _drbd_primary(self):
        '''
        Complete initial synchronization of resources
        '''
        primary_cmd = f'drbdadm primary --force {self.res_name}'
        drbd_primary = self.ssh.excute_command(primary_cmd)
        if drbd_primary is True:
            print(f'{self.res_name} primary success')
            return True
        else:
            s.pe(f'drbd resource {self.res_name} primary failed')

    def drbd_cfg(self):
        if self._drbd_init():
            if self._drbd_up():
                if self._drbd_primary():
                    return True

    def drbd_status_verify(self):
        '''
        Check DRBD resource status and confirm the status is UpToDate
        '''
        verify_cmd = f'drbdadm status {self.res_name}'
        result = self.ssh.excute_command(verify_cmd)
        if result:
            result = result.decode('utf-8')
            re_display = re.compile(r'''disk:(\w*)''')
            re_result = re_display.findall(result)
            if re_result:
                status = re_result[0]
                if status == 'UpToDate':
                    print(f'{self.res_name} DRBD check successful')
                    return True
                else:
                    s.pe(f'{self.res_name} DRBD verification failed')
            else:
                s.pe(f'{self.res_name} DRBD does not exist')

    def vplx_login(self):
        login_cmd = f'iscsiadm -m discovery -t st -p {Netapp_ip} -l'
        login_result = self.ssh.excute_command(login_cmd)
        if s.iscsi_login(Netapp_ip, login_result):
            return True

    def vplx_logout(self):
        logout_cmd = ' iscsiadm -m node -T iqn.1992-08.com.netapp:sn.84305553 --logout'
        logout_result = self.ssh.excute_command(logout_cmd)
        if s.iscsi_logout(Netapp_ip, logout_result):
            return True

    def vplx_session(self):
        session_cmd = 'iscsiadm -m session'
        session_result = self.ssh.excute_command(session_cmd)
        if s.find_session(Netapp_ip, session_result):
            return True


class VplxCrm(VplxDrbd):
    def __init__(self, unique_id, unique_name):
        VplxDrbd.__init__(self, unique_id, unique_name)
        self.lu_name = self.res_name
        self.colocation_name = f'co_{self.lu_name}'
        self.target_iqn = target_iqn
        self.initiator_iqn = initiator_iqn
        self.target_name = target_name
        self.order_name = f'or_{self.lu_name}'

    def _crm_create(self):
        '''
        Create iSCSILogicalUnit resource
        '''
        crm_create_cmd = f'crm conf primitive {self.lu_name} \
            iSCSILogicalUnit params target_iqn="{self.target_iqn}" \
            implementation=lio-t lun={self.id} path="/dev/{self.drbd_device_name}"\
            allowed_initiators="{self.initiator_iqn}" op start timeout=40 interval=0 op stop timeout=40 interval=0 op monitor timeout=40 interval=50 meta target-role=Stopped'

        if self.ssh.excute_command(crm_create_cmd) is True:
            print('iscisi lun_create success')
            return True
        else:
            s.pe('iscisi lun_create failed')

    def _setting_col(self):
        '''
        Setting up iSCSILogicalUnit resources of colocation
        '''
        col_cmd = f'crm conf colocation {self.colocation_name} inf: {self.lu_name} {self.target_name}'
        set_col = self.ssh.excute_command(col_cmd)
        if set_col is True:
            print('setting colocation successful')
            return True
        else:
            s.pe('setting colocation failed')

    def _setting_order(self):
        '''
        Setting up iSCSILogicalUnit resources of order
        '''
        order_cmd = f'crm conf order {self.order_name} {self.target_name} {self.lu_name}'
        set_order = self.ssh.excute_command(order_cmd)
        if set_order is True:
            print('setting order succeed')
            return True
        else:
            s.pe('setting order failed')

    def _crm_setting(self):
        if self._setting_col():
            if self._setting_order():
                return True

    def _crm_start(self):
        '''
        start the iSCSILogicalUnit resource
        '''
        crm_start_cmd = f'crm res start {self.lu_name}'
        crm_start = self.ssh.excute_command(crm_start_cmd)
        if crm_start is True:
            print('iscsi lun start successful')
            return True
        else:
            s.pe('iscsi lun start failed')

    def crm_cfg(self):
        if self._crm_create():
            if self._crm_setting():
                if self._crm_start():
                    return True

    # def _crm_verify(self):
    #     verify_result = self.ssh.excute_command('crm res show')
    #     re_show = re.compile(f'({self.res_name})\s.*:\s(\w*)')
    #     if verify_result:
    #         re_show_result = re_show.findall(verify_result.decode('utf-8'))
    #         dict_show_result = dict(re_show_result)
    #         if self.res_name in dict_show_result.keys():
    #             crm_status = dict_show_result[self.res_name]
    #             if crm_status == 'Started':
    #                 return True
    #             else:
    #                 return False
    #     else:
    #         s.pe('crm show failed')

    # def crm_status(self):
    #     n = 0
    #     while n < 10:
    #         n += 1
    #         if self._crm_verify():
    #             print(f'{self.res_name} is Started')
    #             return True
    #         else:
    #             print(f'{self.res_name} is Started, Wait a moment...')
    #             time.sleep(1.5)
    #     else:
    #         return False

    def _crm_verify(self, res_name):
        verify_result = self.ssh.excute_command('crm res show')
        if verify_result:
            re_show = re.compile(f'({res_name})\s.*:\s(\w*)')
            re_show_result = re_show.findall(verify_result.decode('utf-8'))
            dict_show_result = dict(re_show_result)
            if res_name in dict_show_result.keys():
                crm_status = dict_show_result[res_name]
                if crm_status == 'Stopped':
                    return True
                else:
                    return False
        else:
            s.pe('crm show failed')

    def crm_status_stop(self, res_name):
        n = 0
        while n < 10:
            n += 1
            if self._crm_verify(res_name):
                print(f'{res_name} is Stopped')
                return True
            else:
                print(f'{res_name} is Stopped, Wait a moment...')
                time.sleep(1.5)
        else:
            return False

    def _crm_stop(self, res_name):
        crm_stop_cmd = (f'crm res stop {res_name}')
        print(crm_stop_cmd)
        crm_stop = self.ssh.excute_command(crm_stop_cmd)
        if crm_stop is True:
            if self.crm_status_stop(res_name):
                return True
        else:
            s.pe('crm stop failed')

    def _crm_del(self, res_name):
        crm_del_cmd = f'crm cof delete {res_name}'
        del_result = self.ssh.excute_command(crm_del_cmd)
        if del_result:
            re_delstr = re.compile('deleted')
            re_result = re_delstr.findall(str(del_result, encoding='utf-8'))
            if len(re_result) == 2:
                return True
            else:
                s.pe('crm cof delete failed')

    def _drbd_down(self, res_name):
        drbd_down_cmd = f'drbdadm down {res_name}'
        if self.ssh.excute_command(drbd_down_cmd) is True:
            return True
        else:
            s.pe('drbd down failed')

    def _drbd_del(self, res_name):
        drbd_del_cmd = f'rm /etc/drbd.d/{res_name}.res'
        if self.ssh.excute_command(drbd_del_cmd) is True:
            return True
        else:
            s.pe('drbd remove config file fail')

    def start_del(self, res_name):
        if self._crm_stop(res_name):
            if self._crm_del(res_name):
                if self._drbd_down(res_name):
                    if self._drbd_del(res_name):
                        return True

    def range_uid(self, unique_str, unique_id, res_show_result):
        list_res = []
        for i in range(unique_id[0], unique_id[1]+1):
            res_name = f'res_{unique_str}_{i}'
            re_res_show = re.compile(res_name)
            re_res_name = re_res_show.findall(
                res_show_result.decode('utf-8'))
            if re_res_name:
                list_res.append(re_res_name[0])
                print(f'{res_name} already found')
            else:
                print(f'{res_name} not found')
        return list_res

    def one_uid(self, unique_str, unique_id, res_show_result):
        res_name = f'res_{unique_str}_{unique_id[0]}'
        re_res_show = re.compile(res_name)
        re_res_name = re_res_show.findall(
            res_show_result.decode('utf-8'))
        if re_res_name:
            print(f'{re_res_name} already found')
            return re_res_name
        else:
            s.pe(f'{res_name} not found')

    def vplx_show(self, unique_str, unique_id):
        res_show_result = self.ssh.excute_command('crm res show')
        if res_show_result:
            re_show = re.compile(f'res_{unique_str}_\w*')
            re_result = re_show.findall(res_show_result.decode('utf-8'))
            if unique_id:
                if len(unique_id) == 2:
                    return self.range_uid(unique_str, unique_id, res_show_result)
                elif len(unique_id) == 1:
                    self.one_uid(unique_str, unique_id, res_show_result)
                else:
                    s.pe('please enter a valid value')
            else:
                print(f'{re_result} is found')
                return re_result

    def del_comfirm(self, del_result):
        comfirm = input('Do you want to delete these lun (yes/no):')
        if comfirm == 'yes':
            for res_name in del_result:
                self.start_del(res_name)
        else:
            s.pe('Cancel succeed')

    def vlpx_del(self, unique_str, unique_id):
        del_result = self.vplx_show(unique_str, unique_id)
        self.del_comfirm(del_result)

    def retry_login(self):
        if not self.vplx_session():
            self.vplx_login()
        elif self.vplx_session():
            if self.vplx_logout():
                self.vplx_login()


if __name__ == '__main__':
    # for i  in range(140,174):
    #     test_crm = VplxCrm(i, 'luntest')
    #     test_crm.prepare_config_file()
    #     time.sleep(0.5)
    #     if test_crm.ssh.excute_command(f'drbdadm down res_luntest_{i}') is True:
    #         test_crm.ssh.excute_command(f'rm /etc/drbd.d/res_luntest_{i}.res')
    #         print(i)
    #     test_crm.ssh.close()
    pass
