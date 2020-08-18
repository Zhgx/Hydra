#coding:utf-8

import consts
import time
import vplx
import storage
import host_initiator
import sundry as s
import log
import random


class HydraControl(object):
    def __init__(self):
        self.dict_id_str = {}
        self.capacity = None
        self.random_num=3

    def _storage(self):
        '''
        Connect to NetApp Storage, Create LUN and Map to VersaPLX
        '''
        netapp = storage.Storage()
        netapp.lun_create()
        netapp.lun_map()

    def _vplx_drbd(self):
        '''
        Connect to VersaPLX, Config DRDB resource
        '''
        # drbd.discover_new_lun() # 查询新的lun有没有map过来，返回path
        drbd = vplx.VplxDrbd()
        drbd.prepare_config_file()  # 创建配置文件
        drbd.drbd_cfg()  # run
        drbd.drbd_status_verify()  # 验证有没有启动（UptoDate）

    def _vplx_crm(self):
        '''
        Connect to VersaPLX, Config iSCSI Target
        '''
        crm = vplx.VplxCrm()
        crm.crm_cfg()
        crm.crm_status_verify()

    def _host_test(self):
        '''
        Connect to host
        Umount and start to format, write, and read iSCSI LUN
        '''
        host = host_initiator.HostTest()
        iqn = consts.glo_iqn_list()[-1]
        host.iscsi_connect(iqn)
        host.start_test()

    def _host_modify_iqn_and_test(self):
        iqn_list = consts.glo_iqn_list()
        host = host_initiator.HostTest()
        iqn_random_list=sorted(random.sample(iqn_list,self.random_num))
        for iqn in iqn_random_list:
            host.iscsi_connect(iqn)
            host.start_test()

    def delete_resource(self):
        '''
        User determines whether to delete and execute delete method
        '''
        crm = vplx.VplxCrm()
        drbd = vplx.VplxDrbd()
        stor = storage.Storage()
        host = host_initiator.HostTest()

        crm_to_del_list = s.get_to_del_list(crm.get_all_cfgd_res())
        drbd_to_del_list = s.get_to_del_list(drbd.get_all_cfgd_drbd())
        lun_to_del_list = s.get_to_del_list(stor.get_all_cfgd_lun())

        if crm_to_del_list:
            s.prt_res_to_del('\nCRM resource', crm_to_del_list)
        if drbd_to_del_list:
            s.prt_res_to_del('\nDRBD resource', drbd_to_del_list)
        if lun_to_del_list:
            s.prt_res_to_del('\nStorage LUN', lun_to_del_list)

        if crm_to_del_list or drbd_to_del_list or lun_to_del_list:
            answer = input('\n\nDo you want to delete these resource? (yes/y/no/n):')
            if answer == 'yes' or answer == 'y':
                crm.del_all(crm_to_del_list)
                drbd.del_all(drbd_to_del_list)
                stor.del_all(lun_to_del_list)
                s.pwl('Start to remove all deleted disk device on vplx and host', 0)
                # remove all deleted disk device on vplx and host
                crm.vplx_rescan_r()
                host.host_rescan_r()
                print(f'{"":-^80}', '\n')
            else:
                s.pwe('User canceled deleting proccess ...', 2, 2)
        else:
            print()
            s.pwe('No qualified resources to be delete.', 2, 2)

    def run_mxh(self):
        id_list = consts.glo_id_list()
        consts.set_glo_str('maxhost')
        for id in id_list:
            consts.set_glo_iqn_list([])
            consts.set_glo_id(id)
            s.generate_iqn_list(self.capacity)
            self._storage()
            self._vplx_drbd()
            self._vplx_crm()
            self._host_modify_iqn_and_test()

    @s.record_exception
    def run_maxlun(self, dict_args):
        iqn = s.generate_iqn('0')
        consts.append_glo_iqn_list(iqn)
        rpl = consts.glo_rpl()
        format_width = 105 if rpl == 'yes' else 80
        for id_, str_ in dict_args.items():
            consts.set_glo_id(id_)
            consts.set_glo_str(str_)
            print(f'**** Start working for ID {consts.glo_id()} ****'.center(format_width, '='))
            if rpl == 'no':
                self.transaction_id = s.get_transaction_id()
                self.logger = log.Log(self.transaction_id)
                consts.set_glo_log(self.logger)
                consts.set_glo_tsc_id(self.transaction_id)
                self.logger.write_to_log(
                    'F', 'DATA', 'STR', 'Start a new trasaction', '', f'{consts.glo_id()}')
                self.logger.write_to_log(
                    'F', 'DATA', 'STR', 'unique_str', '', f'{consts.glo_str()}')
            if self.list_tid:
                tid = self.list_tid[0]
                self.list_tid.remove(tid)
                consts.set_glo_tsc_id(tid)
            try:
                s.pwl('Start to configure LUN on NetApp Storage', 0, s.get_oprt_id(), 'start')
                self._storage()
                time.sleep(1.5)
                s.pwl('Start to configure DRDB resource and CRM resource on VersaPLX', 0, s.get_oprt_id(), 'start')
                self._vplx_drbd()
                self._vplx_crm()
                time.sleep(1.5)
                s.pwl('Start to format，write and read the LUN on Host', 0, s.get_oprt_id(), 'start')
                self._host_test()
                print(f'{"":-^{format_width}}', '\n')
                time.sleep(1.5)
            except consts.ReplayExit:
                print(f'{"":-^{format_width}}', '\n')
                continue

    def run_maxhost(self):
        num = 0
        consts.set_glo_str('maxhost')
        self._storage()
        self._vplx_drbd()
        drbd = vplx.VplxDrbd()
        crm = vplx.VplxCrm()
        while True:
            s.prt(f'The current number of max supported hosts test is {num+1}')
            iqn = s.generate_iqn(num)
            num += 1
            consts.append_glo_iqn_list(iqn)
            iqn_list = consts.glo_iqn_list()
            if len(iqn_list) == 1:
                crm.crm_cfg()
                crm.crm_status_verify()
            elif len(iqn_list) > 1:
                drbd.drbd_status_verify()
                crm.modify_allow_initiator()
                crm.crm_and_targetcli_verify()
            self._host_test()

