#  coding: utf-8
import connect
import sundry as s
import time
import consts

SSH = None
# DBG_FOLDER = None


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
        print('start rescan SCSI disk deeply')
        s.scsi_rescan(SSH, 'a')
        disk_dev = _find_new_disk()
        if disk_dev:
            return disk_dev
        else:
            s.pwe('xxx:vplx,get_disk_dev fail')

class DebugLog(object):
    def __init__(self):
        init_ssh()
        self.tid = consts.glo_tsc_id()
        self.debug_folder = f'/var/log/{self.tid}_{host}'
        self.dbg = s.DebugLog(SSH, self.debug_folder)
    
    def collect_debug_sys(self):
        cmd_debug_sys = consts.get_cmd_debug_sys(self.debug_folder, host)
        self.dbg.prepare_debug_log(cmd_debug_sys)

    def collect_debug_drbd(self):
        cmd_debug_drbd = consts.get_cmd_debug_drbd(self.debug_folder, host)
        self.dbg.prepare_debug_log(cmd_debug_drbd)

    def collect_debug_crm(self):
        cmd_debug_crm = consts.get_cmd_debug_crm(self.debug_folder, host)
        self.dbg.prepare_debug_log(cmd_debug_crm)

    def get_all_log(self, folder):
        local_file = f'{folder}/{host}.tar'
        self.dbg.get_debug_log(local_file)




