#  coding: utf-8
import connect
import sundry as s
import time
import sys
import os
import re

# global SSH
SSH = None

global ID
global STRING

host = '10.203.1.199'
port = 22
user = 'root'
password = 'password'
timeout = 3

Netapp_ip = '10.203.1.231'
target_iqn = "iqn.2020-06.com.example:test-max-lun"
initiator_iqn = "iqn.1993-08.org.debian:01:885240c2d86c"
target_name = 't_test'


def init_ssh(logger):
    global SSH
    if not SSH:
        SSH = connect.ConnSSH(host, port, user, password, timeout, logger)
    else:
        pass


def discover_new_lun(logger, cmd_rescan):
    '''
    Scan and find the disk from NetApp
    '''
    logger.write_to_log('T', 'INFO', 'info', 'start', '',
                        f'  Discover_new_lun for id {ID}')
    # self.logger.write_to_log('INFO','info','',f'start to discover_new_lun for id {ID}')
    result_rescan = SSH.execute_command(cmd_rescan)
    # print(result_rescan)
    if result_rescan['sts']:
        cmd_lsscsi = 'lsscsi'
        result_lsscsi = SSH.execute_command(cmd_lsscsi)
        if result_lsscsi['sts']:
            result_lsscsi = result_lsscsi['rst'].decode('utf-8')
        else:
            print(f'command {cmd_lsscsi} execute failed')
            logger.write_to_log('T', 'INFO', 'warning', 'start',
                                '', f'command {cmd_lsscsi} execute failed')
        # log DAT:output:cmd:lsscsi:result_lsscsi
    # if SSH.execute_command('/usr/bin/rescan-scsi-bus.sh'):#新的返回值有状态和数值,以状态判断,记录数值
    #     result_lsscsi = SSH.execute_command('lsscsi')
    else:
        s.pwe(logger, f'Scan new LUN failed on NetApp')
    re_find_id_dev = r'\:(\d*)\].*NETAPP[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
    blk_dev_name = s.get_disk_dev(
        str(ID), re_find_id_dev, result_lsscsi, 'NetApp', logger)

    print(f'Find device {blk_dev_name} for LUN id {ID}')
    logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                        f'    Find device {blk_dev_name} for LUN id {ID}')
    # self.logger.write_to_log('INFO', 'info', '', f'Find device {blk_dev_name} for LUN id {ID}')
    return blk_dev_name


def retry_rescan(logger):
    cmd_rescan = '/usr/bin/rescan-scsi-bus.sh'
    blk_dev_name = discover_new_lun(logger, cmd_rescan)
    # print(blk_dev_name)
    if blk_dev_name:
        return blk_dev_name
    else:
        print('Rescanning...')
        cmd_rescan = '/usr/bin/rescan-scsi-bus.sh -a'
        blk_dev_name = discover_new_lun(logger, cmd_rescan)
        if blk_dev_name:
            return blk_dev_name
        else:
            s.pwe(logger, 'Did not find the new LUN from Netapp,program exit...')


