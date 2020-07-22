# coding:utf-8

import connect
import re
import time
import sundry as s
import consts

SSH = None
# RPL = consts.get_rpl()

#-m:全局变量应该大写吧?
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
    re_lio_disk = r'\:(\d*)\].*LIO-ORG[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
    all_disk = s.re_findall(re_lio_disk, result_lsscsi)
    disk_dev = s.get_the_disk_with_lun_id(all_disk)
    if disk_dev:
        return disk_dev
    else:
        s.pwe()

#    scan
#      meizhaodao, scan again
#    scan
#      zhaodaole 

#-m:这里要注意replay的时候这边程序的调用过程.re-rescan之后又尽心过了一次_find_new_disk(),日志应该需要跳转到下一条lsscsi结果.注意指针及时移动
def get_disk_dev():
    s.scsi_rescan(SSH, 'n')
    disk_dev = _find_new_disk()
    if disk_dev:
        return disk_dev
    else:
        scsi_id = consts.glo_id()
        #-m:需要增加显示level,和警告level
        s.pwl('No disk with SCSI ID {scsi_id} found, scan again...',2)
        s.scsi_rescan(SSH, 'a')
        disk_dev = _find_new_disk()
        if disk_dev:
            #-m:
            s.pwl('找到了',2)
            return disk_dev
        else:
            #-m:真的就要退出了,这里.
            s.pwe('xxx:no new device')

class DebugLog(object):
    def __init__(self):
        init_ssh()
        self.tid = consts.glo_tsc_id()
        self.debug_folder = f'/var/log/{self.tid}_{host}'
        self.dbg = s.DebugLog(SSH, self.debug_folder)
    
    def collect_debug_sys(self):
        cmd_debug_sys = consts.get_cmd_debug_sys(self.debug_folder, host)
        self.dbg.prepare_debug_log(cmd_debug_sys)

    def get_all_log(self, folder):
        local_file = f'{folder}/{host}.tar'
        self.dbg.get_debug_log(local_file)
    

