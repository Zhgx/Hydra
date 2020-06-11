#  coding: utf-8
import paramiko
import time
import telnetlib
class SSHConn(object):
    def __init__(self, host, port, username, password, timeout):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None

    def _connect(self):
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            time.sleep(1)
            print('success')
            objSSHClient.exec_command("\x003")
            self.SSHConnection = objSSHClient
        except:
            pass

    def exctCMD(self, command): #是否需要判断连接
        stdin, stdout, stderr = self.SSHConnection.exec_command(command)
        data = stdout.read()
        if len(data) > 0:
            print(data.strip())
            return data
        err = stderr.read()
        if len(err) > 0:
            print(err.strip())
            return err

    def close(self):
        self.SSHConnection.close()


class TNConn(object):
    def __init__(self, host, Port, username, password, timeout):
        self._host = host
        self._port = Port
        self._username = username
        self._password = password
        self._timeout = timeout
        self.TN = telnetlib.Telnet()

    def _connect(self):
        try:
            self.TN.open(self._host, self._port)
        except:
            print('%sconnect fail' % self._host)
            return False

        self.TN.read_until(b'Username:', timeout=1)
        self.TN.write(b'\n')
        self.TN.write(self._username.encode() + b'\n')

        self.TN.read_until(b'Password:', timeout=1)
        self.TN.write(self._password.encode() + b'\n')

        rely = self.TN.read_very_eager().decode()
        if 'Login invalid' not in rely:
            print('%slogin success' % self._host)
            return True
        else:
            print('%slogin fail' % self._host)
            return False

    # 定义exctCMD函数,用于执行命令
    def exctCMD(self, cmd):
        self.TN.write(cmd.encode().strip() + b'\n')
        time.sleep(2)
        rely = self.TN.read_very_eager().decode()
        print('exctCMD:\n %s' % rely)

    def close(self):
        self.TN.close()


if __name__ == '__main__':
    pass
    # host='10.203.1.200'
    # port='22'
    # username='root'
    # password='password'
    # timeout=10
    # ssh=SSHConn(host, port, username, password, timeout)
    # ssh._connect()
    # strout=ssh.exctCMD('df')
    # print(re.findall('1024',strout))
    # ssh.close()
# telnet
    # host='10.203.1.231'
    # Port='23'
    # username='root'
    # password='Feixi@123'
    # timeout=10
    # testTN=TNConn(host, Port,username, password, timeout)
    # testTN._connect()
    # testTN.exctCMD('lun show')
    # testTN.close()
