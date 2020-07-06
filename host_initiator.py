# coding:utf-8

import connect
import re
import sys
import time
import sundry as s

SSH = None
global ID

vplx_ip = '10.203.1.199'
host = '10.203.1.200'
port = '22'
user = 'root'
password = 'password'
timeout = 3

mount_point = '/mnt'

def init_ssh(logger):
    global SSH
    if not SSH:
        SSH = connect.ConnSSH(host, port, user, password, timeout, logger)
    else:
        pass

def umount_mnt(logger):
    print('  Umount "/mnt"')
    SSH.execute_command('umount /mnt')

def iscsi_login(logger):
    '''
    Discover iSCSI and login to session
    '''
    logger.write_to_log('T','INFO','info','start','',f'  Discover iSCSI and login to {vplx_ip}')
    cmd_iscsi_login = f'iscsiadm -m discovery -t st -p {vplx_ip} -l'
    result_iscsi_login = SSH.execute_command(cmd_iscsi_login)

    if result_iscsi_login['sts']:
        result_iscsi_login = result_iscsi_login['rst'].decode('utf-8')
        re_login = re.compile(
            f'Login to.*portal: ({vplx_ip}).*successful')
        re_result = re_login.findall(result_iscsi_login)
        # self.logger.write_to_log('DATA','output','re_result',re_result)
        oprt_id = s.get_oprt_id()
        logger.write_to_log('T','OPRT','regular','findall',oprt_id,{re_login:result_iscsi_login})
        logger.write_to_log('F','DATA','regular','findall',oprt_id,re_result)

        if re_result:
            print(f'  iSCSI login to {vplx_ip} successful')
            logger.write_to_log('T','INFO','info','finish','',f'  iSCSI login to {vplx_ip} successful')
            return True
        else:
            s.pwe(logger,f'  iSCSI login to {vplx_ip} failed')

def find_session(logger):
    '''
    Execute the command and check up the status of session
    '''
    # self.logger.write_to_log('INFO', 'info', '', 'start to execute the command and check up the status of session')
    logger.write_to_log('T','INFO','info','start','','    Execute the command and check up the status of session')
    cmd_session = 'iscsiadm -m session'
    result_session = SSH.execute_command(cmd_session)
    if result_session['sts']:
        result_session = result_session['rst'].decode('utf-8')
        re_session = re.compile(f'tcp:.*({vplx_ip}):.*')
        re_result = re_session.findall(result_session)
        oprt_id = s.get_oprt_id()
        logger.write_to_log('T','OPRT','regular','findall',oprt_id,{result_session:result_session})
        logger.write_to_log('F','DATA','regular','findall',oprt_id,re_result)
        # self.logger.write_to_log('DATA', 'output', 're_result', re_result)
        if re_result:
            # self.logger.write_to_log('HostTest','return','find_session',True)
            print('  iSCSI already login to VersaPLX')
            logger.write_to_log('T','INFO','info','finish','','    ISCSI already login to VersaPLX')
            return True
        else:
            print('  iSCSI not login to VersaPLX, Try to login')
            logger.write_to_log('T','INFO','warning','failed','','  ISCSI not login to VersaPLX, Try to login')


def discover_new_lun(logger):
    '''
    Scan and find the disk from NetApp
    '''
    # self.logger.write_to_log('INFO','info','',f'start to discover_new_lun for id {ID}')
    print('  Start to scan SCSI device from VersaPLX')
    logger.write_to_log('T','INFO','info','start','','    Start to scan SCSI device from VersaPLX')
    cmd_rescan = '/usr/bin/rescan-scsi-bus.sh'
    result_rescan = SSH.execute_command(cmd_rescan)
    if result_rescan['sts']:
        print('  Start to list all SCSI device')
        logger.write_to_log('T','INFO','info','start','','    Start to list all SCSI device')
        cmd_lsscsi = 'lsscsi'
        result_lsscsi = SSH.execute_command(cmd_lsscsi)
        if result_lsscsi['sts']:
            result_lsscsi = result_lsscsi['rst'].decode('utf-8')
        else:
            print(f'  Command {cmd_lsscsi} execute failed')
            logger.write_to_log('T','INFO','warning','failed','',f'  Command "{cmd_lsscsi}" execute failed')

    # if SSH.execute_command('/usr/bin/rescan-scsi-bus.sh'):#新的返回值有状态和数值,以状态判断,记录数值
    #     result_lsscsi = SSH.execute_command('lsscsi')
    else:
        print('  Scan SCSI device failed')
        logger('T','INFO','warning','failed','','  Scan SCSI device failed')
        # s.pwe(self.logger,f'Scan new LUN failed on NetApp')
    re_find_id_dev = r'\:(\d*)\].*LIO-ORG[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
    blk_dev_name = s.get_disk_dev(str(ID), re_find_id_dev, result_lsscsi, 'NetApp',logger)
    print(f'    Find new device {blk_dev_name} for LUN id {ID}')
    # self.logger.write_to_log('INFO', 'info', '', f'Find device {blk_dev_name} for LUN id {ID}')
    logger.write_to_log('T','INFO','warning','failed','',f'    Find new device {blk_dev_name} for LUN id {ID}')
    return blk_dev_name

