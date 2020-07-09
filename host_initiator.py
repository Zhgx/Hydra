# coding:utf-8

import connect
import re
import sys
import time
import sundry as s
import consts
import logdb

SSH = None
global _ID
global _RPL
global _TID

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

def host_ex_ssh_cmd(logger,unique_str,cmd,oprt_id):
    if _RPL == 'no':
        logger.write_to_log('F', 'DATA', 'STR', unique_str, '', oprt_id)
        logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd)
        result_cmd = SSH.execute_command(cmd)
        logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_cmd)
    elif _RPL == 'yes':
        pass




def iscsi_login(logger):
    '''
    Discover iSCSI and login to session
    '''
    logger.write_to_log('T','INFO','info','start','',f'  Discover iSCSI and login to {vplx_ip}')
    cmd = f'iscsiadm -m discovery -t st -p {vplx_ip} -l'
    result_iscsi_login = SSH.execute_command(cmd)

    if result_iscsi_login['sts']:
        result_iscsi_login = result_iscsi_login['rst'].decode('utf-8')
        re_login = re.compile(
            f'Login to.*portal: ({vplx_ip}).*successful')
        re_result = re_login.findall(result_iscsi_login)

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
    unique_str = 'zWuZsV8e'
    oprt_id_one = s.get_oprt_id()
    oprt_id_two = s.get_oprt_id()
    print('  Start to scan SCSI device from VersaPLX')
    logger.write_to_log('T','INFO','info','start','','    Start to scan SCSI device from VersaPLX')
    cmd_rescan = '/usr/bin/rescan-scsi-bus.sh'
    result_rescan = ex_ssh_cmd(logger,unique_str,cmd_rescan,oprt_id_one)
    # result_rescan = SSH.execute_command(cmd_rescan)
    # if result_rescan['sts']:
    if result_rescan:
        print('  Start to list all SCSI device')
        logger.write_to_log('T','INFO','info','start','','    Start to list all SCSI device')
        cmd_lsscsi = 'lsscsi'
        # result_lsscsi = SSH.execute_command(cmd_lsscsi)
        result_lsscsi = ex_ssh_cmd(logger,unique_str,cmd_rescan,oprt_id_two)
        # if result_lsscsi != None:
        #     pass
            # result_lsscsi = result_lsscsi['rst'].decode('utf-8')
        if result_lsscsi is None:
            print(f'  Command {cmd_lsscsi} execute failed')
            logger.write_to_log('T','INFO','warning','failed','',f'  Command "{cmd_lsscsi}" execute failed')

    # if SSH.execute_command('/usr/bin/rescan-scsi-bus.sh'):#新的返回值有状态和数值,以状态判断,记录数值
    #     result_lsscsi = SSH.execute_command('lsscsi')
    else:
        print('  Scan SCSI device failed')
        logger('T','INFO','warning','failed','','  Scan SCSI device failed')
        # s.pwe(self.logger,f'Scan new LUN failed on NetApp')
    re_find_id_dev = r'\:(\d*)\].*LIO-ORG[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
    blk_dev_name = s.get_disk_dev(str(_ID), re_find_id_dev, result_lsscsi, 'NetApp',logger)
    print(f'    Find new device {blk_dev_name} for LUN id {_ID}')
    # self.logger.write_to_log('INFO', 'info', '', f'Find device {blk_dev_name} for LUN id {ID}')
    logger.write_to_log('T','INFO','warning','failed','',f'    Find new device {blk_dev_name} for LUN id {_ID}')
    return blk_dev_name


def ex_ssh_cmd(logger,unique_str,cmd,oprt_id):
    now_id = consts.get_value('ID')
    print(f'DB ID now is : {now_id}')
    if _RPL == 'no':
        logger.write_to_log('F', 'DATA', 'STR', unique_str, '', oprt_id)
        logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd)
        result_cmd = SSH.execute_command(cmd)
        print(cmd)
        print(result_cmd)
        logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_cmd)
        if result_cmd['sts']:
            return result_cmd['rst'].decode('utf-8')
        else:
            print('execute drbd init command failed')
    elif _RPL == 'yes':
        db = logdb.LogDB()
        db.get_logdb()
        ww = db.find_oprt_id_via_string(_TID, unique_str)
        db_id, oprt_id = ww
        print(f'  DB ID go to: {db_id}')
        print(f'  get opration ID: {oprt_id}')
        result_cmd = db.get_cmd_result(oprt_id)
        if result_cmd:
            result_cmd = eval(result_cmd[0])
            if result_cmd['sts']:
                result = result_cmd['rst'].decode('utf-8')
            else:
                result = None
                print('execute drbd init command failed')
        s.change_pointer(db_id)
        print(f'  Change DB ID to: {db_id}')
        return result

class HostTest(object):
    '''
    Format, write, and read iSCSI LUN
    '''

    def __init__(self, logger):
        
        self.logger = logger
        print('Start IO test on initiator host')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', 'Start to Format and do some IO test on Host')
        if _RPL == 'no':
            init_ssh(self.logger)
            umount_mnt(self.logger)
            if not find_session(logger):
                iscsi_login(logger)

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

        oprt_id = s.get_oprt_id()
        unique_str1 = '7afztNL6'
        unique_str2 = '6CJ5opVX'
        cmd_format = f'mkfs.ext4 {dev_name} -F'
        cmd_mount = f'mount {dev_name} {mount_point}'


        print(f'  Start to format {dev_name}')
        self.logger.write_to_log('T','INFO','info','start',oprt_id,f'    Start to format {dev_name}')
        result_format = ex_ssh_cmd(self.logger,unique_str1,cmd_format,oprt_id)
        if result_format:
            if self._judge_format(result_format):
                print(f'  Try mount {dev_name} to "/mnt"')
                self.logger.write_to_log('T','INFO','info','start','',f'    Try mount {dev_name} to "/mnt"')
                result_mount = ex_ssh_cmd(self.logger,unique_str2,cmd_mount,oprt_id) # 这里返回的值是result['rst']
                if result_mount:
                    print(f'  Disk {dev_name} mounted to "/mnt"')
                    self.logger.write_to_log('T','INFO','info','finish','',f'    Disk {dev_name} mounted to "/mnt"')
                    #self.logger.write_to_log('HostTest', 'return', 'format_mount', True)
                    return True
                else:
                    print(f'  Disk {dev_name} mount to "/mnt" failed')
                    s.pwe(self.logger,f"mount {dev_name} to {mount_point} failed")
            else:
                s.pwe(self.logger,f'  Format {dev_name} failed')
        else:
            print(f'  Format command {cmd_format} execute failed')
            self.logger.write_to_log('T','INFO','warning','failed','',f'  Format command "{cmd_format}" execute failed')

    def _get_dd_perf(self, cmd_dd):
        '''
        Use regular to get the speed of test
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'CwS9LYk0'
        result_dd = ex_ssh_cmd(self.logger,unique_str,cmd_dd,oprt_id)
        re_performance = re.compile(r'.*s, ([0-9.]* [A-Z]B/s)')
        re_result = re_performance.findall(result_dd)
        oprt_id = s.get_oprt_id()
        self.logger.write_to_log('T','OPRT','regular','findall',oprt_id,{re_performance:result_dd})
        if re_result:
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
