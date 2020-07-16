#  coding: utf-8
import connect
import sundry as s
import time
import sys
import os
import re
import logdb
import consts

# global SSH
SSH = None


# global _ID
# global _STR
# global _RPL
# global _TID

host = '10.203.1.199'
port = 22
user = 'root'
password = 'password'
timeout = 3

Netapp_ip = '10.203.1.231'
target_iqn = "iqn.2020-06.com.example:test-max-lun"
initiator_iqn = "iqn.1993-08.org.debian:01:885240c2d86c"
target_name = 't_test'


def init_ssh():
    global SSH
    if not SSH:
        SSH = connect.ConnSSH(host, port, user, password, timeout)
    else:
        pass

# --------------------------------------------------
# --------------------------------------------------


def _find_new_disk():
    result_lsscsi = s.get_lsscsi(SSH, 'D37nG6Yi', s.get_oprt_id())
    re_string = r'\:(\d*)\].*NETAPP[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
    all_disk = s.get_all_scsi_disk(re_string, result_lsscsi)
    disk_dev = s.get_the_disk_with_lun_id(all_disk)
    if disk_dev:
        return disk_dev


def get_disk_dev():
    s.scsi_rescan(SSH, 'n')
    disk_dev = _find_new_disk()
    if disk_dev:
        return disk_dev
    else:
        print('----------------get_disk_dev')
        s.scsi_rescan(SSH, 'a')
        disk_dev = _find_new_disk()
        if disk_dev:
            return disk_dev
        else:
            s.pwe('xxx:vplx,get_disk_dev fail')