class HostTest(object):
    '''
    Format, write, and read iSCSI LUN
    '''

    def __init__(self):
        
        self.logger = consts.glo_log()
        self.rpl = consts.glo_rpl()
        # self.logger.write_to_log(
        #     'T', 'INFO', 'info', 'start', '', 'Start to Format and do some IO test on Host')
        self._prepare()

    def _create_iscsi_session(self):
        #-m:这里应该有一个较高级别的说明现在在干啥.至于哪里需要这个函数的string,哪里不需要,我也晕了,需要确认一下
        self.logger.write_to_log(
            f'T', 'INFO', 'info', 'start', '', f'  Discover iSCSI session for {vplx_ip}')
        if not s.find_session(vplx_ip, SSH, 'V9jGOP2v', s.get_oprt_id()):
            #-m:这里大概也要说明一下现在的情况,not log in,然后再start log in
            # self.logger.write_to_log(
            #     f'T', 'INFO', 'info', 'start', '', f'Login to {vplx_ip}')
            if s.iscsi_login(vplx_ip, SSH, 'rgjfYl5K', s.get_oprt_id()):
                #-m:要打印一下连上了.
                s.pwl('ISSCsi   loged in success')
                pass
            else:
                s.pwe(f'can not login to {vplx_ip}')
        else:
            s.pwl('ISSCsi  Already  loged in',1)

    def _prepare(self):
        if self.rpl == 'no':
            init_ssh()
            umount_mnt()
            # self._create_iscsi_session()
        if self.rpl == 'yes':
            #-m:理清楚 rpl时候有没有调用ssh连接
            s.find_session(vplx_ip, SSH, 'V9jGOP2v', s.get_oprt_id())

    def _mount(self, dev_name):
        '''
        Mount disk
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '6CJ5opVX'
        cmd = f'mount {dev_name} {mount_point}'
        #-m:
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'start', oprt_id, f'Try mount {dev_name} to "/mnt"')
        result_mount = s.get_ssh_cmd(SSH, unique_str, cmd, oprt_id)
        if result_mount['sts']:
            #-m:这个不是start,绝对不是,不能乱...finish
            s.pwl(f'Disk {dev_name} mounted to "/mnt',1,oprt_id,'start')
            # print(f'    Disk {dev_name} mounted to "/mnt"')
            # self.logger.write_to_log(
            #     'T', 'INFO', 'info', 'finish', oprt_id, f'    Disk {dev_name} mounted to "/mnt"')
            return True
        else:
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
        cmd = f'mkfs.ext4 {dev_name} -F'
        oprt_id = s.get_oprt_id()

        s.pwl(f'Start to format {dev_name}',1,oprt_id,'start')

        result_format = s.get_ssh_cmd(SSH, '7afztNL6', cmd, oprt_id)
        if result_format['sts']:
            result_format = result_format['rst'].decode('utf-8')
            if self._judge_format(result_format):
                return True
            else:

                s.pwe(f'Format {dev_name} failed')
        else:
            s.pwl(f'Format command {cmd} execute failed', 1, oprt_id, 'finish')

                #-m:s.pwe 同样需要level,显示level,警告level应该是一样的
            s.pwe(f'Format {dev_name} failed')

            #-m:如果失败,则退出


            # print(f'  Format command {cmd} execute failed')
            # self.logger.write_to_log('T', 'INFO', 'warning', 'failed', '',
            #                          f'  Format command "{cmd}" execute failed')

    def _get_dd_perf(self, cmd_dd, unique_str):
        '''
        Use regular to get the speed of test
        '''
        result_dd = s.get_ssh_cmd(SSH, unique_str, cmd_dd, s.get_oprt_id())
        result_dd = result_dd['rst'].decode('utf-8')
        re_performance = r'.*s, ([0-9.]* [A-Z]B/s)'
        re_result = s.re_findall(re_performance, result_dd)
        oprt_id = s.get_oprt_id()
        #-m:删除findll 的 oprt id
        self.logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {
                                 re_performance: result_dd})
        if re_result:
            dd_perf = re_result[0]
            self.logger.write_to_log(
                'F', 'DATA', 'regular', 'findall', oprt_id, dd_perf)
            return dd_perf
        else:
            s.pwe('Can not get test result')

    def get_test_perf(self):
        '''
        Calling method to read&write test
        '''
        s.pwl(f'Start speed test',1,'','start')
        # self.logger.write_to_log(
        #     'T', 'INFO', 'info', 'start', '', 'Start speed test ... ...')
        cmd_dd_write = f'dd if=/dev/zero of={mount_point}/t.dat bs=512k count=16'
        cmd_dd_read = f'dd if={mount_point}/t.dat of=/dev/zero bs=512k count=16'
        # self.logger.write_to_log('INFO', 'info', '', 'start calling method to read&write test')
        write_perf = self._get_dd_perf(cmd_dd_write, unique_str='CwS9LYk0')
        s.pwl(f'Write Speed: {write_perf}',2,'','finish')
        # print(f'    Write Speed: {write_perf}')
        # self.logger.write_to_log(
        #     'T', 'INFO', 'info', 'finish', '', f'    Write Speed: {write_perf}')
        time.sleep(0.25)
        read_perf = self._get_dd_perf(cmd_dd_read, unique_str='hsjG0miU')
        s.pwl(f'Read  Speed: {read_perf}',2,'','finish')
        # print(f'    Read  Speed: {read_perf}')
        # self.logger.write_to_log(
        #     'T', 'INFO', 'info', 'finish', '', f'    Read  Speed: {read_perf}')

    def start_test(self):
        # self.logger.write_to_log('INFO', 'info', '', 'start to test')
        s.pwl('start iscsi login',2)
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
        '''
        vplx rescan after delete
        '''
        s.scsi_rescan(SSH, 'r')


if __name__ == "__main__":
    # test = HostTest(21)
    consts._init()
    consts.set_glo_tsc_id('789')
    w = DebugLog()
    w.collect_debug_sys()
    pass
    # command_result = '''[2:0:0:0]    cd/dvd  NECVMWar VMware SATA CD00 1.00  /dev/sr0
    # [32:0:0:0]   disk    VMware   Virtual disk     2.0   /dev/sda
    # [33:0:0:15]  disk    LIO-ORG  res_lun_15       4.0   /dev/sdb
    # [33:0:0:21]  disk    LIO-ORG  res_luntest_21   4.0   /dev/sdc '''
    # print(command_result)
