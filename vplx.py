#  coding: utf-8
import connect
import sundry as s
import time
import consts
import log
import re
import sys
SSH = None

HOST = '10.203.1.199'
PORT = 22
USER = 'root'
PASSWORD = 'password'
TIMEOUT = 3

NETAPP_IP = '10.203.1.231'
TARGET_IQN = "iqn.2020-06.com.example:test-max-lun"
TARGET_NAME = 't_test'
PORTBLOCK_UNBLOCK_NAME="p_iscsi_portblock_off"


def init_ssh():
    global SSH
    if not SSH:
        SSH = connect.ConnSSH(HOST, PORT, USER, PASSWORD, TIMEOUT)
    else:
        pass


def _find_new_disk():
    id=consts.glo_id()
    result_lsscsi = s.get_lsscsi(SSH, 'D37nG6Yi', s.get_oprt_id())
    re_string = f'\:{id}\].*NETAPP[ 0-9a-zA-Z._]*(/dev/sd[a-z]{{1,3}})'
    disk_dev= s.re_search(re_string, result_lsscsi)
    if disk_dev:
        return disk_dev.group(1)


def get_disk_dev():
    s.scsi_rescan(SSH, 'n')
    disk_dev = _find_new_disk()
    if disk_dev:
        s.pwl(f'Succeed in getting disk device "{disk_dev}" with id {consts.glo_id()}', 3, '', 'finish')
        return disk_dev
    else:
        s.scsi_rescan(SSH, 'a')
        s.pwl(f'No disk with SCSI ID "{consts.glo_id()}" found, scan again...', 3, '', 'start')
        disk_dev = _find_new_disk() #这里需要查询到的第二个结果，现在返回第一个。
        if disk_dev:
            s.pwl('Found the disk successfully', 4, '', 'finish')
            return disk_dev
        else:
            s.pwce('No disk found, exit the program', 4, 2)


