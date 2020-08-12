# coding:utf-8
import connect
import time
import sundry as s
import consts
import log

SSH = None

VPLX_IP = '10.203.1.199'
HOST = '10.203.1.200'
PORT = 22
USER = 'root'
PASSWORD = 'password'
TIMEOUT = 3
MOUNT_POINT = '/mnt'
TARGET_IQN='iqn.2020-06.com.example:test-max-lun'


def init_ssh():
    global SSH
    if not SSH:
        SSH = connect.ConnSSH(HOST, PORT, USER, PASSWORD, TIMEOUT)
    else:
        pass


def umount_mnt():
    SSH.execute_command(f'umount {MOUNT_POINT}')


def _find_new_disk():
    id=consts.glo_id()
    result_lsscsi = s.get_lsscsi(SSH, 's9mf7aYb', s.get_oprt_id())
    re_lio_disk = f'''\:{id}\].*LIO-ORG[ 0-9a-zA-Z._]*(/dev/sd[a-z]{{1,3}})'''
    disk_dev = s.re_search(re_lio_disk, result_lsscsi)
    if disk_dev:
        return disk_dev.group(1)


# -m:这里要注意replay的时候这边程序的调用过程.re-rescan之后又尽心过了一次_find_new_disk(),日志应该需要跳转到下一条lsscsi结果.注意指针及时移动
def get_disk_dev():
    # time.sleep(5)
    s.scsi_rescan(SSH, 'n')
    disk_dev = _find_new_disk()
    if disk_dev:
        s.pwl(f'Succeed in getting disk device "{disk_dev}" with id {consts.glo_id()}', 3, '', 'finish')
        return disk_dev
    else:
        scsi_id = consts.glo_id()
        s.pwl(f'No disk with SCSI ID {scsi_id} found, scan again...', 3, '', 'start')
        s.scsi_rescan(SSH, 'a')
        disk_dev = _find_new_disk()
        if disk_dev:
            s.pwl(f'Found the disk device "{disk_dev}" successfully', 4, '', 'finish')
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

    def get_all_log(self, folder):
        local_file = f'{folder}/{HOST}.tar'
        self.dbg.get_debug_log(local_file)


