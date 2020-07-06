
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
        # self.parser.add_argument(
        #     '-r',
        #     '--run',
        #     action="store_true",
        #     dest="run_test",
        #     help="run auto max lun test")
        self.parser.add_argument(
            '-s',
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming")
        self.parser.add_argument(
            '-id',
            action="store",
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
        drbd = vplx.VplxDrbd(self.logger)
        # drbd.discover_new_lun() # 查询新的lun有没有map过来，返回path
        drbd.prepare_config_file() # 创建配置文件
        drbd.drbd_cfg() # run
        drbd.drbd_status_verify() # 验证有没有启动（UptoDate）

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

    def execute(self, id, string):
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


    @sundry.record_exception
    def run(self):
        if sys.argv:
            path = sundry.get_path()
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log('T','DATA','input', 'user_input', '',cmd)
            # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
            # [time],[transaction_id],[s],[DATA],[input],[user_input],[cmd],[f{cmd}]

        args = self.parser.parse_args()

        # uniq_str: The unique string for this test, affects related naming
        if args.uniq_str:
            ids = args.id_range.split(',')
            if len(ids) == 1:
                self.execute(int(ids[0]), args.uniq_str)
            elif len(ids) == 2:
                id_start, id_end = int(ids[0]), int(ids[1])
                for i in range(id_start, id_end):
                    self.execute(i, args.uniq_str)
            else:
                self.parser.print_help()

        elif args.replay:
            self.replay(args)

        else:
            # self.logger.write_to_log('INFO','info','','print_help') 
            self.parser.print_help()


if __name__ == '__main__':
    w = HydraArgParse()
    w.run()
