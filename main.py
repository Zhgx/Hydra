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
        self.transaction_id = sundry.get_transaction_id()
        self.logger = log.Log(self.transaction_id)
        self.argparse_init()
        # 初始化一个全局变量：ID
        self.list_tid = None
        consts._init()
        consts.set_glo_log(self.logger)
        self.logger = consts.glo_log()

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

    def execute(self, dict_args):
        for id_one, str_one in dict_args.items():
            consts.set_glo_id(id_one)
            consts.set_glo_str(str_one)
            self.transaction_id = sundry.get_transaction_id()
            self.logger = log.Log(self.transaction_id)
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

    def run(self):
        if sys.argv:
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log(
                'T', 'DATA', 'input', 'user_input', '', cmd)

        args = self.parser.parse_args()
        dict_id_str = {}
        # uniq_str: The unique string for this test, affects related naming
        ids = args.id_range
        if args.id_range:
            ids = [int(i) for i in args.id_range.split(',')]

        if args.delete and args.unique_str:
            consts.set_glo_rpl('no')
            consts.set_glo_str(args.uniq_str)
            consts.set_glo_id_list(ids)
            self.delete_resource()

        elif args.uniq_str and args.id_range:
            consts.set_glo_rpl('no')
            consts.set_glo_log_switch('yes')
            if len(ids) == 1:
                dict_id_str.update({ids[0]: args.uniq_str})

            elif len(ids) == 2:
                id_start, id_end = int(ids[0]), int(ids[1])
                for i in range(id_start, id_end):
                    dict_id_str.update({i: args.uniq_str})
            else:
                self.parser.print_help()

        elif args.replay:
            consts.set_glo_rpl('yes')
            consts.set_glo_log_switch('no')
            logdb.prepare_db()
            db = consts.glo_db()
            if args.transactionid:
                string, id = db.get_string_id(args.transactionid)
                if not all([string, id]):
                    cmd = db.get_cmd_via_tid(args.transactionid)
                    print(
                        f'事务:{args.transactionid} 不满足replay条件，所执行的命令为：python3 {cmd}')
                    return
                consts.set_glo_tsc_id(args.transactionid)
                dict_id_str.update({id: string})

                # self.replay_execute(args.transactionid)
            elif args.date:
                self.list_tid = db.get_transaction_id_via_date(
                    args.date[0], args.date[1])
                for tid in self.list_tid:
                    string, id = db.get_string_id(tid)
                    if string and id:
                        dict_id_str.update({id: string})
                    else:
                        cmd = db.get_cmd_via_tid(tid)
                        print(f'事务:{tid} 不满足replay条件，所执行的命令为：python3 {cmd}')
            else:
                print('replay help')
                return

        else:
            # self.logger.write_to_log('INFO','info','','print_help')
            self.parser.print_help()
            return

        self.execute(dict_id_str)


if __name__ == '__main__':
    w = HydraArgParse()
    # w._host_rescan('1')
    # w._vplx_rescan('1','2')
    w.run()
