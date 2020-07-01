#  coding: utf-8
import storage
import vplx
import host_initiator
import argparse
import sys
import time


class HydraArgParse():
    '''
    Hydra project
    parse argument for auto max lun test program
    '''

    def __init__(self):
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
            dest="id_range",
            help='The ID range of test, split with ","')

    def _storage(self, unique_id, unique_str):
        '''
        Connect to NetApp Storage
        Create LUN and Map to VersaPLX
        '''
        netapp = storage.Storage(unique_id, unique_str)
        netapp.lun_create()
        netapp.lun_map()

    def _vplx_drbd(self, unique_id, unique_str):
        '''
        Connect to VersaPLX
        Go on DRDB resource configuration
        '''
        drbd = vplx.VplxDrbd(unique_id, unique_str)
        drbd.start_discover()
        drbd.prepare_config_file()
        drbd.drbd_cfg()
        drbd.drbd_status_verify()

    def _vplx_crm(self, unique_id, unique_str):
        '''
        Connect to VersaPLX
        Go on crm configuration
        '''
        crm = vplx.VplxCrm(unique_id, unique_str)
        crm.crm_cfg()

    def _host_test(self, unique_id):
        '''
        Connect to host
        Umount and start to format, write, and read iSCSI LUN
        '''
        host = host_initiator.HostTest(unique_id)
        host.ssh.excute_command('umount /mnt')
        host.start_test()

    def _stor_del(self, unique_str, unique_id):
        stor_del = storage.Storage(unique_id, unique_str)
        stor_del.stor_del(unique_str, unique_id)

    def _vplx_del(self, unique_str, unique_id):
        v_del = vplx.VplxCrm(unique_id, unique_str)
        v_del.vlpx_del(unique_str, unique_id)

    def _vplx_retry(self, unique_str, unique_id):
        v_retry = vplx.VplxCrm(unique_str, unique_id)
        v_retry.retry_login()

    def _host_retry(self, unique_id):
        host_retry = host_initiator.HostTest(unique_id)
        host_retry.retry_login()

    def start_all_del(self, uniq_str, list_id=''):
        self._vplx_del(uniq_str, list_id)
        self._stor_del(uniq_str, list_id)
        self._host_retry(list_id)
        self._vplx_retry(uniq_str, list_id)

    def run(self):
        args = self.parser.parse_args()
        '''
        uniq_str: The unique string for this test, affects related naming
        '''
        if args.uniq_str:
            if not args.delete:
                if args.id_range:
                    id_range = args.id_range.split(',')
                    if len(id_range) == 2:
                        id_start, id_end = int(id_range[0]), int(id_range[1])
                    else:
                        self.parser.print_help()
                        sys.exit()
                else:
                    self.parser.print_help()
                    sys.exit()

                for i in range(id_start, id_end):
                    print(f'\n======*** Start working for ID {i} ***======')
                    self._storage(i, args.uniq_str)
                    self._vplx_drbd(i, args.uniq_str)
                    self._vplx_crm(i, args.uniq_str)
                    self._host_test(i)

            else:
                if args.id_range:
                    if ',' in args.id_range:
                        id_range = args.id_range.split(',')
                        id_start, id_end = int(id_range[0]), int(id_range[1])
                        list_id = [id_start, id_end]
                        self.start_all_del(args.uniq_str, list_id)

                    else:
                        list_id = []
                        list_id.append(args.id_range)
                        self.start_all_del(args.uniq_str, list_id)
                else:
                    self.start_all_del(args.uniq_str)
        else:
            self.parser.print_help()


if __name__ == '__main__':
    w = HydraArgParse()
    w.run()