class HostTest(object):
    '''
    Format, write, and read iSCSI LUN
    '''

    def __init__(self, logger):
        
        self.logger = logger
        # self.logger.host = host # 给logger对象的host属性附上这个模块的host
        print('Start IO test on initiator host')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', 'Start to Format and do some IO test on Host')
        init_ssh(self.logger)
        umount_mnt(self.logger)
        if not find_session(logger):
            iscsi_login(logger)
        # self.logger.write_to_log('INFO','info','','find_session end')

    def _judge_format(self, string):
        '''
        Determine the format status
        '''
        # self.logger.write_to_log('INFO','info','','start to determine the format status')
        re_done = re.compile(r'done')
        # self.logger.write_to_log('HostTest','regular_before','_judge_format',string)
        # self.logger.write_to_log('DATA','output','re_result',re_done.findall(string))
        if len(re_done.findall(string)) == 4:
            return True
        else:
            print('Format disk failed')
            sys.exit()
        # self.logger.write_to_log('INFO','info','','_judge_format end')

    def format_mount(self, dev_name):
        '''
        Format disk and mount disk
        '''
        # self.logger.write_to_log('INFO','info','',f'start to format disk {dev_name} and mount disk {dev_name}')
        print(f'  Start to format {dev_name}')
        self.logger.write_to_log('T','INFO','info','start','',f'    Start to format {dev_name}')
        cmd_format = f'mkfs.ext4 {dev_name} -F'
        result_format = SSH.execute_command(cmd_format)
        if result_format['sts']:
            result_format = result_format['rst'].decode('utf-8')
            if self._judge_format(result_format):
                print(f'  Try mount {dev_name} to "/mnt"')
                self.logger.write_to_log('T','INFO','info','start','',f'    Try mount {dev_name} to "/mnt"')
                cmd_mount = f'mount {dev_name} {mount_point}'
                result_mount = SSH.execute_command(cmd_mount)
                if result_mount['sts']:
                    print(f'  Disk {dev_name} mounted to "/mnt"')
                    self.logger.write_to_log('T','INFO','info','finish','',f'    Disk {dev_name} mounted to "/mnt"')
                    #self.logger.write_to_log('HostTest', 'return', 'format_mount', True)
                    return True
                else:
                    print(f'  Disk {dev_name} mount to "/mnt" failed')
                    s.pwe(self.logger,f"mount {dev_name} to {mount_point} failed")

            else:
                # print(f'  Format {dev_name} failed')
                s.pwe(self.logger,f'  Format {dev_name} failed')
        else:
            print(f'  Format command {cmd_format} execute failed')
            self.logger.write_to_log('T','INFO','warning','failed','',f'  Format command "{cmd_format}" execute failed')

    def _get_dd_perf(self, cmd_dd):
        '''
        Use regular to get the speed of test
        '''
        result_dd = SSH.execute_command(cmd_dd)
        result_dd = result_dd['rst'].decode('utf-8')
    # self.logger.write_to_log('INFO','info','','start to get the speed of test')
        re_performance = re.compile(r'.*s, ([0-9.]* [A-Z]B/s)')
        re_result = re_performance.findall(result_dd)
        oprt_id = s.get_oprt_id()
        self.logger.write_to_log('T','OPRT','regular','findall',oprt_id,{re_performance:result_dd})
    # self.logger.write_to_log('DATA', 'output', 're_result', re_result)
        if re_result:
            # self.logger.write_to_log('DATA', 'output', 'return', perf[0])
            dd_perf = re_result[0]
            self.logger.write_to_log('F','DATA','regular','findall',oprt_id,dd_perf)
            return dd_perf
        else:
            s.pwe(self.logger,'  Can not get test result')

    def get_test_perf(self):
        '''
        Calling method to read&write test
        '''
        print('  Start speed test ... ... ... ... ... ...')
        self.logger.write_to_log('T','INFO','info','start','','  Start speed test ... ... ... ... ... ...')
        cmd_dd_write = f'dd if=/dev/zero of={mount_point}/t.dat bs=512k count=16'
        cmd_dd_read = f'dd if={mount_point}/t.dat of=/dev/zero bs=512k count=16'
        # self.logger.write_to_log('INFO', 'info', '', 'start calling method to read&write test')
        write_perf = self._get_dd_perf(cmd_dd_write)
        print(f'    Write Speed: {write_perf}')
        self.logger.write_to_log('T','INFO','info','finish','',f'    Write Speed: {write_perf}')
        # self.logger.write_to_log('INFO', 'info', '', (f'write speed: {write_perf}'))
        time.sleep(0.25)
        read_perf = self._get_dd_perf(cmd_dd_read)
        print(f'    Read  Speed: {read_perf}')
        self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', f'    Read  Speed: {read_perf}')
        # self.logger.write_to_log('INFO', 'info', '', (f'read speed: {read_perf}'))

    def start_test(self):
        # self.logger.write_to_log('INFO', 'info', '', 'start to test')
        dev_name = discover_new_lun(self.logger)
        mount_status = self.format_mount(dev_name)
        if mount_status:
            self.get_test_perf()
        else:
            s.pwe(self.logger,f'Device {dev_name} mount failed')


if __name__ == "__main__":
    test = HostTest(21)
    command_result = '''[2:0:0:0]    cd/dvd  NECVMWar VMware SATA CD00 1.00  /dev/sr0
    [32:0:0:0]   disk    VMware   Virtual disk     2.0   /dev/sda 
    [33:0:0:15]  disk    LIO-ORG  res_lun_15       4.0   /dev/sdb 
    [33:0:0:21]  disk    LIO-ORG  res_luntest_21   4.0   /dev/sdc '''
    print(command_result)
