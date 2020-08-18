#  coding: utf-8

import consts
import argparse
import sys
import time
import sundry as s
import log
import logdb
import debug_log
import control


class HydraArgParse(control.HydraControl):
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
        super(HydraArgParse, self).__init__()

    def log_user_input(self):
        if sys.argv:
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log(
                'T', 'DATA', 'input', 'user_input', '', cmd)

    def get_valid_transaction(self, list_transaciont):
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

    def argparse_init(self):
        self.parser = argparse.ArgumentParser(prog='Hydra',
                                              description='Auto test max supported LUNs/Hosts/Replicas on VersaRAID-SDS')
        # self.parser.add_argument(
        #     '-t',
        #     action="store_true",
        #     dest="test",
        #     help="just for test"
        # )
        sub_parser = self.parser.add_subparsers(dest='subcommand')
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
            help='The transaction id for replay'
        )
        parser_replay.add_argument(
            '-d',
            '--date',
            dest='date',
            metavar='',
            nargs=2,
            help='The time period for replay'
        )
        self.parser_replay = parser_replay
        parser_maxlun = sub_parser.add_parser(
            'maxlun',
            aliases=['mxl'],
            help='Do the max supported LUNs test'
        )
        parser_maxlun.add_argument(
            '-id',
            required=True,
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        parser_maxlun.add_argument(
            '-s',
            required=True,
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming"
        )
        #max host test with one lun
        parser_maxhost_lun = sub_parser.add_parser(
            'mh',
            help = 'Do the max supported Hosts test with one LUN'
        )
        #max host test with number luns
        parser_maxhost_luns = sub_parser.add_parser(
            'mxh',
            #aliases=['mxh'],
            help='Do the max supported Hosts test with N LUNs'
        )
        parser_maxhost_luns.add_argument(
            '-id',
            required=True,
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        parser_maxhost_luns.add_argument(
            '-c',
            required=True,
            action="store",
            dest="capacity",
            type=int,
            help="The capacity of each Lun, which represents the number of hosts that can be mapped"
        )
        parser_maxhost_luns.add_argument(
            '-n',
            action="store",
            type=int,
            dest="random_number",
            help='The number of hosts which is select for test'
        )
        #delete resource
        parser_delete_re = sub_parser.add_parser(
            'delete',
            aliases=['del'],
            help='Confirm to delete LUNs'
        )
        parser_delete_re.add_argument(
            '-id',
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        parser_delete_re.add_argument(
            '-s',
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming"
        )
        # parser_maxlun.set_defaults(func=self.run_maxlun)
        # parser_maxhost_lun.set_defaults(func=self.run_maxhost)
        # parser_maxhost_luns.set_defaults(func=self.run_mxh)
        # parser_delete_re.set_defaults(func=self.delete_resource())

    def start(self):
        args = self.parser.parse_args()
        print('args:',args)
        try:
            if args.id_range:
                id_list = s.change_id_str_to_list(args.id_range)
                consts.set_glo_id_list(id_list)
        except:
            pass
        try:
            if args.uniq_str:
                consts.set_glo_str(args.uniq_str)
        except:
            pass
        try:
            if args.capacity:
                self.capacity = args.capacity
        except:
            pass
        try:
            self.random_num=args.random_number
        except:
            pass
        if args.subcommand in ['mxl','maxlun']:
            id_list = consts.glo_id_list()
            for id_ in id_list:
                self.dict_id_str.update({id_: args.uniq_str})
            self.run_maxlun(self.dict_id_str)
        elif args.subcommand == 'mh':
            self.run_maxhost()
        elif args.subcommand == 'mxh':
            self.run_mxh()
        elif args.subcommand in ['del', 'delete']:
            self.delete_resource()
        elif args.subcommand == 're':
            consts.set_glo_rpl('yes')
            consts.set_glo_log_switch('no')
            logdb.prepare_db()
            self.prepare_replay(args)
        else:
            self.parser.print_help()
        # args.func(args)

        # if args.test:
        #     debug_log.collect_debug_log()
        #     return


if __name__ == '__main__':
    obj = HydraArgParse()
    obj.start()

