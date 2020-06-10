import conn
import time
import sys
import os
import re
class Vplx:
    def __init__(self):
        host='10.203.1.200'
        port=22
        username='root'
        password='password'
        timeout=10
        self.ssh=conn.SSHConn(host, port, username, password, timeout)
        self.ssh._connect()
        self.blk_dev_name=None

    def discover_new_lun(self,lun_id):
        self.ssh.exctCMD('rescan-scsi-bus.sh')
        time.sleep(1)   
        Str_out=self.ssh.exctCMD('lsscsi')

        re_vplx_id_path = re.compile(
        r'''\:(\d*)\].*NETAPP[ 0-9a-zA-Z.]*([/a-z]*)''') 
        stor_result = re_vplx_id_path.findall(Str_out)  #list

        result_tuple=stor_result[lun_id] #该lun_id-tuple
        assert_lun_id=result_tuple[0] #get lun_id
        try:
            assert lun_id == assert_lun_id
            self.blk_dev_name=result_tuple[1]
        except:
            sys.exit()

     
        
    #drdb--vi
    def prepare_config_file(self,res_name,drbd_device_name):
        context=r'''resource <{0}> {{
        on maxluntarget {{
        device /dev/<{1}>;
        disk /dev/<{2}>;
        address 10.203.1.199:7789;
        meta-disk internal;
        }} }}'''.format(res_name,drbd_device_name,self.blk_dev_name)
        GotoFolder('/etc/drbd.d')
        #print(os.getcwd())
        with open(f'{res_name}.res','a+',encoding='utf-8') as f:
            f.write(context)
    



def GotoFolder(strFolder):
    def _mkdir():
        if strFolder:
            if os.path.exists(strFolder):
                return True
            else:
                try:
                    os.makedirs(strFolder)
                    return True
                except Exception as E:
                    print('Create folder "{}" fail with error:\n\t"{}"'.format(
                        strFolder, E))

    if _mkdir():
        try:
            os.chdir(strFolder)
            return True
        except Exception as E:
            print('Change to folder "{}" fail with error:\n\t"{}"'.format(
                strFolder, E))
