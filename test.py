import connect as conn
import re
unique_name = 'luntest'
unique_id = r'\w*'
# atest=b"'res_luntest_0' , 'res_luntest_1', 'res_luntest_2', 'res_luntest_3', 'res_luntest_26','res_luntest_111'"
atest = b'''t_test (ocf::heartbeat:iSCSITarget): Started
res3 (ocf::heartbeat:iSCSILogicalUnit): Stopped
res_test_9 (ocf::heartbeat:iSCSILogicalUnit): Stopped
res_test_12 (ocf::heartbeat:iSCSILogicalUnit): Stopped
res_test_13 (ocf::heartbeat:iSCSILogicalUnit): Stopped
res_test_14 (ocf::heartbeat:iSCSILogicalUnit): Stopped
res_lun_15 (ocf::heartbeat:iSCSILogicalUnit): Started
res_luntest_2 (ocf::heartbeat:iSCSILogicalUnit): Stopped
res_luntest_20 (ocf::heartbeat:iSCSILogicalUnit): Started
res_luntest_21 (ocf::heartbeat:iSCSILogicalUnit): Started
res_luntest_200 (ocf::heartbeat:iSCSILogicalUnit): Stopped'''
re_showstr = re.compile(f'(res_{unique_name}_{unique_id})\s.*:\s(\w*)')
re_show_result = re_showstr.findall(str(atest, encoding='utf-8'))
result = dict(re_show_result)
print(result['res_luntest_20'])