class DebugLog(object):
    def __init__(self):
        init_ssh()
        self.tid = consts.glo_tsc_id()
        self.debug_folder = f'/var/log/{self.tid}'
        self.dbg = s.DebugLog(SSH, self.debug_folder, HOST)

    def collect_debug_sys(self):
        cmd_debug_sys = consts.get_cmd_debug_sys(self.debug_folder, HOST)
        self.dbg.prepare_debug_log(cmd_debug_sys)

    def collect_debug_drbd(self):
        cmd_debug_drbd = consts.get_cmd_debug_drbd(self.debug_folder, HOST)
        self.dbg.prepare_debug_log(cmd_debug_drbd)

    def collect_debug_crm(self):
        cmd_debug_crm = consts.get_cmd_debug_crm(self.debug_folder, HOST)
        self.dbg.prepare_debug_log(cmd_debug_crm)

    def get_all_log(self, folder):
        local_file = f'{folder}/{HOST}.tar'
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
        self.res_name = f'res_{self.STR}_{self.ID}'
        global DRBD_DEV_NAME
        DRBD_DEV_NAME = f'drbd{self.ID}'
        global RPL
        RPL = consts.glo_rpl()
        self._prepare()
        self.iscsi=s.Iscsi(SSH,NETAPP_IP)

    def _prepare(self):
        if self.rpl == 'no':
            init_ssh()

    def prepare_config_file(self):
        '''
        Prepare DRDB resource config file
        '''
        self.iscsi.create_iscsi_session()
        s.pwl(f'Start to get the disk device with id {consts.glo_id()}', 2)
        blk_dev_name = get_disk_dev()
        s.pwl(f'Start to prepare DRBD config file "{self.res_name}.res"', 2, '', 'start')
        # self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
        #                          f'Start prepare config file for resource {self.res_name}')

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
            if echo_result['sts']:
                continue
            else:
                s.pwce('Failed to prepare DRBD config file..', 3, 2)

        s.pwl(f'Succeed in creating DRBD config file "{self.res_name}.res"', 3, '', 'finish')

    def _drbd_init(self):
        '''
        Initialize DRBD resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'usnkegs'
        cmd = f'drbdadm create-md {self.res_name}'
        info_msg = f'Start to initialize DRBD resource for "{self.res_name}"'
        s.pwl(info_msg, 3, oprt_id, 'start')
        init_result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        re_drbd = 'New drbd meta data block successfully created'
        if init_result:
            if init_result['sts']:
                re_result = s.re_search(re_drbd, init_result['rst'].decode())
                if re_result:
                    s.pwl(f'Succeed in initializing DRBD resource "{self.res_name}"', 4, oprt_id, 'finish')
                    return True
                else:
                    s.pwce(f'Failed to initialize DRBD resource {self.res_name}', 4, 2)
        else:
            s.handle_exception()

    def _drbd_up(self):
        '''
        Start DRBD resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'elsflsnek'
        cmd = f'drbdadm up {self.res_name}'
        s.pwl(f'Start to bring up DRBD resource "{self.res_name}"', 3, oprt_id, 'start')
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result:
            if result['sts']:
                s.pwl(f'Succeed in bringing up DRBD resource "{self.res_name}"', 4, oprt_id, 'finish')
                return True
            else:
                s.pwce(f'Failed to bring up resource {self.res_name}', 4, 2)
        else:
            s.handle_exception()

    def _drbd_primary(self):
        '''
        Complete initial synchronization of resources
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '7C4LU6Xr'
        cmd = f'drbdadm primary --force {self.res_name}'
        s.pwl(f'Start to initial synchronization for "{self.res_name}"', 3, oprt_id, 'start')
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result:
            if result['sts']:
                s.pwl(f'Succeed in synchronizing DRBD resource "{self.res_name}"', 4, oprt_id, 'finish')
                return True
            else:
                s.pwce(f'Failed to synchronize resource {self.res_name}', 4, 2)
        else:
            s.handle_exception()

    def drbd_cfg(self):
        s.pwl('Start to configure DRBD resource', 2, '', 'start')
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
        s.pwl(f'Start to check DRBD resource "{self.res_name}" status', 3, oprt_id, 'start')
        result = s.get_ssh_cmd(SSH, 'By91GFxC', cmd, oprt_id)
        if result:
            if result['sts']:
                result = result['rst'].decode()
                re_display = r'''disk:(\w*)'''
                re_result = s.re_search(re_display, result)
                if re_result:
                    status = re_result.group(1)
                    if status == 'UpToDate':
                        s.pwl(f'Succeed in checking DRBD resource "{self.res_name}"', 4, oprt_id, 'finish')

                        return True
                    else:
                        s.pwce(f'Failed to check DRBD resource "{self.res_name}"', 4, 2)
                else:
                    s.pwce(f'DRBD {self.res_name} does not exist', 4, 2)
        else:
            s.handle_exception()

    def _drbd_down(self, res_name):
        '''
        Stop the DRBD resource
        '''
        unique_str = 'UqmYgtM3'
        drbd_down_cmd = f'drbdadm down {res_name}'
        oprt_id = s.get_oprt_id()
        down_result = s.get_ssh_cmd(SSH, unique_str, drbd_down_cmd, oprt_id)
        if down_result['sts']:
            s.pwl(f'Down the DRBD resource "{res_name}" successfully',2)
            return True
        else:
            s.pwce(f'Failed to stop DRBD "{res_name}"', 4, 2)

    def _drbd_del_config(self, res_name):
        '''
        remove the DRBD config file
        '''
        unique_str = 'UqkYgtM3'
        drbd_del_cmd = f'rm /etc/drbd.d/{res_name}.res'
        oprt_id = s.get_oprt_id()
        del_result = s.get_ssh_cmd(SSH, unique_str, drbd_del_cmd, oprt_id)
        if del_result['sts']:
            s.pwl(f'Removed the DRBD resource "{res_name}" config file successfully',2)
            return True
        else:
            s.pwce('Failed to remove DRBD config file', 4, 2)
  

    def get_all_cfgd_drbd(self):
        # get list of all configured crm res
        cmd_drbd_status = 'drbdadm status'
        show_result = s.get_ssh_cmd(SSH, 'UikYgtM1', cmd_drbd_status, s.get_oprt_id())
        if show_result:
            if show_result['sts']:
                re_drbd = f'res_\w*_[0-9]{{1,3}}'
                show_result = show_result['rst'].decode('utf-8')
                drbd_cfgd_list = s.re_findall(re_drbd, show_result)
                return drbd_cfgd_list
            else:
                s.pwe(f'Failed to execute command "{cmd_drbd_status}"', 3, 2)
        else:
            s.handle_exception()


    def drbd_del(self, res_name):
        s.pwl(f'Deleting DRBD resource {res_name}',1)
        if self._drbd_down(res_name):
            if self._drbd_del_config(res_name):
                return True

    def del_all(self, drbd_to_del_list):
        if drbd_to_del_list:
            s.pwl('Start to delete DRBD resource',0)
            for res_name in drbd_to_del_list:
                self.drbd_del(res_name)


class VplxCrm(object):
    def __init__(self):
        self.logger = consts.glo_log()
        self.ID = consts.glo_id()
        self.ID_LIST = consts.glo_id_list()
        self.STR = consts.glo_str()
        self.rpl = consts.glo_rpl()
        self.lu_name = f'res_{self.STR}_{self.ID}'
        self.colocation_name = f'co_{self.lu_name}'
        self.order_name = f'or_{self.lu_name}'
        self.order_name2=f'or_{self.lu_name}_prtoff'
        if self.rpl == 'no':
            init_ssh()

    def _crm_create(self):
        '''
        Create iSCSILogicalUnit resource
        '''
        oprt_id = s.get_oprt_id()
        if consts.glo_iqn_list():
            initiator_iqn=' '.join(consts.glo_iqn_list())
        else:
            s.pwe('Global IQN list is None',2,2)
        unique_str = 'LXYV7dft'
        s.pwl(f'Start to create iSCSILogicalUnit resource "{self.lu_name}"', 3, oprt_id, 'start')
        cmd = f'crm conf primitive {self.lu_name} \
            iSCSILogicalUnit params target_iqn="{TARGET_IQN}" \
            implementation=lio-t lun={consts.glo_id()} path="/dev/{DRBD_DEV_NAME}"\
            allowed_initiators="{initiator_iqn}" op start timeout=600 interval=0 op stop timeout=600 interval=0 op monitor timeout=40 interval=50 meta target-role=Stopped'#40->600
        result = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result:
            if result['sts']:
                s.pwl(f'Succeed in creating iSCSILogicaLUnit "{self.lu_name}"', 4, oprt_id, 'finish')
                return True
            else:
                s.pwce(f'Failed to create iSCSILogicaLUnit "{self.lu_name}"', 4, 2)
        else:
            s.handle_exception()

    def _setting_col(self):
        '''
        Setting up iSCSILogicalUnit resources of colocation
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'E03YgRBd'
        cmd = f'crm conf colocation {self.colocation_name} inf: {self.lu_name} {TARGET_NAME}'
        s.pwl(f'Start to set up colocation of iSCSILogicalUnit "{self.lu_name}"', 3, oprt_id, 'start')
        result_crm = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_crm:
            if result_crm['sts']:
                s.pwl(f'Succeed in setting colocation of "{self.lu_name}"', 4, oprt_id, 'finish')
                return True
            else:
                s.pwce(f'Failed to set colocation of "{self.lu_name}"', 4, 2)
        else:
            s.handle_exception()

    def _setting_order(self):
        '''
        Setting up iSCSILogicalUnit resources of order
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '0GHI63jX'
        cmd = f'crm conf order {self.order_name} {TARGET_NAME} {self.lu_name}'
        s.pwl(f'Start to set up order of iSCSILogicalUnit "{self.lu_name}"', 3, oprt_id, 'start')
        result_crm = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_crm:
            if result_crm['sts']:
                s.pwl(f'Succeed in setting order of "{self.lu_name}"', 4, oprt_id, 'finish')
                return True
            else:
                s.pwce(f'Failed to set order of "{self.lu_name}"', 4, 2)
        else:
            s.handle_exception()
    
    def _setting_portblock(self):
        oprt_id=s.get_oprt_id()
        unique_str='TgFqUiOkl'
        cmd=f'crm conf order {self.order_name2} {self.lu_name} {PORTBLOCK_UNBLOCK_NAME}'
        s.pwl(f'Start to set up portblock of iSCSILogicalUnit "{self.lu_name}"', 3, oprt_id, 'start')
        results=s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if results:
            if results['sts']:
                s.pwl(f'Succeed in setting portblock of "{self.lu_name}"', 4, oprt_id, 'finish')
                return True
            else:
                s.pwce(f'Failed to set portblock of "{self.lu_name}"', 4, 2)
        else:
            s.handle_exception()


    def _crm_setting(self):
        if self._setting_col():
            if self._setting_order():
                if self._setting_portblock():
                    return True

    def _crm_start(self):
        '''
        start up the iSCSILogicalUnit resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'YnTDsuVX'
        cmd = f'crm res start {self.lu_name}'
        s.pwl(f'Start up the iSCSILogicalUnit resource "{self.lu_name}"', 3, oprt_id, 'start')
        result_cmd = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_cmd:
            if result_cmd['sts']:
                if self._check_crm_status(self.lu_name,'Started'):
                    s.pwl(f'Succeed in starting up iSCSILogicaLUnit "{self.lu_name}"', 4, oprt_id, 'finish')
                    return True
                else:
                    s.pwce(f'Failed to start up iSCSILogicaLUnit "{self.lu_name}"', 4, 2)
            else:
                s.pwce(f'Failed to start up iSCSILogicaLUnit "{self.lu_name}"', 4, 2)
        else:
            s.handle_exception()

    def crm_cfg(self):
        s.pwl('Start to configure crm resource', 2, '', 'start')
        if self._crm_create():
            if self._crm_setting():
                if self._crm_start():
                    time.sleep(0.5)
                    return True


    def _get_crm_status(self, res_name):
        '''
        Check the crm resource status
        '''
        unique_str = 'UqmUytK3'
        crm_show_cmd = f'crm res list | grep {res_name}'
        oprt_id = s.get_oprt_id()
        verify_result = s.get_ssh_cmd(SSH, unique_str, crm_show_cmd, oprt_id)
        if verify_result:
            if verify_result['sts']:
                re_string=f'''{res_name}\s*\(ocf::heartbeat:\w*\):\s*(\w*)'''
                re_result=s.re_search(re_string, verify_result['rst'].decode('utf-8'))
                if re_result:
                    return {'status': re_result.group(1)}
                else:
                    s.pwce('Failed to show crm',4,2)
            else:
                s.pwce('Failed to show crm',4,2)
        else:
            s.handle_exception()
            

    def cyclic_check_crm_status(self, res_name, expect_status,sec, num):
        '''
        Determine crm resource status is started/stopped
        '''
        n = 0
        while n < num:
            n += 1
            if self._get_crm_status(res_name)['status'] != expect_status:
                time.sleep(sec)
            else:
                if self._targetcli_verify():
                    return True        

    def _crm_stop(self, res_name):
        '''
        stop the iSCSILogicalUnit resource
        '''
        unique_str = 'UqmYgtM1'
        crm_stop_cmd = (f'crm res stop {res_name}')
        oprt_id = s.get_oprt_id()
        crm_stop = s.get_ssh_cmd(SSH, unique_str, crm_stop_cmd, oprt_id)
        if crm_stop:
            if crm_stop['sts']:
                if self._check_crm_status(res_name, 'Stopped'):
                    s.prt(f'Succeed in Stopping the iSCSILogicalUnit resource "{res_name}"', 2)
                    return True
                else:
                    s.pwce('Failed to stop CRM resource ,exit the program...', 3, 2)
            else:
                s.pwce('Failed to stop CRM resource', 3, 2)
        else:
            s.handle_exception()


    def _crm_del(self, res_name):
        '''
        Delete the iSCSILogicalUnit resource
        '''
        unique_str = 'EsTyUqIb5'
        crm_del_cmd = f'crm cof delete {res_name}'
        oprt_id = s.get_oprt_id()
        del_result = s.get_ssh_cmd(SSH, unique_str, crm_del_cmd, oprt_id)
        # a:delete_result为error
        if del_result:
            re_delstr = 'deleted'
            re_result = s.re_findall(
                re_delstr, del_result['rst'].decode('utf-8'))
            if len(re_result) == 3:
                s.prt(f'Succeed in deleting the iSCSILogicalUnit resource "{res_name}"', 2)
                return True
            else:
                s.pwce(f'Failed to delete the iSCSILogicalUnit resource "{res_name}"', 3, 2)
        else:
            s.handle_exception()

    def crm_del(self, res_name):
        s.pwl(f'Deleting crm resource {res_name}',1)
        if self._crm_stop(res_name):
            if self._crm_del(res_name):
                return True


    def get_all_cfgd_res(self):
        # get list of all configured crm res
        cmd_crm_res_show = 'crm res show'
        show_result = s.get_ssh_cmd(
            SSH, 'IpJhGfVc4', cmd_crm_res_show, s.get_oprt_id())
        if show_result['sts']:
            re_crm_res = f'res_\w*_[0-9]{{1,3}}'
            show_result = show_result['rst'].decode('utf-8')
            crm_res_cfgd_list = s.re_findall(re_crm_res, show_result)
            return crm_res_cfgd_list



    def del_all(self, crm_to_del_list):
        if crm_to_del_list:
            s.pwl('Start to delete CRM resource',0)
            for res_name in crm_to_del_list:
                self.crm_del(res_name)

    def vplx_rescan_r(self):
        '''
        vplx rescan after delete
        '''
        s.scsi_rescan(SSH, 'r')

    
    def modify_allow_initiator(self):
        iqn_string=' '.join(consts.glo_iqn_list())
        cmd=f'crm conf set {self.lu_name}.allowed_initiators "{iqn_string}"'
        oprt_id=s.get_oprt_id()
        result=s.get_ssh_cmd(SSH,'',cmd,oprt_id)
        if result:
            if result['sts']:
                if self._check_crm_status(self.lu_name,'Started'):
                    s.pwl('Success in modify the allow initiator', 2, oprt_id)
                else:
                    s.pwe('Failed in verify the allow initiator', 2, 2)   
            else:
                s.pwe('Failed in modify the allow initiator', 2, 2)
        else:
            s.handle_exception()
    
    def _targetcli_verify(self):
        cmd=f'targetcli ls iscsi/{TARGET_IQN}/tpg1/acls'
        oprt_id=s.get_oprt_id()
        results=s.get_ssh_cmd(SSH,'',cmd,oprt_id)
        if results:
            if results['sts']:
                # print(results['rst'].decode('utf-8'))
                restr = re.compile(f'''(iqn.1993-08.org.debian:01:2b129695b8bbmaxhost{self.ID}.\d+).*?mapped_lun{self.ID}''', re.DOTALL)
                re_result=restr.findall(results['rst'].decode('utf-8'))
                if re_result:
                    if re_result==consts.glo_iqn_list():
                        return True
                else:
                    return False    
        else:
            s.handle_exception() 

    # def _crm_restart(self):
    #     cmd=f'crm res restart {self.lu_name}'
    #     oprt_id=s.get_oprt_id()
    #     results=s.get_ssh_cmd(SSH,'',cmd,oprt_id)
    #     if results:
    #         return True
    #     else:
    #         s.handle_exception()
    
    # def _crm_ref(self):
    #     cmd=f'crm res ref'
    #     oprt_id=s.get_oprt_id()
    #     results=s.get_ssh_cmd(SSH,'',cmd,oprt_id)
    #     if results:
    #         if results['sts']:
    #             return True
    #     else:
    #         s.handle_exception()

        
    def _check_crm_status(self,res_name,expect_status):
        if self._get_crm_status(res_name)['status']==expect_status:
            return True
        elif self._get_crm_status(res_name)['status']=='FAILED':
            s.pwe('Failed in CRM status is "FAILED"',2,2)
        elif self._get_crm_status(res_name)['status']!=expect_status:
            if self.cyclic_check_crm_status(res_name,expect_status,6,100):
                return True

    
    # def crm_targetcli_verify(self):
    #     if self._check_crm_status(self.lu_name,'Started'):
    #         if self._targetcli_verify():
    #             return True
    
    # def cyclic_crm_targetcli_verify(self):
    #     n=0
    #     while n<100:
    #         n+=1
    #         if self.crm_targetcli_verify():
    #             return True
    #         else:
    #             time.sleep(6)
    #     else:
    #         s.pwce('Failed to verify the CRM and targetcli status',2,2)


if __name__ == '__main__':
    # pass
    logger = log.Log(s.get_transaction_id())
    consts._init()
    consts.set_glo_log(logger)
    consts.set_glo_id('')
    consts.set_glo_id_list('')
    consts.set_glo_str('luntest')
    consts.set_glo_rpl('no')
    test_crm = VplxCrm()
    # test_crm._crm_verify('res_hosttest_100')
    # 
    
