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

    def exctCMD(self, command):       
        stdin,stdout, stderr = self.SSHConnection.exec_command(command)
        data = stdout.read()
        if len(data) > 0:
            print(data.strip())   #打印正确结果
            return data
        err = stderr.read()
        if len(err) > 0:
            print(err.strip())     #输出错误结果
            return err
          
    def close(self):
        self.SSHConnection.close()

class TNConn(object):
    def __init__(self, strIP, intPort,strName, strPWD, intTO):
        self._host = strIP
        self._port = intPort
        self._username=strName
        self._password = strPWD
        self._timeout = intTO
        self.TN=telnetlib.Telnet()

    def _connect(self):
       #连接设备，try-except结构
        try:
            self.TN.open(self._host,self._port)
        except:
            print('%sconnect fail' %self._host)
            return False
        #'输入用户名'
        self.TN.read_until(b'Username:', timeout=1)
        self.TN.write(b'\n')
        self.TN.write(self._username.encode() + b'\n')

        #'输入用户密码'
        self.TN.read_until(b'Password:', timeout=1)
        self.TN.write(self._password.encode() + b'\n')

        rely = self.TN.read_very_eager().decode()
        if 'Login invalid' not in rely:
            print('%slogin success' % self._host)
            return True
        else:
            print('%slogin fail' % self._host)
            return False

    #定义exctCMD函数,用于执行命令
    def exctCMD(self,cmd):       
        self.TN.write(cmd.encode().strip() + b'\n')
        time.sleep(2)
        rely = self.TN.read_very_eager().decode()
        print('exctCMD:\n %s' %rely)
    #定义close函数，关闭程序
    def close(self):
        self.TN.close()
if __name__ == '__main__':  
    pass
#ssh
    # host='10.203.1.200'
    # port='22'
    # username='root'
    # password='password'
    # timeout=10
    # ssh=SSHConn(host, port, username, password, timeout)
    # ssh._connect()
    # ssh.exctCMD('df')
    # ssh.close()
#telnet
    # strIP='10.203.1.231'
    # intPort='23'
    # strName='root'
    # strPWD='Feixi@123'
    # intTO='10'
    # testTN=TNConn(strIP, intPort,strName, strPWD, intTO)
    # testTN._connect()
    # testTN.exctCMD('lun show')
    # testTN.close()
   
    