class VplxDrbd(object):
    '''
    Integrate LUN in DRBD resources
    '''

    def __init__(self):
        self.logger = consts.glo_log()
        self.STR = consts.glo_str()
        self.ID = consts.glo_id()
        self.ID_LIST = consts.glo_id_list()
        self.rpl = consts.glo_rpl()
        # self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
        #                          'Start to configure DRDB resource and crm resource on VersaPLX')

        self.res_name = f'res_{self.STR}_{self.ID}'
        global DRBD_DEV_NAME
        DRBD_DEV_NAME = f'drbd{self.ID}'
        global RPL
        RPL = consts.glo_rpl()
        self._prepare()

    def _create_iscsi_session(self):
        #-m:是不是s.find_session部分就不需要记录太详细?在外面记录
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

    # def get_disk_device(self):
    #     self.blk_dev_name = get_disk_dev()

    def prepare_config_file(self):
        '''
        Prepare DRDB resource config file
        '''
        #-m:是否要这么简单粗暴?
        if self.rpl == 'yes':
            return
        self._create_iscsi_session()
        blk_dev_name = get_disk_dev()
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'Start prepare config file for resource {self.res_name}') #-v 删除空格

        context = [rf'resource {self.res_name} {{',
                   rf'\ \ \ \ on maxluntarget {{',
                   rf'\ \ \ \ \ \ \ \ device /dev/{DRBD_DEV_NAME}\;',
                   rf'\ \ \ \ \ \ \ \ disk {blk_dev_name}\;',
                   rf'\ \ \ \ \ \ \ \ address 10.203.1.199:7789\;',
                   rf'\ \ \ \ \ \ \ \ node-id 0\;',
                   rf'\ \ \ \ \ \ \ \ meta-disk internal\;',
                   r'\ \ \ \}',
                   r'}']
        if self.rpl == 'yes':
            return
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

        s.pwl(f'Create the DRBD config file "{self.res_name}.res"',2,'','finish')
        # print(f'  Config file "{self.res_name}.res" created')
        # self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
        #                          f'      Create DRBD config file "{self.res_name}.res" done')

    def _drbd_init(self):
        '''
        Initialize DRBD resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'usnkegs'
        cmd = f'drbdadm create-md {self.res_name}'
        info_msg = f'Start to initialize drbd for {self.res_name}'
        s.pwl(info_msg,3,oprt_id,'start')

        init_result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        re_drbd = 'New drbd meta data block successfully created'
        # if init_result:
        re_result = s.re_findall(re_drbd, init_result['rst'].decode())
        if re_result:
            s.pwl(f'Succeed in initializing DRBD resource "{self.res_name}"',4,oprt_id,'finish')# 3->4 +f
            return True
        else:
            s.pwe(f'Resource {self.res_name} initialize failed') #-v 删空格
        # else:
        #     db = consts.glo_db()
        #     print(db.get_exception(consts.glo_tsc_id()))

    def _drbd_up(self):
        '''
        Start DRBD resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'elsflsnek'
        cmd = f'drbdadm up {self.res_name}'
        s.pwl(f'Start to bring up DRBD resource "{self.res_name}"', 3, oprt_id, 'start')
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result['sts']:

            s.pwl(f'Succeed in bringing up DRBD resource "{self.res_name}"',4,oprt_id,'finish')

            return True

    def _drbd_primary(self):
        '''
        Complete initial synchronization of resources
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '7C4LU6Xr'
        cmd = f'drbdadm primary --force {self.res_name}'
        s.pwl(f'Start to initial synchronization for {self.res_name}',3,oprt_id,'start')
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result['sts']:
            s.pwl(f"Succeed in synchronizing DRBD resource {self.res_name}",4,oprt_id,'finish') #-v 3->4
            return True
        else:
            s.pwe(f'drbd resource {self.res_name} primary failed')

    def drbd_cfg(self):
        s.pwl('Start to configure DRBD resource',2,'','start')
        if self._drbd_init():
            if self._drbd_up():
                if self._drbd_primary():
                    return True

    def drbd_status_verify(self):
        '''
        Check DRBD resource status and confirm the status is UpToDate
        '''
        oprt_id = s.get_oprt_id()
        cmd = f'drbdadm status {self.res_name}'
        #-m:这个start是否需要?
        s.pwl(f'Start to check DRBD resource {self.res_name} status',3,oprt_id,'start')
        result = s.get_ssh_cmd(SSH, 'By91GFxC', cmd, oprt_id)
        if result['sts']:
            result = result['rst'].decode()
            re_display = r'''disk:(\w*)'''
            re_result = s.re_findall(re_display, result)
            if re_result:
                status = re_result[0]
                if status == 'UpToDate':

                    s.pwl(f'Succeed in checking DRBD resource "{self.res_name}"',4,oprt_id,'finish')

                    return True
                else:
                    s.pwe(f'{self.res_name} DRBD verification failed',4
            else:
                s.pwe(f'{self.res_name} DRBD does not exist',4)

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

    def get_all_cfgd_drbd(self):
        # get list of all configured crm res
        cmd_drbd_status = 'drbdadm status'
        show_result = s.get_ssh_cmd(SSH, 'UikYgtM1', cmd_drbd_status, s.get_oprt_id())
        # s.dp('drbd show ',show_result)
        if show_result['sts']:
            re_drbd = f'res_\w*_[0-9]{{1,3}}'
            show_result = show_result['rst'].decode('utf-8')
            drbd_cfgd_list = s.re_findall(re_drbd, show_result)
            return drbd_cfgd_list
        else:
            s.pwe(f'command "{cmd_drbd_status}" execute failed')

    def drbd_del(self, res_name):
        if self._drbd_down(res_name):
            if self._drbd_del_config(res_name):
                return True

    def del_all(self, drbd_to_del_list):
        if drbd_to_del_list:
            for res_name in drbd_to_del_list:
                self.drbd_del(res_name)

class VplxCrm(object):
    def __init__(self):
        self.logger = consts.glo_log()
        self.ID = consts.glo_id()
        self.ID_LIST = consts.glo_id_list()
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
        s.pwl(f'Start to create iSCSILogicalUnit resource {self.lu_name}"', 3, oprt_id, 'start')
        # self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
        #                          f'    Start to create iSCSILogicalUnit resource {self.lu_name}')
        cmd = f'crm conf primitive {self.lu_name} \
            iSCSILogicalUnit params target_iqn="{target_iqn}" \
            implementation=lio-t lun={consts.glo_id()} path="/dev/{DRBD_DEV_NAME}"\
            allowed_initiators="{initiator_iqn}" op start timeout=40 interval=0 op stop timeout=40 interval=0 op monitor timeout=40 interval=50 meta target-role=Stopped'
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result['sts']:
            s.pwl(f'Succeed in creating iSCSILogicaLUnit "{self.lu_name}"', 4, oprt_id, 'finish') #3->4
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
        s.pwl(f'Start to setting up iSCSILogicalUnit resources of colocation',3,oprt_id,'start')
        # self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
        #                          '      start to setting up iSCSILogicalUnit resources of colocation')
        result_crm = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_crm['sts']:
            s.pwl(f'Succeed in setting colocation of "{self.lu_name}"', 4, oprt_id, 'finish') # -v 3->4
            # print('    Setting colocation successful')
            # self.logger.write_to_log(
            #     'T', 'INFO', 'info', 'finish', '', '    Setting colocation successful')
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
        s.pwl(f'Start to setting up iSCSILogicalUnit resources of order',3,oprt_id,'start')
        # self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
        #                          '      Start to setting up iSCSILogicalUnit resources of order')
        result_crm = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_crm['sts']:
            s.pwl(f'Succeed in setting order of {self.lu_name}', 4, oprt_id, 'finish')# -v 3->4
            # print('    Setting order succeed')
            # self.logger.write_to_log(
            #     'T', 'INFO', 'info', 'finish', '', '    Setting order succeed')
            return True
        else:
            s.pwe('setting order failed')

    def _crm_setting(self):
        if self._setting_col():
            if self._setting_order():
                return True

    def _crm_start(self):
        '''
        start up the iSCSILogicalUnit resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'YnTDsuVX'
        cmd = f'crm res start {self.lu_name}'
        s.pwl(f'Start up the iSCSILogicalUnit resource {self.lu_name}',3,oprt_id,'start')
        # self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
        #                          f'      Start the iSCSILogicalUnit resource {self.lu_name}')
        result_cmd = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_cmd['sts']:
            s.pwl(f'Succeed in starting up iSCSILogicaLUnit "{self.lu_name}"', 4, oprt_id, 'finish') #-v 3->4
            # print('    ISCSI LUN start successful')
            # self.logger.write_to_log(
            #     'T', 'INFO', 'info', 'finish', '', '    ISCSI LUN start successful')
            return True
        else:
            s.pwe('iscsi lun start failed')

    def crm_cfg(self):
        s.pwl('Start to configure crm resource', 2, '', 'start')
        if self._crm_create():
            if self._crm_setting():
                if self._crm_start():
                    time.sleep(0.5)
                    return True

    def _crm_status_check(self, res_name, status):
        cmd_crm_show = f'crm res show {res_name}'
        result_crm_show = s.get_ssh_cmd(SSH, 'UqmUytK3', cmd_crm_show, s.get_oprt_id())
        if status == 'running':
            re_running = f'resource {res_name} is running on'
            if s.re_findall(re_running, result_crm_show):
                return True
        if status == 'stopped':
            re_stopped = f'resource {res_name} is stopped'  ##################
            if s.re_findall(re_running, result_crm_show):
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

    # def _get_all_crm(self):

    #     oprt_id = s.get_oprt_id()
    #     res_show_result = s.get_ssh_cmd(SSH, unique_str, res_show_cmd, oprt_id)
    #     if res_show_result['sts']:
    #         re_show = 
    #         list_of_all_crm = s.re_findall(
    #             re_show, res_show_result['rst'].decode('utf-8'))
    #         s.dp('out_str',res_show_result['rst'].decode('utf-8'))
    #         s.dp('list_of_all_crm',list_of_all_crm)
    #         return list_of_all_crm

    # def get_tgt_to_del(self):
    #     '''
    #     Get the crm resource name through regular matching and determine whether these exist
    #     '''
    #     crm_show_result = self._get_all_crm()
    #     if crm_show_result:
    #         list_of_show_crm = s.get_to_del_list(crm_show_result)
    #         if list_of_show_crm:
    #             print('crm：')
    #             print(s.print_format(list_of_show_crm))
    #         return list_of_show_crm
    #     else:
    #         return False

    def get_all_cfgd_res(self):
        # get list of all configured crm res
        cmd_crm_res_show = 'crm res show'
        show_result = s.get_ssh_cmd(SSH, 'IpJhGfVc4', cmd_crm_res_show, s.get_oprt_id())
        if show_result['sts']:
            re_crm_res = f'res_\w*_[0-9]{{1,3}}'
            show_result = show_result['rst'].decode('utf-8')
            crm_res_cfgd_list = s.re_findall(re_crm_res, show_result)
            return crm_res_cfgd_list

    # def get_res_to_del(self):
    #     '''
    #     Get all luns through regular matching
    #     '''
    #     # get list of all configured luns
    #     lun_cfgd_list = self._get_all_cfgd_lun()
    #     lun_to_del_list = s.get_to_del_list(lun_cfgd_list)
    #     return lun_to_del_list

    def del_all(self, crm_to_del_list):
        if crm_to_del_list:
            for res_name in crm_to_del_list:
                self.crm_del(res_name)

    def vplx_rescan_r(self):
        '''
        vplx rescan after delete
        '''
        s.scsi_rescan(SSH, 'r')


if __name__ == '__main__':
    #     test_crm = VplxCrm('72', 'luntest')
    #     test_crm.discover_new_lun()
    pass