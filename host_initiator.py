# coding:utf-8

import connect
import re
import sys
import time
import sundry as s
import consts
import logdb

SSH = None
RPL = consts.get_rpl()

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
    # print('  Umount "/mnt"')
    SSH.execute_command(f'umount {mount_point}')



def iscsi_login(logger):
    '''
    Discover iSCSI login session, if no, login to vplx
    '''
    logger.write_to_log('T', 'INFO', 'info', 'start', '', f'  Discover iSCSI and login to {vplx_ip}')
    cmd = f'iscsiadm -m discovery -t st -p {vplx_ip} -l'
    result_iscsi_login = SSH.execute_command(cmd)

    if result_iscsi_login['sts']:
        result_iscsi_login = result_iscsi_login['rst'].decode('utf-8')
        re_login = re.compile(
            f'Login to.*portal: ({vplx_ip}).*successful')
        re_result = re_login.findall(result_iscsi_login)

        oprt_id = s.get_oprt_id()
        logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {re_login: result_iscsi_login})
        logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, re_result)

        if re_result:
            print(f'  iSCSI login to {vplx_ip} successful')
            logger.write_to_log('T', 'INFO', 'info', 'finish', '', f'  iSCSI login to {vplx_ip} successful')
            return True
        else:
            s.pwe(logger, f'  iSCSI login to {vplx_ip} failed')

def find_session(logger):
    '''
    Execute the command and check up the status of session
    '''
    # self.logger.write_to_log('INFO', 'info', '', 'start to execute the command and check up the status of session')
    unique_str = '4aXALx0R'
    oprt_id_cmd = s.get_oprt_id()
    oprt_id_re = s.get_oprt_id()
    cmd = 'iscsiadm -m session'

    logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id_cmd,
                        '    Execute the command and check up the status of session')
    result_session = get_ssh_cmd(logger, unique_str, cmd, oprt_id_one)
    # if result_session['sts']:
    #     result = result_session['rst'].decode('utf-8')
    # else:
    #     result = None
    #     print('execute drbd init command failed')

    if result_session['sts']:
        result_session = result_session['rst'].decode('utf-8')
        re_session = re.compile(f'tcp:.*({vplx_ip}):.*')
        re_result = re_session.findall(result_session['rst'].decode(utf-8))
        logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id_re, {result_session: result_session})
        logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id_re, re_result)
        # self.logger.write_to_log('DATA', 'output', 're_result', re_result)
        if re_result:
            # self.logger.write_to_log('HostTest','return','find_session',True)
            print('    iSCSI already login to VersaPLX')
            logger.write_to_log('T', 'INFO', 'info', 'finish', oprt_id_one, '    ISCSI already login to VersaPLX')
            return True
        else:
            print('  iSCSI not login to VersaPLX, Try to login')
            logger.write_to_log('T', 'INFO', 'warning', 'failed', oprt_id_one,
                                '  ISCSI not login to VersaPLX, Try to login')

def _scsi_rescan(logger, unique_str, oprt_id, cmd_rescan):
    print('    Start to scan SCSI device')
    logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id, '    Start to scan SCSI device')
    result_rescan = get_ssh_cmd(SSH, unique_str, cmd_rescan, oprt_id)
    if result_rescan['sts']:
        return True
    else:
        print('  Scan SCSI device failed')
        logger.write_to_log('T', 'INFO', 'warning', 'failed', oprt_id, '  Scan SCSI device failed')

def _list_disk():
    unique_str = 'JRQb18mg'
    oprt_id = s.get_oprt_id()

    print('    Start to list all SCSI device')
    logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id, '    Start to list all SCSI device')
    cmd_lsscsi = 'lsscsi'
    # result_lsscsi = SSH.execute_command(cmd_lsscsi)
    result_lsscsi = get_ssh_cmd(logger, unique_str, cmd_lsscsi, oprt_id)
    if result_lsscsi['sts']:
        return result_lsscsi['rst']
    else:
        print(f'  Command {cmd_lsscsi} execute failed')
        logger.write_to_log('T', 'INFO', 'warning', 'failed', oprt_id,
                            f'  Command "{cmd_lsscsi}" execute failed')

