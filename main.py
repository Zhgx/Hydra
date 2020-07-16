#  coding: utf-8

import consts
import argparse
import sys
import time
import vplx
import storage
import host_initiator
import sundry
import log
import logdb


class HydraArgParse():
    '''
    Hydra project
    parse argument for auto max lun test program
    '''

    def __init__(self):
        consts._init()
        self.logger = self.init_log()
        consts.set_glo_log(self.logger)
        self.argparse_init()
        self.list_tid = None # for replay
        self.log_user_input()
        self.dict_id_str = {}

    def init_log(self):
        return log.Log(sundry.get_transaction_id())

    def log_user_input(self):
        if sys.argv:
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log(
                'T', 'DATA', 'input', 'user_input', '', cmd)

    def argparse_init(self):
        self.parser = argparse.ArgumentParser(prog='max_lun',
                                              description='Test max lun number of VersaRAID-SDS')
        self.parser.add_argument(
            '-d',
            action="store_true",
            dest="delete",
            help="to confirm delete lun")
        self.parser.add_argument(
            '-s',
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming")
        self.parser.add_argument(
            '-id',
            action="store",
            default='',
            dest="id_range",
            help='ID or ID range(split with ",")')

        sub_parser = self.parser.add_subparsers(dest='replay')
        parser_replay = sub_parser.add_parser(
            'replay',
            aliases=['re'],
            formatter_class=argparse.RawTextHelpFormatter
        )

        parser_replay.add_argument(
            '-t',
            '--transactionid',
            dest='transactionid',
            metavar='',
            help='transaction id')

        parser_replay.add_argument(
            '-d',
            '--date',
            dest='date',
            metavar='',
            nargs=2,
            help='date')

    def _storage(self):
        '''
        Connect to NetApp Storage, Create LUN and Map to VersaPLX
        '''
        netapp = storage.Storage()
        netapp.lun_create()
        netapp.lun_map()
        print('------* storage end *------')

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
        print('------* drbd end *------')

    def _host_test(self):
        '''
        Connect to host
        Umount and start to format, write, and read iSCSI LUN
        '''
        host = host_initiator.HostTest()
        # host.ssh.execute_command('umount /mnt')
        host.start_test()
        print('------* host_test end *------')

    def delete_resource(self):
        '''
        User determines whether to delete and execute delete method
        '''

        crm = vplx.VplxCrm()
        list_of_del_crm = crm.crm_show()

        drbd = vplx.VplxDrbd()
        list_of_del_drbd = drbd.drbd_show()

        stor = storage.Storage()
        list_of_del_stor = stor.lun_show()

        host = host_initiator.HostTest()

        if list_of_del_crm or list_of_del_drbd or list_of_del_stor:
            comfirm = input('Do you want to delete these lun (yes/no):')
            if comfirm == 'yes':
                crm.start_crm_del(list_of_del_crm)
                drbd.start_drbd_del(list_of_del_drbd)
                stor.start_stor_del(list_of_del_stor)
                crm.vplx_rescan()
                host.host_rescan()
            else:
                sundry.pwe('Cancel succeed')
        else:
            sundry.pwe(
                'The resource you want to delete does not exist. Please confirm the information you entered.\n')

    def run(self, dict_args):
        rpl = consts.glo_rpl()
        for id_, str_ in dict_args.items():
            consts.set_glo_id(id_)
            consts.set_glo_str(str_)
            if rpl == 'no':
                self.logger = log.Log(sundry.get_transaction_id())
                self.logger.write_to_log(
                    'F', 'DATA', 'STR', 'Start a new trasaction', '', f'{consts.glo_id()}')
                self.logger.write_to_log(
                    'F', 'DATA', 'STR', 'unique_str', '', f'{consts.glo_str()}')
            if self.list_tid:
                tid = self.list_tid[0]
                self.list_tid.remove(tid)
                consts.set_glo_tsc_id(tid)
            self._storage()
            self._vplx_drbd()
            self._vplx_crm()
            self._host_test()

    # @sundry.record_exception
    def prepare_replay(arg_tid, arg_data):
        db = consts.glo_db()
        if arg_tid:
            string, id = db.get_string_id(arg_tid)
            if not all([string, id]):
                cmd = db.get_cmd_via_tid(arg_tid)
                print(
                    f'事务:{arg_tid} 不满足replay条件，所执行的命令为：python3 {cmd}')
                return
            consts.set_glo_tsc_id(arg_tid)
            self.dict_id_str.update({id: string})

            # self.replay_run(args.transactionid)
        elif arg_data:
            self.list_tid = db.get_transaction_id_via_date(
                arg_data[0], arg_data[1])
            for tid in self.list_tid:
                string, id = db.get_string_id(tid)
                if string and id:
                    self.dict_id_str.update({id: string})
                else:
                    cmd = db.get_cmd_via_tid(tid)
                    print(f'事务:{tid} 不满足replay条件，所执行的命令为：python3 {cmd}')
        else:
            print('replay help')
            return

    def start(self):
        args = self.parser.parse_args()
        
        # uniq_str: The unique string for this test, affects related naming
        if args.id_range:
            id_list = change_id_str_to_list(args.id_range)
            consts.set_glo_id_list(id_list)

        if args.uniq_str:
            consts.set_glo_str(args.uniq_str)

        if args.delete:
            self.delete_resource()
            return

        elif args.replay:
            consts.set_glo_rpl('yes')
            consts.set_glo_log_switch('no')
            logdb.prepare_db()
            self.prepare_replay()
            
        elif args.uniq_str and args.id_range:
            uniq_str = consts.glo_str()
            id_list = consts.glo_id_list()
            for id_ in id_list:
                self.dict_id_str.update({id_: args.uniq_str})

        else:
            # self.logger.write_to_log('INFO','info','','print_help')
            self.parser.print_help()
            return

        self.run(self.dict_id_str)


if __name__ == '__main__':
    obj = HydraArgParse()
    obj.start()