class VplxDrbd(object):
    '''
    Integrate LUN in DRBD resources
    '''

    def __init__(self, logger):
        self.logger = logger
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 'Start to configure DRDB resource and crm resource on VersaPLX')
        init_ssh(self.logger)
        self.blk_dev_name = retry_rescan(logger)
        self.res_name = f'res_{STRING}_{ID}'
        global DRBD_DEV_NAME
        DRBD_DEV_NAME = f'drbd{ID}'
        # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
        # start
        # log INF:info:start to config drbd resource {r_name}
        # self.logger.write_to_log('INFO','info','',f'start to config drbd resource {self.res_name}')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'    Start to configure DRBD resource {self.res_name}')

    def prepare_config_file(self):
        '''
        Prepare DRDB resource config file
        '''
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'      Start prepare config fiel for resource {self.res_name}')
        context = [rf'resource {self.res_name} {{',
                   rf'\ \ \ \ on maxluntarget {{',
                   rf'\ \ \ \ \ \ \ \ device /dev/{DRBD_DEV_NAME}\;',
                   rf'\ \ \ \ \ \ \ \ disk {self.blk_dev_name}\;',
                   rf'\ \ \ \ \ \ \ \ address 10.203.1.199:7789\;',
                   rf'\ \ \ \ \ \ \ \ node-id 0\;',
                   rf'\ \ \ \ \ \ \ \ meta-disk internal\;',
                   r'\ \ \ \}',
                   r'}']

        # self.logger.write_to_log('DATA','input','context',context)
        # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
        # [time],[transaction_id],[-],[DATA],[value],[list],['content of drbd config file'],[data]
        self.logger.write_to_log(
            'F', 'DATA', 'value', 'list', 'content of drbd config file', context)

        # for echo_command in context:
        #     echo_result = SSH.execute_command(
        #         f'echo {echo_command} >> /etc/drbd.d/{self.res_name}.res')
        #     if echo_result is True:
        #         continue
        #     else:
        #         s.pe('fail to prepare drbd config file..')
        config_file_name = f'{self.res_name}.res'
        for i in range(len(context)):
            if i == 0:
                echo_result = SSH.execute_command(
                    f'echo {context[i]} > /etc/drbd.d/{config_file_name}')
            else:
                echo_result = SSH.execute_command(
                    f'echo {context[i]} >> /etc/drbd.d/{config_file_name}')
            # result of ssh command like (1,'done'),1 for status, 'done' for data.
            if echo_result['sts']:
                continue
            else:
                # print('fail to prepare drbd config file..')
                # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
                # [time],[transaction_id],[s],[INFO],[error],[exit],[d2],['fail to prepare drbd config file..']
                # ??? oprt
                s.pwe(self.logger, 'fail to prepare drbd config file..')
                # sys.exit()

                # s.pwe(self.logger,'fail to prepare drbd config file..')
        print(f'create DRBD config file "{self.res_name}.res" done')
        self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                                 f'      Create DRBD config file "{self.res_name}.res" done')
        # [time],[transaction_id],[display],[INFO],[info],[finish],[d2],[data]
        # self.logger.write_to_log('INFO','info','',f'Create DRBD config file "{self.res_name}.res" done')

    def _drbd_init(self):
        '''
        Initialize DRBD resource
        '''
        info_msg = f'      Initialize drbd for {self.res_name}'
        # self.logger.write_to_log('INFO','info','',f'info:start to init drbd for {self.res_name}')
        # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
        # [time],[transaction_id],[s],[INFO],[info],[start],[d2],[info_msg]
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', info_msg)
        init_cmd = f'drbdadm create-md {self.res_name}'
        # print(init_cmd)
        drbd_init = SSH.execute_command(init_cmd)
        # log DAT:output:cmd:f'{init_cmd}':start to init drbd for {self.res_name}
        if drbd_init['sts']:
            drbd_init = drbd_init['rst'].decode('utf-8')
            # print(drbd_init)
            re_drbd = re.compile(
                'New drbd meta data block successfully created')
            # [time],[transaction_id],[-],[OPRT],[re],[findall],[d2],[data]
            re_init = re_drbd.findall(drbd_init)
            # [time],[transaction_id],[s],[INFO],[info],[d1],[d2],[data]
            # [time],[transaction_id],[-],[DATA],[re],[d1],[d2],[data]
            # self.logger.write_to_log('DATA','output','re_result',re_init)
            oprt_id = s.get_oprt_id()
            self.logger.write_to_log(
                'T', 'OPRT', 'regular', 'findall', oprt_id, drbd_init)
            self.logger.write_to_log(
                'F', 'DATA', 'regular', 'findall', oprt_id, re_init)
            if re_init:
                print(f'{self.res_name} initialize success')
                # self.logger.write_to_log('INFO','info','',(f'{self.res_name} initialize success'))
                return True
            else:
                s.pwe(self.logger,
                      f'drbd resource {self.res_name} initialize failed')

        else:
            s.pwe(self.logger,
                  f'drbd resource {self.res_name} initialize failed')

    def _drbd_up(self):
        '''
        Start DRBD resource
        '''
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', '', f'      Start to drbd up for {self.res_name}')
        up_cmd = f'drbdadm up {self.res_name}'
        drbd_up = SSH.execute_command(up_cmd)
        if drbd_up['sts']:
            print(f'{self.res_name} up success')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', f'      {self.res_name} started successfully')
            # self.logger.write_to_log('INFO','info','',(f'{self.res_name} up success'))
            return True
        else:
            s.pwe(self.logger, f'drbd resource {self.res_name} up failed')

    def _drbd_primary(self):
        '''
        Complete initial synchronization of resources
        '''
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'      Start to initial synchronization for {self.res_name}')
        primary_cmd = f'drbdadm primary --force {self.res_name}'
        drbd_primary = SSH.execute_command(primary_cmd)
        if drbd_primary['sts']:
            print(f'{self.res_name} primary success')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', f'      {self.res_name} synchronize successfully')
            # self.logger.write_to_log('INFO','info','',(f'{self.res_name} primary success'))
            return True
        else:
            s.pwe(self.logger, f'drbd resource {self.res_name} primary failed')

    def drbd_cfg(self):
        if self._drbd_init():
            if self._drbd_up():
                if self._drbd_primary():
                    return True

    def drbd_status_verify(self):
        '''
        Check DRBD resource status and confirm the status is UpToDate
        '''
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', '', '      Start to check DRBD resource status')
        verify_cmd = f'drbdadm status {self.res_name}'
        result = SSH.execute_command(verify_cmd)
        if result['sts']:
            result = result['rst'].decode('utf-8')
            re_display = re.compile(r'''disk:(\w*)''')
            re_result = re_display.findall(result)
            oprt_id = s.get_oprt_id()
            self.logger.write_to_log(
                'T', 'OPRT', 'regular', 'findall', oprt_id, result)
            if re_result:
                status = re_result[0]
                self.logger.write_to_log(
                    'F', 'DATA', 'regular', 'findall', oprt_id, status)
                if status == 'UpToDate':
                    print(f'{self.res_name} DRBD check successfully')
                    self.logger.write_to_log(
                        'T', 'INFO', 'info', 'finish', '', f'      {self.res_name} DRBD check successfully')
                    # self.logger.write_to_log('INFO','info','',(f'{self.res_name} DRBD check successful'))
                    return True
                else:
                    s.pwe(self.logger,
                          f'{self.res_name} DRBD verification failed')
            else:
                s.pwe(self.logger, f'{self.res_name} DRBD does not exist')

    def vplx_login(self):
        '''
        Discover iSCSI server and login to session
        '''
        login_cmd = f'iscsiadm -m discovery -t st -p {Netapp_ip} -l'
        login_result = SSH.execute_command(login_cmd)
        if s.iscsi_login(self.logger, Netapp_ip, login_result):
            return True

    def vplx_session(self):
        '''
        Execute the command and check up the status of session
        '''
        session_cmd = 'iscsiadm -m session'
        session_result = SSH.execute_command(session_cmd)
        if s.find_session(Netapp_ip, session_result):
            return True


