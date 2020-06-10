import conn
class Storage:
    def __init__(self):
        host='10.203.1.231'
        Port=23
        username='root'
        password='Feixi@123'
        timeout=10
        self.telnet_conn=conn.TNConn(host, Port, username, password, timeout)
        self.telnet_conn._connect()
    def lun_create(self,lun_name):
        lc_cmd=r'lun create -s 10m -t linux /vol/esxi/%s'%lun_name
        self.telnet_conn.exctCMD(lc_cmd)

    def lun_map(self,lun_name,lun_id):
        lm_cmd=r'lun map /vol/esxi/%s'%lun_name+' hydra￼ %s'%lun_id
        self.telnet_conn.exctCMD(lm_cmd)

    def lun_create_verify(self):
        pass
    def lun_map_verify(self):
        pass