def _find_new_lun():
    re_find_id_dev = r'\:(\d*)\].*LIO-ORG[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
    str_lsscsi = _list_disk9()
    return s.get_disk_dev(consts.get_id(), re_find_id_dev, str_lsscsi, 'NetApp', logger)

def discover_new_lun():
    uni_str_resacan = 'JR2b1ejg'
    oprt_id_resacan = s.get_oprt_id()
    uni_str_resacan_retry = '3Riemejl'
    oprt_id_resacan_retry = s.get_oprt_id()
    cmd_rescan = '/usr/bin/rescan-scsi-bus.sh'
    cmd_rescan_retry = '/usr/bin/rescan-scsi-bus.sh -a'

    _scsi_rescan(uni_str_resacan, oprt_id_resacan, cmd_rescan)
    new_disk_dev = _find_new_lun()
    if new_disk_dev:
        print(f'    Find new device {blk_dev_name} for LUN id {consts.get_id()}')
    # self.logger.write_to_log('INFO', 'info', '', f'Find device {blk_dev_name} for LUN id {ID}')
        logger.write_to_log('T', 'INFO', 'warning', 'failed', '', f'    Find new device {blk_dev_name} for LUN id {consts.get_id()}')
        return new_disk_dev
    else:
        _scsi_rescan(uni_str_resacan_retry, oprt_id_resacan_retry, cmd_rescan_retry)
        new_disk_dev = _find_new_lun()
            if new_disk_dev:
                print(f'    Find new device {blk_dev_name} for LUN id {consts.get_id()}')
            # self.logger.write_to_log('INFO', 'info', '', f'Find device {blk_dev_name} for LUN id {ID}')
                logger.write_to_log('T', 'INFO', 'warning', 'failed', '', f'    Find new device {blk_dev_name} for LUN id {consts.get_id()}')
                return new_disk_dev
            else:
                s.pwe(xxx)


def start_rescan(logger):
    cmd_rescan = '/usr/bin/rescan-scsi-bus.sh'
    blk_dev_name = discover_new_lun(logger, cmd_rescan)
    # print(blk_dev_name)
    if blk_dev_name:
        return blk_dev_name
    else:
        print('Rescanning...')
        cmd_rescan = '/usr/bin/rescan-scsi-bus.sh -a'
        blk_dev_name = discover_new_lun(logger,cmd_rescan)
        if blk_dev_name:
            return blk_dev_name
        else:
            print('Did not find the new LUN from VersaPLX,exit the program...')
            sys.exit()

