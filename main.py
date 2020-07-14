#  coding: utf-8
import argparse
import sys
import time
import vplx
import storage
import host_initiator
import sundry
import log
import logdb
import consts



class HydraArgParse():
    '''
    Hydra project
    parse argument for auto max lun test program
    '''

    def __init__(self):
        self.transaction_id = sundry.get_transaction_id()
        self.logger = log.Log(self.transaction_id)
        self.argparse_init()
        consts._init()  # 初始化一个全局变量：ID
        self.list_tid = None

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
        print('------* storage end *------')

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
        print('------* drbd end *------')

    def _host_test(self):
        '''
        Connect to host
        Umount and start to format, write, and read iSCSI LUN
        '''
        host = host_initiator.HostTest(self.logger)
        # host.ssh.execute_command('umount /mnt')
        host.start_test()
        print('------* host_test end *------')

    def delete_resource(self):
        '''
        User determines whether to delete and execute delete method
        '''
        # _ID = consts.get_id
        # _STR = consts.get_str

        crm = vplx.VplxCrm(self.logger)
        list_of_del_crm = crm.crm_show()


        drbd = vplx.VplxDrbd(self.logger)
        list_of_del_drbd = drbd.drbd_show()

        stor = storage.Storage(self.logger)
        list_of_del_stor = stor.lun_show()
        # print(list_of_del_stor)
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


    def replay_execute(self, tid):
        db = logdb.LogDB()
        db.get_logdb()
        _string, _id = db.get_string_id(tid)
        vplx._RPL = 'yes'
        storage._RPL = 'yes'
        host_initiator._RPL = 'yes'
        vplx._TID = tid
        storage._TID = tid
        host_initiator._TID = tid
        consts._init()  # 初始化一个全局变量：ID
        consts.set_value('LOG_SWITCH', 'OFF')
        self.execute(_id, _string)

    def execute(self, dict_args):
        for id_one,str_one in dict_args.items():
            consts.set_value('id_one',id_one)
            consts.set_value('str_one',str_one)
            self.transaction_id = sundry.get_transaction_id()
            self.logger = log.Log(self.transaction_id)
            self.logger.write_to_log('F', 'DATA', 'STR', 'Start a new trasaction', '', f'{consts.get_id()}')
            self.logger.write_to_log('F', 'DATA', 'STR', 'unique_str', '', f'{consts.get_str()}')
            if self.list_tid:
                for tid in self.list_tid:
                    consts.set_value('tid',tid)
                    self._storage()
                    self._vplx_drbd()
                    self._vplx_crm()
                    self._host_test()
                return

            self._storage()
            self._vplx_drbd()
            self._vplx_crm()
            self._host_test()


        # print(f'\n======*** Start working for ID {id} ***======')
        # self._storage()
        #
        #
        # # 初始化一个全局变量ID
        # storage._ID = id
        # storage._STR = string
        # self._storage()
        #
        # vplx._ID = id
        # vplx._STR = string
        # self._vplx_drbd()
        # self._vplx_crm()
        #
        # host_initiator._ID = id
        # self._host_test()

    # @sundry.record_exception

    def run(self):
        if sys.argv:
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log('T', 'DATA', 'input', 'user_input', '', cmd)

        args = self.parser.parse_args()
        dict_id_str = {}
        # uniq_str: The unique string for this test, affects related naming

        # if args.uniq_str and args.id_range:
        #     consts.set_value('RPL', 'no')
        #     consts.set_value('LOG_SWITCH', 'ON')
        #     ids = args.id_range.split(',')
        #     if len(ids) == 1:
        #         dict_id_str.update({ids[0]:args.uniq_str})
                
        #     elif len(ids) == 2:
        #         id_start, id_end = int(ids[0]), int(ids[1])
        #         for i in range(id_start, id_end):
        #             dict_id_str.update({i: args.uniq_str})     
        #     else:
        #         self.parser.print_help()
        if args.uniq_str:
            if args.delete:
                consts.set_value('RPL', 'no')
                if args.id_range:
                    ids = [int(i) for i in args.id_range.split(',')]
                else:
                    ids=''
                consts.set_value('str_one', args.uniq_str)
                consts.set_value('id_one',ids)
                self.delete_resource()  
  

        elif args.replay:
            consts.set_value('RPL','yes')
            consts.set_value('LOG_SWITCH','OFF')
            db = logdb.LogDB()
            db.get_logdb()
            if args.transactionid:
                string, id = db.get_string_id(args.transactionid)
                consts.set_value('tid', args.transactionid)
                print(consts.get_tid())
                dict_id_str.update({id: string})
 
                # self.replay_execute(args.transactionid)
            elif args.date:
                self.list_tid = db.get_transaction_id_via_date(args.date[0], args.date[1])
                for tid in self.list_tid:
                    string, id = db.get_string_id(tid)
                    dict_id_str.update({id:string})

            else:
                print('replay help')


        else:
            # self.logger.write_to_log('INFO','info','','print_help')
            self.parser.print_help()
        self.execute(dict_id_str)


if __name__ == '__main__':
    w = HydraArgParse()
    # w._host_rescan('1')
    # w._vplx_rescan('1','2')
    w.run()
