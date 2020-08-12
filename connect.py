#  coding: utf-8
import paramiko
import time
import telnetlib
import sundry as s
import traceback
import consts


class ConnSSH(object):
    '''
    ssh connect to VersaPLX
    '''

    def __init__(self, host, port, username, password, timeout):
        self.logger = consts.glo_log()
        self.logger.d1 = host
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self._sftp = None
        self.SSHConnection = None
        self.ssh_connect()

    def _connect(self):
        oprt_id = s.get_oprt_id()
        s.pwl(f'Start to connect {self._host} via SSH', 2, oprt_id, 'start')
        self.logger.write_to_log('F', 'DATA', 'value', 'dict', 'data for SSH connect',
                                 {'host': self._host, 'port': self._port, 'username': self._username,
                                  'password': self._password})
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            self.SSHConnection = objSSHClient
        except Exception as e:
            self.logger.write_to_log(
                'F', 'DATA', 'debug', 'exception', 'ssh connect', str(traceback.format_exc()))
            s.pwe(f'Connect to {self._host} failed with error: {e}', 2, 2)


    def execute_command(self, command):
        stdin, stdout, stderr = self.SSHConnection.exec_command(command)
        data = stdout.read()
        if len(data) > 0:
            output = {'sts': 1, 'rst': data}
            return output
        err = stderr.read()
        if len(err) > 0:
            output = {'sts': 0, 'rst': err}
            return output
        if data == b'':
            output = {'sts': 1, 'rst': data}
            return output

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            s.pwl(f'Retry to connect {self._host} via SSH',2,'','start')
            self.logger.write_to_log(
                'T', 'INFO', 'info', 'start', '', '  Retry connect to VersaPLX via SSH')
            self._connect()

    def download(self, remotepath, localpath):
        def _download():
            if self._sftp is None:
                self._sftp = self.SSHConnection.open_sftp()
            self._sftp.get(remotepath, localpath)

        try:
            _download()
        except AttributeError as e:
            print(f'Download file "{remotepath}" failed with error: {e}')

    def upload(self, localpath, remotepath):
        def _upload():
            if self._sftp is None:
                self._sftp = self.SSHConnection.open_sftp()
            self._sftp.put(localpath, remotepath)

        try:
            _upload()
        except AttributeError as e:
            print(f'Upload file "{remotepath}" failed with error: {e}')

    def close(self):
        self.SSHConnection.close()
        self.logger.write_to_log(
            'T', 'INFO', 'info', 'finish', '', 'Close SSH connection')


class ConnTelnet(object):
    '''
    telnet connect to NetApp
    '''

    def __init__(self, host, port, username, password, timeout):
        self.logger = consts.glo_log()
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout
        self.telnet = telnetlib.Telnet()
        self.telnet_connect()

    def _connect(self):
        try:
            oprt_id = s.get_oprt_id()

            s.pwl('Start to connect NetApp via Telnet', 2, oprt_id, 'start')
            # -m:DATA,Telnet,connect,dict
            self.logger.write_to_log('F', 'DATA', 'value', 'dict', 'data for telnet connect',
                                     {'host': self._host, 'port': self._port, 'username': self._username,
                                      'password': self._password})
            self.telnet.open(self._host, self._port)
            self.telnet.read_until(b'Username:', timeout=1)
            self.telnet.write(self._username.encode() + b'\n')
            self.telnet.read_until(b'Password:', timeout=1)
            self.telnet.write(self._password.encode() + b'\n')

        except Exception as e:
            self.logger.write_to_log(
                'F', 'DATA', 'debug', 'exception', 'telnet connect', str(traceback.format_exc()))

            s.pwe(f'Connect to {self._host} failed with error: {e}', 2, 2)


    # 定义exctCMD函数,用于执行命令
    def execute_command(self, cmd):
        self.telnet.read_until(b'fas270>').decode()
        self.telnet.write(cmd.encode().strip() + b'\r')
        time.sleep(0.1)
        rely = self.telnet.read_until(b'fas270>').decode()
        self.telnet.write(b'\r')
        return rely

    def telnet_connect(self):
        self._connect()
        if not self.telnet:
            s.pwl('Retry to connect {self._host} via Telnet',2,'','start')
            self._connect()

    def close(self):
        self.telnet.close()
        self.logger.write_to_log(
            'INFO', 'info', '', 'Close Telnet connection.')


if __name__ == '__main__':
    # telnet
    # host = '10.203.1.231'
    # port = '22'
    # username = 'root'
    # password = 'Feixi@123'
    # timeout = 5
    # ssh = ConnSSH(host, port, username, password, timeout)
    # strout = ssh.execute_command('?')
    # w = strout.decode('utf-8')
    # print(type(w))
    # print(w.split('\n'))
    # pprint.pprint(w)
    # time.sleep(2)
    # strout = ssh.execute_command('lun show -m')
    # pprint.pprint(strout)

    pass