class HostTest(object):
    '''
    Format, write, and read iSCSI LUN
    '''
    def __init__(self, logger):

        self.logger = logger
        print('Start IO test on initiator host')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', 'Start to Format and do some IO test on Host')
        self._prepare()
        

    def _prepare(self):
        if _RPL == 'no':
            init_ssh(self.logger)
            umount_mnt(self.logger)
            if not find_session(logger):
                iscsi_login(logger)
        if _RPL == 'yes':
            find_session(self.logger)


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

    def mount(self, dev_name):
        '''
        Mount disk
        '''
        oprt_id = s.get_oprt_id()
        unique_str2 = '6CJ5opVX'
        cmd_mount = f'mount {dev_name} {mount_point}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id, f'    Try mount {dev_name} to "/mnt"')
        result_mount = get_ssh_cmd(self.logger, unique_str2, cmd_mount, oprt_id)
        if result_mount['sts']:
            print(f'    Disk {dev_name} mounted to "/mnt"')
            self.logger.write_to_log('T', 'INFO', 'info', 'finish', oprt_id, f'    Disk {dev_name} mounted to "/mnt"')
            return True
        else:
            print(f'    Disk {dev_name} mount to "/mnt" failed')
            s.pwe(self.logger, f"mount {dev_name} to {mount_point} failed")

    def format(self, dev_name):
        '''
        Format disk and mount disk
        '''
        # self.logger.write_to_log('INFO','info','',f'start to format disk {dev_name} and mount disk {dev_name}')
        oprt_id = s.get_oprt_id()
        unique_str = '7afztNL6'
        cmd_format = f'mkfs.ext4 {dev_name} -F'

        print(f'    Start to format {dev_name}')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id, f'    Start to format {dev_name}')
        result_format = get_ssh_cmd(self.logger, unique_str, cmd_format, oprt_id)
        if result_format['sts']:
            result_format = result_format['rst'].decode('utf-8')
            if self._judge_format(result_format):
                return True
            else:
                s.pwe(self.logger, f'  Format {dev_name} failed')
        else:
            print(f'  Format command {cmd_format} execute failed')
            self.logger.write_to_log('T', 'INFO', 'warning', 'failed', '',
                                     f'  Format command "{cmd_format}" execute failed')

    def _get_dd_perf(self, cmd_dd, unique_str):
        '''
        Use regular to get the speed of test
        '''
        oprt_id = s.get_oprt_id()
        result_dd = get_ssh_cmd(self.logger, unique_str, cmd_dd, oprt_id)
        result_dd = result_dd['rst'].decode('utf-8')
        re_performance = re.compile(r'.*s, ([0-9.]* [A-Z]B/s)')
        re_result = re_performance.findall(result_dd)
        oprt_id = s.get_oprt_id()
        self.logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {re_performance: result_dd})
        if re_result:
            dd_perf = re_result[0]
            self.logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, dd_perf)
            return dd_perf
        else:
            s.pwe(self.logger, '  Can not get test result')

    def get_test_perf(self):
        '''
        Calling method to read&write test
        '''
        print('  Start speed test ... ... ... ... ... ...')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', '  Start speed test ... ... ... ... ... ...')
        cmd_dd_write = f'dd if=/dev/zero of={mount_point}/t.dat bs=512k count=16'
        cmd_dd_read = f'dd if={mount_point}/t.dat of=/dev/zero bs=512k count=16'
        # self.logger.write_to_log('INFO', 'info', '', 'start calling method to read&write test')
        write_perf = self._get_dd_perf(cmd_dd_write, unique_str='CwS9LYk0')
        print(f'    Write Speed: {write_perf}')
        self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', f'    Write Speed: {write_perf}')
        # self.logger.write_to_log('INFO', 'info', '', (f'write speed: {write_perf}'))
        time.sleep(0.25)
        read_perf = self._get_dd_perf(cmd_dd_read, unique_str='hsjG0miU')
        print(f'    Read  Speed: {read_perf}')
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'finish', '', f'    Read  Speed: {read_perf}')
        # self.logger.write_to_log('INFO', 'info', '', (f'read speed: {read_perf}'))

    def start_test(self):
        # self.logger.write_to_log('INFO', 'info', '', 'start to test')
        dev_name = start_rescan(self.logger)
        mount_status = None
        if self.format(dev_name):
            mount_status = self.mount(dev_name)
        # mount_status = self.format_mount(dev_name)
        if mount_status:
            self.get_test_perf()
        else:
            s.pwe(self.logger, f'Device {dev_name} mount failed')

    def initiator_rescan(self):
        '''
        initiator rescan after delete
        '''
        rescan_cmd = 'rescan-scsi-bus.sh -r'
        SSH.execute_command(rescan_cmd)


if __name__ == "__main__":
    test = HostTest(21)

    # command_result = '''[2:0:0:0]    cd/dvd  NECVMWar VMware SATA CD00 1.00  /dev/sr0
    # [32:0:0:0]   disk    VMware   Virtual disk     2.0   /dev/sda
    # [33:0:0:15]  disk    LIO-ORG  res_lun_15       4.0   /dev/sdb
    # [33:0:0:21]  disk    LIO-ORG  res_luntest_21   4.0   /dev/sdc '''
    # print(command_result)
