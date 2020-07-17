# coding:utf-8

import connect
import re
import time
import sundry as s
import consts

SSH = None
# RPL = consts.get_rpl()

vplx_ip = '10.203.1.199'
host = '10.203.1.200'
port = '22'
user = 'root'
password = 'password'
timeout = 3
mount_point = '/mnt'


def init_ssh():
    global SSH
    if not SSH:
        SSH = connect.ConnSSH(host, port, user, password, timeout)
    else:
        pass


def umount_mnt():
    SSH.execute_command(f'umount {mount_point}')


def _find_new_disk():
    result_lsscsi = s.get_lsscsi(SSH, 's9mf7aYb', s.get_oprt_id())
    re_string = r'\:(\d*)\].*LIO-ORG[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
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
        s.scsi_rescan(SSH, 'a')
        disk_dev = _find_new_disk()
        if disk_dev:
            return disk_dev
        else:
            s.pwe('xxx:no new device')


class HostTest(object):
    '''
    Format, write, and read iSCSI LUN
    '''

    def __init__(self):
        
        self.logger = consts.glo_log()
        self.rpl = consts.glo_rpl()
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', '', 'Start to Format and do some IO test on Host')
        self._prepare()

    def _create_iscsi_session(self):
        self.logger.write_to_log(
            f'T', 'INFO', 'info', 'start', '', f'  Discover iSCSI session for {vplx_ip}')
        if not s.find_session(vplx_ip, SSH, 'V9jGOP2v', s.get_oprt_id()):
            self.logger.write_to_log(
                f'T', 'INFO', 'info', 'start', '', f'  Login to {vplx_ip}')
            if s.iscsi_login(vplx_ip, SSH, 'rgjfYl5K', s.get_oprt_id()):
                pass
            else:
                s.pwe(f'can not login to {vplx_ip}')

    def _prepare(self):
        if self.rpl == 'no':
            init_ssh()
            umount_mnt()
            # self._create_iscsi_session()
        if self.rpl == 'yes':
            s.find_session(vplx_ip, SSH, 'V9jGOP2v', s.get_oprt_id())

    def _mount(self, dev_name):
        '''
        Mount disk
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '6CJ5opVX'
        cmd = f'mount {dev_name} {mount_point}'
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', oprt_id, f'    Try mount {dev_name} to "/mnt"')
        result_mount = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_mount['sts']:
            print(f'    Disk {dev_name} mounted to "/mnt"')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'finish', oprt_id, f'    Disk {dev_name} mounted to "/mnt"')
            return True
        else:
            print(f'    Disk {dev_name} mount to "/mnt" failed')
            s.pwe(f"mount {dev_name} to {mount_point} failed")

    def _judge_format(self, string):
        '''
        Determine the format status
        '''
        re_string = r'done'
        re_resulgt = s.re_findall(re_string, string)
        if len(re_resulgt) == 4:
            return True
        else:
            s.pwe('format failed')

    def format(self, dev_name):
        '''
        Format disk and mount disk
        '''
        # self.logger.write_to_log('INFO','info','',f'start to format disk {dev_name} and mount disk {dev_name}')
        cmd = f'mkfs.ext4 {dev_name} -F'
        oprt_id = s.get_oprt_id()
        print(f'    Start to format {dev_name}')
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', oprt_id, f'    Start to format {dev_name}')
        result_format = s.get_ssh_cmd(SSH, '7afztNL6', cmd, oprt_id)
        if result_format['sts']:
            result_format = result_format['rst'].decode('utf-8')
            if self._judge_format(result_format):
                return True
            else:
                s.pwe(f'  Format {dev_name} failed')
        else:
            print(f'  Format command {cmd} execute failed')
            self.logger.write_to_log('T', 'INFO', 'warning', 'failed', '',
                                     f'  Format command "{cmd}" execute failed')

    def _get_dd_perf(self, cmd_dd, unique_str):
        '''
        Use regular to get the speed of test
        '''
        result_dd = s.get_ssh_cmd(SSH, unique_str, cmd_dd, s.get_oprt_id())
        result_dd = result_dd['rst'].decode('utf-8')
        re_performance = r'.*s, ([0-9.]* [A-Z]B/s)'
        re_result = s.re_findall(re_performance, result_dd)
        oprt_id = s.get_oprt_id()
        self.logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {
                                 re_performance: result_dd})
        if re_result:
            dd_perf = re_result[0]
            self.logger.write_to_log(
                'F', 'DATA', 'regular', 'findall', oprt_id, dd_perf)
            return dd_perf
        else:
            s.pwe('  Can not get test result')

    def get_test_perf(self):
        '''
        Calling method to read&write test
        '''
        print('  Start speed test ... ... ... ... ... ...')
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', '', '  Start speed test ... ... ... ... ... ...')
        cmd_dd_write = f'dd if=/dev/zero of={mount_point}/t.dat bs=512k count=16'
        cmd_dd_read = f'dd if={mount_point}/t.dat of=/dev/zero bs=512k count=16'
        # self.logger.write_to_log('INFO', 'info', '', 'start calling method to read&write test')
        write_perf = self._get_dd_perf(cmd_dd_write, unique_str='CwS9LYk0')
        print(f'    Write Speed: {write_perf}')
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'finish', '', f'    Write Speed: {write_perf}')
        # self.logger.write_to_log('INFO', 'info', '', (f'write speed: {write_perf}'))
        time.sleep(0.25)
        read_perf = self._get_dd_perf(cmd_dd_read, unique_str='hsjG0miU')
        print(f'    Read  Speed: {read_perf}')
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'finish', '', f'    Read  Speed: {read_perf}')
        # self.logger.write_to_log('INFO', 'info', '', (f'read speed: {read_perf}'))

    def start_test(self):
        print('Start IO test on initiator host')
        # self.logger.write_to_log('INFO', 'info', '', 'start to test')
        self._create_iscsi_session()
        dev_name = get_disk_dev()
        if self.format(dev_name):
            if self._mount(dev_name):
                self.get_test_perf()
            else:
                s.pwe(f'Device {dev_name} mount failed')
        else:
            s.pwe(f'Device {dev_name} format failed')

    def host_rescan_r(self):
        s.scsi_rescan(SSH, 'r')


if __name__ == "__main__":
    # test = HostTest(21)
    pass
    # command_result = '''[2:0:0:0]    cd/dvd  NECVMWar VMware SATA CD00 1.00  /dev/sr0
    # [32:0:0:0]   disk    VMware   Virtual disk     2.0   /dev/sda
    # [33:0:0:15]  disk    LIO-ORG  res_lun_15       4.0   /dev/sdb
    # [33:0:0:21]  disk    LIO-ORG  res_luntest_21   4.0   /dev/sdc '''
    # print(command_result)
