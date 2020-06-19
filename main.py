
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
        drbd.discover_new_lun()
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

    def run(self):
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
                    self.parser.print_help()
                    sys.exit()
            else:
                self.parser.print_help()
                sys.exit()

            for i in range(id_start, id_end):
                print(f'\n======*** Start working for ID {i} ***======')
                self._storage(i, args.unique_str)
                self._vplx_drbd(i, args.unique_str)
                self._vplx_crm(i, args.unique_str)
                time.sleep(1.5)
                self._host_test(i)
        else:
            self.parser.print_help()


if __name__ == '__main__':
    w = HydraArgParse()
    w.run()