class HostTest(object):
    '''
    Format, write, and read iSCSI LUN
    '''

    def __init__(self):
        self.logger = consts.glo_log()
        self.rpl = consts.glo_rpl()
        self._prepare()
        self.iscsi=s.Iscsi(SSH,VPLX_IP)

            
    def _modify_host_iqn(self):
        initiator_iqn=consts.glo_iqn()
        cmd=f'echo "InitiatorName={initiator_iqn}" > /etc/iscsi/initiatorname.iscsi'
        oport_id=s.get_oprt_id()
        results=s.get_ssh_cmd(SSH,'RTDAJDas',cmd,oport_id)
        if results:
            if results['sts']:
                s.pwl(f'Success in modify initiator IQN "{initiator_iqn}"',2,'','finish')
                return True
            else:
                s.pwe(f'Failed to  modify initiator IQN "{initiator_iqn}"',2,2)
        else:
            s.handle_exception()
      
    def modify_iqn_and_restart(self):
        if self.iscsi.disconnect_iscsi_session(TARGET_IQN):
            if self._modify_host_iqn():
                self.iscsi.restart_iscsi()
    
    
    def _prepare(self):
        if self.rpl == 'no':
            init_ssh()
            umount_mnt()
            # self._create_iscsi_session()
        if self.rpl == 'yes':
            pass
            # s.find_session(VPLX_IP, SSH)

    def _mount(self, dev_name):
        '''
        Mount disk
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '6CJ5opVX'
        cmd = f'mount {dev_name} {MOUNT_POINT}'
        s.pwl(f'Start trying to mount "{dev_name}" to "{MOUNT_POINT}"', 2, oprt_id, 'start')
        result_mount = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_mount:
            if result_mount['sts']:
                s.pwl(f'Disk "{dev_name}" mounted to "{MOUNT_POINT}"', 3, oprt_id, 'finish')
                return True
            else:
                s.pwce(f'Failed to mount "{dev_name}" to "{MOUNT_POINT}"', 3, 2)
        else:
            s.handle_exception()

    def _judge_format(self, string):
        '''
        Determine the format status
        '''
        re_string = r'done'
        re_resulgt = s.re_findall(re_string, string)
        if len(re_resulgt) == 4:
            return True

    def format(self, dev_name):
        '''
        Format disk and mount disk
        '''
        cmd = f'mkfs.ext4 {dev_name} -F'
        oprt_id = s.get_oprt_id()

        s.pwl(f'Start to format "{dev_name}"', 2, oprt_id, 'start')

        result_format = s.get_ssh_cmd(SSH, '7afztNL6', cmd, oprt_id)
        if result_format:
            if result_format['sts']:
                result_format = result_format['rst'].decode('utf-8')
                if self._judge_format(result_format):
                    return True
                else:
                    s.pwe(f'Failed to format "{dev_name}"', 3, 2)
            else:
                s.pwce(f'Failed to execute command:"{cmd}"', 3, 2)
        else:
            s.handle_exception()

    def _get_dd_perf(self, cmd_dd, unique_str):
        '''
        Use regular to get the speed of test
        '''
        result_dd = s.get_ssh_cmd(SSH, unique_str, cmd_dd, s.get_oprt_id())
        result_dd = result_dd['rst'].decode('utf-8')
        re_performance = r'.*s, ([0-9.]* [A-Z]B/s)'
        re_result = s.re_findall(re_performance, result_dd)
        # 正则相关的暂时不做记录
        # self.logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {
        #                          re_performance: result_dd})
        if re_result:
            dd_perf = re_result[0]
            # self.logger.write_to_log(
            #     'F', 'DATA', 'regular', 'findall', oprt_id, dd_perf)
            return dd_perf
        else:
            s.pwce('Can not get test result', 3, 2)

    def get_test_perf(self):
        '''
        Calling method to read&write test
        '''
        s.pwl(f'Start speed test', 2, '', 'start')
        cmd_dd_write = f'dd if=/dev/zero of={MOUNT_POINT}/t.dat bs=512k count=16'
        cmd_dd_read = f'dd if={MOUNT_POINT}/t.dat of=/dev/zero bs=512k count=16'
        write_perf = self._get_dd_perf(cmd_dd_write, unique_str='CwS9LYk0')
        s.pwl(f'Write Speed: {write_perf}', 3, '', 'finish')
        time.sleep(0.25)
        read_perf = self._get_dd_perf(cmd_dd_read, unique_str='hsjG0miU')
        s.pwl(f'Read  Speed: {read_perf}', 3, '', 'finish')

    def start_test(self):
        # s.pwl('Start iscsi login',2,'','start')
        self.iscsi.create_iscsi_session()
        s.pwl(f'Start to get the disk device with id {consts.glo_id()}', 2)
        dev_name = get_disk_dev()
        if self.format(dev_name):
            if self._mount(dev_name):
                self.get_test_perf()
            else:
                s.pwce(f'Failed to mount device "{dev_name}"', 3, 2)
        else:
            s.pwce(f'Failed to format device "{dev_name}"', 3, 2)

    def host_rescan_r(self):
        '''
        vplx rescan after delete
        '''
        s.scsi_rescan(SSH, 'r')


if __name__ == "__main__":
    logger = log.Log(s.get_transaction_id())
    consts._init()
    consts.set_glo_log(logger)
    consts.set_glo_id('')
    consts.set_glo_id_list('')
    consts.set_glo_str('luntest')
    consts.set_glo_rpl('no')
    test = HostTest()
    # test.iscsi_logout()
    # consts._init()
    # consts.set_glo_tsc_id('789')
    # w = DebugLog()
    # w.collect_debug_sys()
    pass
  