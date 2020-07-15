
#  coding: utf-8
import argparse
import sys
import time

import storage
import vplx
import host_initiator
import sundry
import log
import replay

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
            help='The ID range of test, split with ","')

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

    def _storage(self, unique_id, unique_str):
        '''
        Connect to NetApp Storage
        Create LUN and Map to VersaPLX
        '''
        netapp = storage.Storage(unique_id, unique_str,self.logger)
        netapp.lun_create()
        netapp.lun_map()

    def _vplx_drbd(self, unique_id, unique_str):
        '''
        Connect to VersaPLX
        Go on DRDB resource configuration
        '''
        drbd = vplx.VplxDrbd(unique_id, unique_str,self.logger)
        drbd.discover_new_lun() # 查询新的lun有没有map过来，返回path
        drbd.prepare_config_file() # 创建配置文件
        drbd.drbd_cfg() # run
        drbd.drbd_status_verify() # 验证有没有启动（UptoDate）

    def _vplx_crm(self, unique_id, unique_str):
        '''
        Connect to VersaPLX
        Go on crm configuration
        '''
        crm = vplx.VplxCrm(unique_id, unique_str,self.logger)
        crm.crm_cfg()

    def _host_test(self, unique_id):
        '''
        Connect to host
        Umount and start to format, write, and read iSCSI LUN
        '''
        host = host_initiator.HostTest(unique_id,self.logger)
        host.ssh.excute_command('umount /mnt')
        host.start_test()

    def replay(self, args):
        logdb = replay.LogDB()
        logdb.produce_logdb()
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

            logdb.replay_via_tid(args.transactionid)


        elif args.date:
            # python3 vtel_client_main.py re -d '2020/06/16 16:08:00' '2020/06/16 16:08:10'
            print('data')
        else:
            print('replay help')


    # @sundry.record_exception
    def run(self):
        if sys.argv:
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log('DATA', 'input', 'user_input', '',cmd)

        args = self.parser.parse_args()

        '''
        uniq_str: The unique string for this test, affects related naming
        '''

        if args.uniq_str:
            if args.id_range:
                id_range = args.id_range.split(',')
                if len(id_range) == 2:
                    id_start, id_end = int(id_range[0]), int(id_range[1])
                else:
                    self.logger.write_to_log('INFO','warning','fail','','print_help')
                    self.parser.print_help()
                    sys.exit()
            else:
                self.logger.write_to_log('INFO','warning','fail','','print_help')
                self.parser.print_help()
                sys.exit()

            for i in range(id_start, id_end):
                # 新的logger对象（新的事务id）
                self.transaction_id = sundry.get_transaction_id()
                self.logger = log.Log(self.transaction_id)
                print(f'\n======*** Start working for ID {i} ***======')
                self._storage(i, args.uniq_str)
                self._vplx_drbd(i, args.uniq_str)
                self._vplx_crm(i, args.uniq_str)
                time.sleep(1.5)
                self._host_test(i)
        elif args.replay:
            self.replay(args)

        else:
            self.logger.write_to_log('INFO','warning','fail','','print_help')
            self.parser.print_help()




if __name__ == '__main__':
    w = HydraArgParse()
    w.run()
