#  coding: utf-8
import argparse
import sys
import time
import storage
import vplx
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
        netapp = storage.Storage(self.logger)
        netapp.lun_create()
        netapp.lun_map()

    def _vplx_drbd(self):
        '''
        Connect to VersaPLX, Config DRDB resource
        '''
        # drbd.discover_new_lun() # 查询新的lun有没有map过来，返回path
        drbd = vplx.VplxDrbd(self.logger)
        drbd.prepare_config_file()  # 创建配置文件
        drbd.drbd_cfg()  # run
        drbd.drbd_status_verify()  # 验证有没有启动（UptoDate）

    def _vplx_crm(self):
        '''
        Connect to VersaPLX, Config iSCSI Target
        '''
        crm = vplx.VplxCrm(self.logger)
        crm.crm_cfg()

    def _host_test(self):
        '''
        Connect to host
        Umount and start to format, write, and read iSCSI LUN
        '''
        host = host_initiator.HostTest(self.logger)
        # host.ssh.execute_command('umount /mnt')
        host.start_test()

    def delete_resource(self, uniq_str, list_id):
        '''
        User determines whether to delete and execute delete method
        '''
        storage.ID = list_id
        storage.STRING = uniq_str
        vplx.ID = list_id
        vplx.STRING = uniq_str

        crm = vplx.VplxCrm(self.logger)
        list_of_del_crm = crm.crm_show()

        drbd = vplx.VplxDrbd(self.logger)
        list_of_del_drbd = drbd.drbd_show()

        stor = storage.Storage(self.logger)
        list_of_del_stor = stor.lun_show()

        host_initiator.ID = id
        host = host_initiator.HostTest(self.logger)

        if list_of_del_crm or list_of_del_drbd or list_of_del_stor:
            comfirm = input('Do you want to delete these lun (yes/no):')
            if comfirm == 'yes':
                crm.start_crm_del(list_of_del_crm)
                drbd.start_drbd_del(list_of_del_drbd)
                stor.start_stor_del(list_of_del_stor)
                crm.vplx_rescan()
                host.initiator_rescan()
            else:
                sundry.pwe(self.logger, 'Cancel succeed')
        else:
            sundry.pwe(
                self.logger, 'The resource you want to delete does not exist. Please confirm the information you entered.\n')

    def execute(self, string, id):
        self.transaction_id = sundry.get_transaction_id()
        self.logger = log.Log(self.transaction_id)

        print(f'\n======*** Start working for ID {id} ***======')

        storage.ID = id
        storage.STRING = string
        self._storage()

        vplx.ID = id
        vplx.STRING = string
        self._vplx_drbd()
        self._vplx_crm()
        time.sleep(1.5)

        host_initiator.ID = id
        self._host_test()

    def replay(self, args):
        if args.transactionid or args.date:
            db = logdb.LogDB()
            db.get_logdb()

        if args.transactionid and args.date:
            print('1')
        elif args.transactionid:
            # result = logdb.get_info_via_tid(args.transactionid)
            # data = logdb.get_data_via_tid(args.transactionid)
            # for info in result:
            #     print(info[0])
            # print('============ * data * ==============')
            # for data_one in data:
            #     print(data_one[0])
            db.print_info_via_tid(args.transactionid)

            # logdb.replay_via_tid(args.transactionid)

        elif args.date:
            # python3 vtel_client_main.py re -d '2020/06/16 16:08:00' '2020/06/16 16:08:10'
            print('data')
        else:
            print('replay help')

    def get_ids(self, ids):
        ids = [int(i) for i in ids.split(',')]
        if len(ids) == 2:
            ids[1] += 1
        return ids

    def create_lun(self, uniq_str, ids):
        if len(ids) == 1:
            self.execute(uniq_str, int(ids[0]))
        elif len(ids) == 2:
            id_start, id_end = int(ids[0]), int(ids[1])
            for i in range(id_start, id_end):
                self.execute(uniq_str, i)
        else:
            self.parser.print_help()

    @sundry.record_exception
    def run(self):
        if sys.argv:
            path = sundry.get_path()
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log(
                'T', 'DATA', 'input', 'user_input', '', cmd)
            # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
            # [time],[transaction_id],[s],[DATA],[input],[user_input],[cmd],[f{cmd}]

        args = self.parser.parse_args()

        # uniq_str: The unique string for this test, affects related naming
        if args.uniq_str:
            ids = args.id_range
            if args.id_range:
                ids = self.get_ids(args.id_range)
            if args.delete:
                self.delete_resource(args.uniq_str, ids)
            else:
                self.create_lun(args.uniq_str, ids)
        else:
            self.parser.print_help()


if __name__ == '__main__':
    w = HydraArgParse()
    # w._host_rescan('1')
    # w._vplx_rescan('1','2')
    w.run()
