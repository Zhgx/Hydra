#  coding: utf-8

import time

import sys
import sundry as s
import pprint
import traceback
import consts
import storage
import vplx
import host_initiator


def get_dbg_stor(folder):
    tid = consts.glo_tsc_id()
    stor = storage.Storage()
    stor.generate_debug()
    stor.save_log()

def get_vplx_debug(folder):
    tid = consts.glo_tsc_id()
    drbd = vplx.VplxDrbd()
    crm = vplx.VplxCrm()
    drbd.get_sys_debug()

def get_debug():
    tid = consts.glo_tsc_id()
    log_folder = f'/var/log/{tid}'
    mk_folder(log_folder)

    get_stor_debug(log_folder)
    get_vplx_debug(log_folder)
    get_drbd_debug(log_folder)
    get_crm_debug(log_folder)
    get_host_debug(log_folder)
    
