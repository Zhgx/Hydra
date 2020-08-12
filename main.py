#  coding: utf-8

import consts
import argparse
import sys
import time
import vplx
import storage
import host_initiator
import sundry as s
import log
import logdb
import os
import subprocess
import debug_log


class HydraArgParse():
    '''
    Hydra project
    parse argument for auto max lun test program
    '''

    def __init__(self):
        consts._init()
        # -m:可能在某个地方我们要打印出来这个ID,哦,collect debug log时候就需要这个.但是这个id是什么时候更新的??理一下
        self.transaction_id = s.get_transaction_id()
        consts.set_glo_tsc_id(self.transaction_id)
        self.logger = log.Log(self.transaction_id)
        consts.set_glo_log(self.logger)
        self.argparse_init()
        self.list_tid = None  # for replay
        self.log_user_input()
        self.dict_id_str = {}
        self.del_print=False

       

    def log_user_input(self):
        if sys.argv:
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log(
                'T', 'DATA', 'input', 'user_input', '', cmd)

    def argparse_init(self):
        self.parser = argparse.ArgumentParser(prog='Hydra',
                                              description='Auto test max supported LUNs/Hosts/Replicas on VersaRAID-SDS')
        self.parser.add_argument(
            '-d',
            action="store_true",
            dest="delete",
            help="Confirm to delete LUNs")

        self.parser.add_argument(
            '-mh',
            action="store_true",
            dest="maxhost",
            help="Do the max supported host test with one LUN")
        
        self.parser.add_argument(
            '-mxh',
            action="store_true",
            dest="mxh",
            help="Do the max supported host test with N LUN")

        self.parser.add_argument(
            '-t',
            action="store_true",
            dest="test",
            help="just for test")

        self.parser.add_argument(
            '-s',
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming")

        self.parser.add_argument(
            '-c',
            action="store",
            dest="capacity",
            type=int,
            help="The capacity for determine the number of IQN every LUN")

        self.parser.add_argument(
            '-id',
            action="store",
            default='',
            dest="id_range",
            nargs= '+',
            help='ID or ID range')

        sub_parser = self.parser.add_subparsers(dest='replay')
        parser_replay = sub_parser.add_parser(
            'replay',
            aliases=['re'],
            formatter_class=argparse.RawTextHelpFormatter,
            help='Replay the Hydra program'

        )

        parser_replay.add_argument(
            '-t',
            '--transactionid',
            dest='tid',
            metavar='',
            help='The transaction id for replay')

        parser_replay.add_argument(
            '-d',
            '--date',
            dest='date',
            metavar='',
            nargs=2,
            help='The time period for replay')
        self.parser_replay = parser_replay

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
        s.generate_iqn('0')
        crm = vplx.VplxCrm()
        crm.crm_cfg()

    def _host_test(self):
        '''
        Connect to host
        Umount and start to format, write, and read iSCSI LUN
        '''
        host = host_initiator.HostTest()
        host.modify_iqn_and_restart()
        host.start_test()

    def create_max_host_resource(self):
        consts.set_glo_id_list([0])
        self.delete_resource()
        consts.set_glo_id(0)
        consts.set_glo_str('maxhost')
        self._storage()
        self._vplx_drbd()
    
    def run_maxhost(self):
        num=0
        self.create_max_host_resource()
        drbd=vplx.VplxDrbd()
        crm = vplx.VplxCrm()
        host=host_initiator.HostTest()
        while True:
            num+=1
            s.prt(f'The current number of max supported hosts test is {num}')
            s.generate_iqn(num)
            iqn_list=consts.glo_iqn_list()
            host.modify_iqn_and_restart()
            if len(iqn_list)==1:
                crm.crm_cfg()
            elif len(iqn_list)>1:
                drbd.drbd_status_verify()
                crm.modify_allow_initiator()
            self._host_test()   
            
    def generate_iqn_list(self):
        cap=consts.glo_cap()
        for iqn_id in range(cap):
            iqn_id+=1
            s.generate_iqn(iqn_id) 

    def iqn_to_host_test(self):
        iqn_list=consts.glo_iqn_list()
        host=host_initiator.HostTest()
        for iqn in iqn_list:
            consts.set_glo_iqn(iqn)
            host.modify_iqn_and_restart()
            host.start_test()

      
    def run_mxh(self):
        id_list=consts.glo_id_list()
        consts.set_glo_str('maxhost')
        for id in id_list:
            consts.set_glo_iqn_list([])
            consts.set_glo_id(id)
            self._storage()
            self._vplx_drbd()
            self.generate_iqn_list()
            crm=vplx.VplxCrm()
            if crm.crm_cfg():
                self.iqn_to_host_test()      
            

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
        if self.del_print:
            if crm_to_del_list:
                s.prt_res_to_del('\nCRM resource', crm_to_del_list)
            if drbd_to_del_list:
                s.prt_res_to_del('\nDRBD resource', drbd_to_del_list) 
            if lun_to_del_list:
                s.prt_res_to_del('\nStorage LUN', lun_to_del_list)

        if crm_to_del_list or drbd_to_del_list or lun_to_del_list:
            if self.del_print:
                answer = input('\n\nDo you want to delete these resource? (yes/y/no/n):')
                if answer == 'yes' or answer == 'y':
                    pass
                else:
                    self.del_print=False
            else:
                self.del_print=True
            
            if self.del_print:
                crm.del_all(crm_to_del_list)
                drbd.del_all(drbd_to_del_list)
                stor.del_all(lun_to_del_list)
                s.pwl('Start to remove all deleted disk device on vplx and host',0)
                # remove all deleted disk device on vplx and host
                crm.vplx_rescan_r()
                host.host_rescan_r()
                print(f'{"":-^80}','\n')
            else:
                s.pwe('User canceled deleting proccess ...', 2, 2)
        else:
            if self.del_print:
                print()
                s.pwe('No qualified resources to be delete.', 2, 2)
            else:
                return True

    @s.record_exception
    def run(self, dict_args):
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
                print(f'{"":-^{format_width}}','\n')
                time.sleep(1.5)
            except consts.ReplayExit:
                print(f'{"":-^{format_width}}', '\n')
                continue

    def get_valid_transaction(self,list_transaciont):
        db = consts.glo_db()
        lst_tid = list_transaciont[:]
        for tid in lst_tid:
            string, id = db.get_string_id(tid)
            if string and id:
                self.dict_id_str.update({id: string})
            else:
                self.list_tid.remove(tid)
                cmd = db.get_cmd_via_tid(tid)
                print(f'事务:{tid} 不满足replay条件，所执行的命令为：{cmd}')
        print(f'Transaction to be executed: {" ".join(self.list_tid)}')
        return self.dict_id_str


    def prepare_replay(self, args):
        db = consts.glo_db()
        arg_tid = args.tid
        arg_date = args.date
        print('* MODE : REPLAY *')
        time.sleep(1.5)
        if arg_tid:
            string, id = db.get_string_id(arg_tid)
            if not all([string, id]):
                cmd = db.get_cmd_via_tid(arg_tid)
                print(
                    f'事务:{arg_tid} 不满足replay条件，所执行的命令为：{cmd}')
                return
            consts.set_glo_tsc_id(arg_tid)
            self.dict_id_str.update({id: string})
            print(f'Transaction to be executed: {arg_tid}')
            # self.replay_run(args.transactionid)
        elif arg_date:
            self.list_tid = db.get_transaction_id_via_date(
                arg_date[0], arg_date[1])
            self.get_valid_transaction(self.list_tid)
        elif arg_tid and arg_date:
            print('Please specify only one type of data for replay')
        else:
            # 执行日志全部的事务
            self.list_tid = db.get_all_transaction()
            self.get_valid_transaction(self.list_tid)



    def start(self):
        args = self.parser.parse_args()

        # uniq_str: The unique string for this test, affects related naming
        if args.test:
            debug_log.collect_debug_log()
            return
        if args.id_range:
            id_list = s.change_id_str_to_list(args.id_range)
            consts.set_glo_id_list(id_list)

        if args.uniq_str:
            consts.set_glo_str(args.uniq_str)

        if args.capacity:
            consts.set_glo_cap(args.capacity)

        if args.delete:
            self.del_print=True
            self.delete_resource()
            return

        elif args.maxhost:
            # consts.set_glo_id(args.id_range[0])
            self.run_maxhost()
            return

        elif args.mxh:
            if args.id_range and args.capacity:
                self.run_mxh()
            return

        elif args.replay:
            consts.set_glo_rpl('yes')
            consts.set_glo_log_switch('no')
            logdb.prepare_db()
            self.prepare_replay(args)

        elif args.uniq_str and args.id_range:
            id_list = consts.glo_id_list()
            for id_ in id_list:
                self.dict_id_str.update({id_: args.uniq_str})

        else:
            self.parser.print_help()
            return

        self.run(self.dict_id_str)


if __name__ == '__main__':
    obj = HydraArgParse()
    obj.start()