class VplxCrm(object):
    def __init__(self, logger):
        init_ssh(logger)
        self.logger = logger
        self.lu_name = f'res_{STRING}_{ID}'  # same as drbd resource name
        self.colocation_name = f'co_{self.lu_name}'
        self.order_name = f'or_{self.lu_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start',
                                 '', f'  Start to configure crm resource {self.lu_name}')
        # self.logger.write_to_log('INFO','info','',f'start to config crm resource {self.lu_name}') #

    def _crm_create(self):
        '''
        Create iSCSILogicalUnit resource
        '''
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'    Start to create iSCSILogicalUnit resource {self.lu_name}')
        cmd_crm_create = f'crm conf primitive {self.lu_name} \
            iSCSILogicalUnit params target_iqn="{target_iqn}" \
            implementation=lio-t lun={ID} path="/dev/{DRBD_DEV_NAME}"\
            allowed_initiators="{initiator_iqn}" op start timeout=40 interval=0 op stop timeout=40 interval=0 op monitor timeout=40 interval=50 meta target-role=Stopped'
        result_crm_create = SSH.execute_command(cmd_crm_create)
        if result_crm_create['sts']:
            print('create iSCSILogicalUnit successfully')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', '      Create iSCSILogicalUnit successfully')
            # self.logger.write_to_log('INFO','info','',('iscisi lun_create success'))
            return True
        else:
            s.pwe(self.logger, 'iscisi lun_create failed')

    def _setting_col(self):
        '''
        Setting up iSCSILogicalUnit resources of colocation
        '''
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 '      start to setting up iSCSILogicalUnit resources of colocation')
        cmd_crm_col = f'crm conf colocation {self.colocation_name} inf: {self.lu_name} {target_name}'
        result_crm_col = SSH.execute_command(cmd_crm_col)
        if result_crm_col['sts']:
            print('  setting colocation successful')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', '      Setting colocation successful')
            return True
        else:
            s.pwe(self.logger, 'setting colocation failed')

    def _setting_order(self):
        '''
        Setting up iSCSILogicalUnit resources of order
        '''
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 '      Start to setting up iSCSILogicalUnit resources of order')
        cmd_crm_order = f'crm conf order {self.order_name} {target_name} {self.lu_name}'
        result_crm_order = SSH.execute_command(cmd_crm_order)
        if result_crm_order['sts']:
            print('setting order succeed')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', '      Setting order succeed')
            return True
        else:
            s.pwe(self.logger, 'setting order failed')

    def _crm_setting(self):
        if self._setting_col():
            if self._setting_order():
                # self.logger.write_to_log('VplxCrm', 'return', '_setting_col', True)
                return True

    def _crm_start(self):
        '''
        start the iSCSILogicalUnit resource
        '''
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'      Start the iSCSILogicalUnit resource {self.lu_name}')
        cmd_lu_start = f'crm res start {self.lu_name}'
        result_lu_start = SSH.execute_command(cmd_lu_start)
        if result_lu_start['sts']:
            print('  iSCSI LUN start successful')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', '', '      ISCSI LUN start successful')
            return True
        else:
            s.pwe(self.logger, 'iscsi lun start failed')

    def crm_cfg(self):
        if self._crm_create():
            if self._crm_setting():
                if self._crm_start():
                    return True

    def _crm_verify(self, res_name, status):
        '''
        Check the crm resource status
        '''
        verify_result = SSH.execute_command('crm res show')
        if verify_result:
            re_show = re.compile(f'({res_name})\s.*:\s(\w*)')
            re_show_result = re_show.findall(
                verify_result['rst'].decode('utf-8'))
            dict_show_result = dict(re_show_result)
            if res_name in dict_show_result.keys():
                crm_status = dict_show_result[res_name]
                if crm_status == f'{status}':
                    return True
                else:
                    return False
        else:
            s.pwe(self.logger, 'crm show failed')

    def crm_status(self, res_name, status):
        '''
        Determine crm resource status is started/stopped
        '''
        n = 0
        while n < 10:
            n += 1
            if self._crm_verify(res_name, status):
                print(f'{res_name} is {status}')
                return True
            else:
                print(f'{res_name} is {status}, Wait a moment...')
                time.sleep(1.5)
        else:
            return False

    def _crm_stop(self, res_name):
        '''
        stop the iSCSILogicalUnit resource
        '''
        crm_stop_cmd = (f'crm res stop {res_name}')
        crm_stop = SSH.execute_command(crm_stop_cmd)
        if crm_stop['sts'] == 1:
            if self.crm_status(res_name, 'Stopped'):
                return True
        else:
            s.pwe(self.logger, 'crm stop failed')

    def _crm_del(self, res_name):
        '''
        Delete the iSCSILogicalUnit resource
        '''
        crm_del_cmd = f'crm cof delete {res_name}'
        del_result = SSH.execute_command(crm_del_cmd)
        if del_result:
            re_delstr = re.compile('deleted')
            re_result = re_delstr.findall(
                str(del_result['rst'], encoding='utf-8'))
            if len(re_result) == 2:
                return True
            else:
                s.pwe(self.logger, 'crm cof delete failed')

    def _drbd_down(self, res_name):
        '''
        Stop the DRBD resource
        '''
        drbd_down_cmd = f'drbdadm down {res_name}'
        down_result = SSH.execute_command(drbd_down_cmd)
        if down_result['sts'] == 1:
            return True
        else:
            s.pwe(self.logger, 'drbd down failed')

    def _drbd_del(self, res_name):
        '''
        remove the DRBD config file
        '''
        drbd_del_cmd = f'rm /etc/drbd.d/{res_name}.res'
        del_result = SSH.execute_command(drbd_del_cmd)
        if del_result['sts'] == 1:
            return True
        else:
            s.pwe(self.logger, 'drbd remove config file fail')

    def start_del(self, res_name):
        if self._crm_stop(res_name):
            if self._crm_del(res_name):
                if self._drbd_down(res_name):
                    if self._drbd_del(res_name):
                        return True

    def vplx_show(self, unique_str, unique_id):
        '''
        Get the resource name through regular matching and determine whether these LUNs exist
        '''
        res_show_result = SSH.execute_command('crm res show')
        if res_show_result:
            re_show = re.compile(f'res_{unique_str}_\w*')
            re_result = re_show.findall(res_show_result['rst'].decode('utf-8'))
            if re_result:
                if unique_id:
                    if len(unique_id) == 2:
                        return s.range_uid(self.logger, unique_str, unique_id, re_result, 'res_')
                    elif len(unique_id) == 1:
                        return s.one_uid(self.logger, unique_str, unique_id, re_result, 'res_')
                    else:
                        s.pwe(self.logger, 'please enter a valid value')
                else:
                    print(f'{re_result} is found')
                    return re_result
            else:
                s.pwe(self.logger, 'LUNs does not exists,exit this program')

    def del_comfirm(self, del_result):
        '''
        User determines whether to delete
        '''
        comfirm = input('Do you want to delete these lun (yes/no):')
        if comfirm == 'yes':
            for res_name in del_result:
                self.start_del(res_name)
        else:
            s.pwe(self.logger, 'Cancel succeed')

    def vlpx_del(self, unique_str, unique_id):
        '''
        Call the function method to delete
        '''
        del_result = self.vplx_show(unique_str, unique_id)
        self.del_comfirm(del_result)

    def vplx_rescan(self):
        '''
        vplx rescan after delete
        '''
        rescan_cmd = 'rescan-scsi-bus.sh -r'
        SSH.execute_command(rescan_cmd)
        SSH.execute_command('rescan-scsi-bus.sh -a')


# if __name__ == '__main__':
#     test_crm = VplxCrm('72', 'luntest')
#     test_crm.discover_new_lun()