class VplxDrbd(object):
    '''
    Integrate LUN in DRBD resources
    '''

    def __init__(self):
        self.logger = consts.glo_log()
        self.STR = consts.glo_str()
        self.ID = consts.glo_id()
        self.LIST_ID = consts.glo_list_id()
        self.rpl = consts.glo_rpl()
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 'Start to configure DRDB resource and crm resource on VersaPLX')

        self.res_name = f'res_{self.STR}_{self.ID}'
        global DRBD_DEV_NAME
        DRBD_DEV_NAME = f'drbd{self.ID}'
        global RPL
        RPL = consts.glo_rpl()
        self._prepare()

    def _create_iscsi_session(self):
        self.logger.write_to_log(
            f'T', 'INFO', 'info', 'start', '', f'  Discover iSCSI session for {Netapp_ip}')
        if not s.find_session(Netapp_ip, SSH, 'V9jGOP1i', s.get_oprt_id()):
            self.logger.write_to_log(
                f'T', 'INFO', 'info', 'start', '', f'  Login to {Netapp_ip}')
            if s.iscsi_login(Netapp_ip, SSH, 'rgjfYl3K', s.get_oprt_id()):
                pass
            else:
                s.pwe(f'can not login to {Netapp_ip}')

    def _prepare(self):
        if self.rpl == 'no':
            init_ssh()
            self._create_iscsi_session()

    # def get_disk_device(self):
    #     self.blk_dev_name = get_disk_dev()

    def prepare_config_file(self):
        '''
        Prepare DRDB resource config file
        '''
        if self.rpl == 'yes':
            return
        blk_dev_name = get_disk_dev()
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'      Start prepare config fiel for resource {self.res_name}')
        context = [rf'resource {self.res_name} {{',
                   rf'\ \ \ \ on maxluntarget {{',
                   rf'\ \ \ \ \ \ \ \ device /dev/{DRBD_DEV_NAME}\;',
                   rf'\ \ \ \ \ \ \ \ disk {blk_dev_name}\;',
                   rf'\ \ \ \ \ \ \ \ address 10.203.1.199:7789\;',
                   rf'\ \ \ \ \ \ \ \ node-id 0\;',
                   rf'\ \ \ \ \ \ \ \ meta-disk internal\;',
                   r'\ \ \ \}',
                   r'}']

        self.logger.write_to_log(
            'F', 'DATA', 'value', 'list', 'content of drbd config file', context)
        unique_str = 'UsKyYtYm1'
        config_file_name = f'{self.res_name}.res'
        for i in range(len(context)):
            if i == 0:
                oprt_id = s.get_oprt_id()
                cmd = f'echo {context[i]} > /etc/drbd.d/{config_file_name}'
                echo_result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
            else:
                oprt_id = s.get_oprt_id()
                cmd = f'echo {context[i]} >> /etc/drbd.d/{config_file_name}'
                echo_result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
            # result of ssh command like (1,'done'),1 for status, 'done' for data.
            if echo_result['sts']:
                continue
            else:

                s.pwe('fail to prepare drbd config file..')

        print(f'  config file "{self.res_name}.res" created')
        self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                                 f'      Create DRBD config file "{self.res_name}.res" done')

    def _drbd_init(self):
        '''
        Initialize DRBD resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'usnkegs'
        cmd = f'drbdadm create-md {self.res_name}'

        info_msg = f'      Initialize drbd for {self.res_name}'
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', oprt_id, info_msg)

        init_result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        re_drbd = 'New drbd meta data block successfully created'
        re_result = s.re_findall(re_drbd, init_result['rst'].decode())
        if re_result:
            print(f'  Resource "{self.res_name}" initialize successful')
            return True
        else:
            s.pwe(f'drbd resource {self.res_name} initialize failed')

    def _drbd_up(self):
        '''
        Start DRBD resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'elsflsnek'
        cmd = f'drbdadm up {self.res_name}'
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result['sts']:
            print(f'  Resource "{self.res_name}" bring up successful')
            return True

    def _drbd_primary(self):
        '''
        Complete initial synchronization of resources
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '7C4LU6Xr'
        cmd = f'drbdadm primary --force {self.res_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'      Start to initial synchronization for {self.res_name}')
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result['sts']:
            print(f'    {self.res_name} synchronize successfully')
            self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                                     f'    {self.res_name} synchronize successfully')
            return True
        else:
            s.pwe(f'drbd resource {self.res_name} primary failed')
        # drbd_primary = SSH.execute_command(primary_cmd)
        # if drbd_primary['sts']:
        #     print(f'{self.res_name} primary success')
        #     self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', f'      {self.res_name} synchronize successfully')
        #     # self.logger.write_to_log('INFO','info','',(f'{self.res_name} primary success'))
        #     return True
        # else:
        #     s.pwe(self.logger,f'drbd resource {self.res_name} primary failed')

    def drbd_cfg(self):
        print('Start to config DRBD resource...')

        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'    Start to configure DRBD resource {self.res_name}')

        if self._drbd_init():
            if self._drbd_up():
                if self._drbd_primary():
                    return True

    def drbd_status_verify(self):
        '''
        Check DRBD resource status and confirm the status is UpToDate
        '''
        cmd = f'drbdadm status {self.res_name}'
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', '', '      Start to check DRBD resource status')
        result = s.get_ssh_cmd(SSH, 'By91GFxC', cmd, s.get_oprt_id())
        if result['sts']:
            result = result['rst'].decode()
            re_display = r'''disk:(\w*)'''
            re_result = s.re_findall(re_display, result)
            if re_result:
                status = re_result[0]
                if status == 'UpToDate':
                    print(f'    {self.res_name} DRBD check successfully')
                    self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                                             f'    {self.res_name} DRBD check successfully')
                    # self.logger.write_to_log('INFO','info','',(f'{self.res_name} DRBD check successful'))
                    return True
                else:
                    s.pwe(f'{self.res_name} DRBD verification failed')
            else:
                s.pwe(f'{self.res_name} DRBD does not exist')

    def _drbd_down(self, res_name):
        '''
        Stop the DRBD resource
        '''
        unique_str = 'UqmYgtM3'
        drbd_down_cmd = f'drbdadm down {res_name}'
        oprt_id = s.get_oprt_id()
        down_result = s.get_ssh_cmd(SSH, unique_str, drbd_down_cmd, oprt_id)
        if down_result['sts']:
            return True
        else:
            s.pwe('drbd down failed')

    def _drbd_del_config(self, res_name):
        '''
        remove the DRBD config file
        '''
        unique_str = 'UqkYgtM3'
        drbd_del_cmd = f'rm /etc/drbd.d/{res_name}.res'
        oprt_id = s.get_oprt_id()
        del_result = s.get_ssh_cmd(SSH, unique_str, drbd_del_cmd, oprt_id)
        if del_result['sts']:
            return True
        else:
            s.pwe('drbd remove config file fail')

    def _get_all_drbd(self):
        unique_str = 'UikYgtM1'
        drbd_show_cmd = 'drbdadm status'
        oprt_id = s.get_oprt_id()
        drbd_show_result = s.get_ssh_cmd(
            SSH, unique_str, drbd_show_cmd, oprt_id)
        if drbd_show_result['sts']:
            re_drbd = f'res_{self.STR}_[0-9]{{1,3}}'
            list_of_all_drbd = s.re_findall(
                re_drbd, drbd_show_result['rst'].decode('utf-8'))
            return list_of_all_drbd

    def drbd_show(self):
        '''
        Get the DRBD resource name through regular matching and determine whether these  exist
        '''
        drbd_show_result = self._get_all_drbd()
        if drbd_show_result:
            list_of_show_drbd = s.getshow(
                self.logger, self.STR, self.LIST_ID, drbd_show_result)
            if list_of_show_drbd:
                print('DRBD：')
                print(s.print_format(list_of_show_drbd))
            return list_of_show_drbd
        else:
            return False

    def drbd_del(self, res_name):
        if self._drbd_down(res_name):
            if self._drbd_del_config(res_name):
                return True

    def start_drbd_del(self, drbd_show_result):
        if drbd_show_result:
            for res_name in drbd_show_result:
                self.drbd_del(res_name)


class VplxCrm(object):
    def __init__(self):
        self.logger = consts.glo_log()
        self.ID = consts.glo_id()
        self.LIST_ID = consts.glo_list_id()
        self.STR = consts.glo_str()
        self.rpl = consts.glo_rpl()
        # same as drbd resource name
        self.lu_name = f'res_{self.STR}_{self.ID}'
        self.colocation_name = f'co_{self.lu_name}'
        self.order_name = f'or_{self.lu_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start',
                                 '', f'  Start to configure crm resource {self.lu_name}')
        # self.logger.write_to_log('INFO','info','',f'start to config crm resource {self.lu_name}') #
        if self.rpl == 'no':
            init_ssh()

    def _crm_create(self):
        '''
        Create iSCSILogicalUnit resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'LXYV7dft'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                                 f'    Start to create iSCSILogicalUnit resource {self.lu_name}')
        cmd = f'crm conf primitive {self.lu_name} \
            iSCSILogicalUnit params target_iqn="{target_iqn}" \
            implementation=lio-t lun={consts.glo_id()} path="/dev/{DRBD_DEV_NAME}"\
            allowed_initiators="{initiator_iqn}" op start timeout=40 interval=0 op stop timeout=40 interval=0 op monitor timeout=40 interval=50 meta target-role=Stopped'
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result['sts']:
            print('    Create iSCSILogicalUnit successfully')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', '    Create iSCSILogicalUnit successfully')
            return True
        else:
            s.pwe('iscisi lun_create failed')

    def _setting_col(self):
        '''
        Setting up iSCSILogicalUnit resources of colocation
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'E03YgRBd'
        cmd = f'crm conf colocation {self.colocation_name} inf: {self.lu_name} {target_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                                 '      start to setting up iSCSILogicalUnit resources of colocation')
        result_crm = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_crm['sts']:
            print('      Setting colocation successful')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', '      Setting colocation successful')
            return True
        else:
            s.pwe('setting colocation failed')

    def _setting_order(self):
        '''
        Setting up iSCSILogicalUnit resources of order
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '0GHI63jX'
        cmd = f'crm conf order {self.order_name} {target_name} {self.lu_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                                 '      Start to setting up iSCSILogicalUnit resources of order')
        result_crm = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_crm['sts']:
            print('      Setting order succeed')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', '      Setting order succeed')
            return True
        else:
            s.pwe('setting order failed')

    def _crm_setting(self):
        if self._setting_col():
            if self._setting_order():
                return True

    def _crm_start(self):
        '''
        start the iSCSILogicalUnit resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'YnTDsuVX'
        cmd = f'crm res start {self.lu_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                                 f'      Start the iSCSILogicalUnit resource {self.lu_name}')
        result_cmd = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_cmd['sts']:
            print('      ISCSI LUN start successful')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', '      ISCSI LUN start successful')
            return True
        else:
            s.pwe('iscsi lun start failed')

    def crm_cfg(self):
        print('  start cmd_cfg')
        if self._crm_create():
            if self._crm_setting():
                if self._crm_start():
                    return True

    def _crm_verify(self, res_name):
        '''
        Check the crm resource status
        '''
        unique_str = 'UqmUytK3'
        crm_show_cmd = f'crm res show {res_name}'
        oprt_id = s.get_oprt_id()
        verify_result = s.get_ssh_cmd(SSH, unique_str, crm_show_cmd, oprt_id)
        if verify_result['sts'] == 1:
            return {'status': 'Started'}
        if verify_result['sts'] == 0:
            return {'status': 'Stopped'}
        else:
            s.pwe('crm show failed')

    def crm_status(self, res_name, status):
        '''
        Determine crm resource status is started/stopped
        '''
        n = 0
        while n < 10:
            n += 1
            crm_verify = self._crm_verify(res_name)
            if crm_verify['status'] == status:
                print(f'{res_name} is {status}')
                return True
            else:
                print(
                    f'{res_name} is {crm_verify["status"]}, Wait a moment...')
                time.sleep(1.5)
        else:
            return False

    def _crm_stop(self, res_name):
        '''
        stop the iSCSILogicalUnit resource
        '''
        unique_str = 'UqmYgtM1'
        crm_stop_cmd = (f'crm res stop {res_name}')
        oprt_id = s.get_oprt_id()
        crm_stop = s.get_ssh_cmd(SSH, unique_str, crm_stop_cmd, oprt_id)
        if crm_stop['sts']:
            if self.crm_status(res_name, 'Stopped'):
                return True
            else:
                s.pwe('crm stop failed,exit the program...')
        else:
            s.pwe('crm stop failed')

    def _crm_del(self, res_name):
        '''
        Delete the iSCSILogicalUnit resource
        '''
        unique_str = 'EsTyUqIb5'
        crm_del_cmd = f'crm cof delete {res_name}'
        oprt_id = s.get_oprt_id()
        del_result = s.get_ssh_cmd(SSH, unique_str, crm_del_cmd, oprt_id)
        if del_result['sts']:
            re_delstr = 'deleted'
            re_result = s.re_findall(
                re_delstr, del_result['rst'].decode('utf-8'))
            if len(re_result) == 2:
                return True
            else:
                s.pwe('crm cof delete failed')

    def crm_del(self, res_name):
        if self._crm_stop(res_name):
            if self._crm_del(res_name):
                return True

    def _get_all_crm(self):
        unique_str = 'IpJhGfVc4'
        res_show_cmd = 'crm res show'
        oprt_id = s.get_oprt_id()
        res_show_result = s.get_ssh_cmd(SSH, unique_str, res_show_cmd, oprt_id)
        if res_show_result['sts']:
            re_show = f'res_{self.STR}_[0-9]{{1,3}}'
            list_of_all_crm = s.re_findall(
                re_show, res_show_result['rst'].decode('utf-8'))
            return list_of_all_crm

    def crm_show(self):
        '''
        Get the crm resource name through regular matching and determine whether these  exist
        '''
        crm_show_result = self._get_all_crm()
        if crm_show_result:
            list_of_show_crm = s.getshow(
                self.logger, self.STR, self.LIST_ID, crm_show_result)
            if list_of_show_crm:
                print('crm：')
                print(s.print_format(list_of_show_crm))
            return list_of_show_crm
        else:
            return False

    def start_crm_del(self, crm_show_result):
        if crm_show_result:
            for res_name in crm_show_result:
                self.crm_del(res_name)

    def vplx_rescan(self):
        '''
        vplx rescan after delete
        '''
        s.scsi_rescan(SSH, 'r')



if __name__ == '__main__':

    #     test_crm = VplxCrm('72', 'luntest')
    #     test_crm.discover_new_lun()
    pass
