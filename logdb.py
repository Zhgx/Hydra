import re
import os
import subprocess
import sqlite3
import pprint
import consts

list_cmd = []


def prepare_db():
    db = LogDB()
    db.get_logdb()
    consts.set_glo_db(db)


def isFileExists(strfile):
    # 检查文件是否存在
    return os.path.isfile(strfile)


def get_target_file(filename):
    list_file = []
    file_last = None
    all_file = (os.listdir('.'))
    for file in all_file:
        if filename in file:
            list_file.append(file)
    list_file.sort(reverse=True)
    return list_file


class LogDB():
    create_table_sql = '''
    create table if not exists logtable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time DATE(30),
        transaction_id varchar(20),
        display varchar(5),
        type1 TEXT,
        type2 TEXT,
        describe1 TEXT,
        describe2 TEXT,
        data TEXT
        );'''

    insert_sql = '''
    replace into logtable
    (
        id,
        time,
        transaction_id,
        display,
        type1,
        type2,
        describe1,
        describe2,
        data
        )
    values(?,?,?,?,?,?,?,?,?)
    '''

    drop_table_sql = "DROP TABLE if exists logtable "

    def __init__(self):
        self.con = sqlite3.connect("logDB.db", check_same_thread=False)
        self.cur = self.con.cursor()

    def insert(self, data):
        self.cur.execute(self.insert_sql, data)

    def drop_tb(self):
        self.cur.execute(self.drop_table_sql)
        self.con.commit()

    def select_all(self):
        self.cur.execute("SELECT * FROM logtable")
        return self.cur.fetchall()

    # 获取表单行数据的通用方法
    def sql_fetch_one(self, sql):
        self.cur.execute(sql)
        data_set = self.cur.fetchone()
        if data_set:
            if len(data_set) == 1:
                return data_set[0]
            else:
                return data_set
        else:
            return data_set

    # 获取表全部数据的通用方法
    def sql_fetch_all(self, sql):
        cur = self.cur
        cur.execute(sql)
        date_set = cur.fetchall()
        return list(date_set)

    def get_cmd_result(self, oprt_id):
        sql = f"SELECT data FROM logtable WHERE type1 = 'DATA' and type2 = 'cmd' and describe2 = '{oprt_id}'"
        return self.sql_fetch_one(sql)


    def find_oprt_id_via_string(self, transaction_id, string):
        id_now = consts.glo_log_id()
        sql = f"SELECT id,data FROM logtable WHERE describe1 = '{string}' and id > {id_now} and transaction_id = '{transaction_id}'"
        id_and_oprt_id = self.sql_fetch_one(sql)
        if id_and_oprt_id:
            return id_and_oprt_id
        else:
            return ('','')

    def get_string_id(self, transaction_id):
        sql = f"SELECT data FROM logtable WHERE describe1 = 'Start a new trasaction' and transaction_id = '{transaction_id}'"
        _id = self.sql_fetch_one(sql)
        sql = f"SELECT data FROM logtable WHERE describe1 = 'unique_str' and transaction_id = '{transaction_id}'"
        string = self.sql_fetch_one(sql)
        return (string, _id)
        # re_ = re.compile(r'Start to create lun, name: (.*)_(.*)')
        # return re_.findall(result[0])

    def get_info_start(self, oprt_id):
        # 通过oprt_id，获取到INFO start信息
        sql = f"SELECT data FROM logtable WHERE type1 = 'INFO' and describe1 = 'start' and describe2 = '{oprt_id}'"
        return self.sql_fetch_one(sql)

    def get_info_finish(self, oprt_id):
        # 通过oprt_id，获取到INFO finish信息
        sql = f"SELECT data FROM logtable WHERE type1 = 'INFO' and describe1 = 'finish' and describe2 = '{oprt_id}'"
        return self.sql_fetch_one(sql)

    #-m:via? with
    def get_transaction_id_via_date(self, date_start, date_end):
        # 获取一个时间段内的全部事务id
        sql = f"SELECT DISTINCT transaction_id FROM logtable WHERE time >= '{date_start}' and time <= '{date_end}'"
        result = self.sql_fetch_all(sql)
        list_result = []
        if result:
            for i in result:
                list_result.append(i[0])
            return list_result
        return []

    def get_all_transaction(self):
        sql = f'SELECT DISTINCT transaction_id FROM logtable'
        result = self.sql_fetch_all(sql)
        list_result = []
        if result:
            for i in result:
                list_result.append(i[0])
            return list_result
        return []

    def get_cmd_via_tid(self, transaction_id):
        sql = f"SELECT data FROM logtable WHERE transaction_id = '{transaction_id}'"
        return self.sql_fetch_one(sql)

    def get_time_via_str(self, transaction_id , str):
        id_now = consts.glo_log_id()
        sql = f"SELECT time FROM logtable WHERE transaction_id = '{transaction_id}' and id >= {id_now} and data LIKE '%{str}%'"
        return self.sql_fetch_one(sql)

    def get_time_via_unique_str(self,transaction_id, str):
        id_now = consts.glo_log_id()
        oprt_id = self.find_oprt_id_via_string(transaction_id,str)[1]
        sql = f"SELECT time FROM logtable WHERE transaction_id = '{transaction_id}' and id >= {id_now} and describe2 = '{oprt_id}'"
        return self.sql_fetch_one(sql)

    def get_exception_info(self,transaction_id):
        id_now = consts.glo_log_id()
        sql = f"SELECT data FROM logtable WHERE transaction_id = '{transaction_id}' and describe1 = 'exception' and id >= {id_now}"
        return self.sql_fetch_one(sql)

    def get_last_one(self,transaction_id):
        sql = f"SELECT describe1,data FROM logtable WHERE transaction_id = '{transaction_id}' ORDER BY id DESC"
        return self.sql_fetch_one(sql)

    def get_oprt_id_via_db_id(self,transaction_id,db_id):
        sql = f"SELECT data FROM logtable WHERE transaction_id = '{transaction_id}' and id = {db_id}"
        return self.sql_fetch_one(sql)





    def get_logdb(self):
        self.drop_tb()
        self.cur.execute(self.create_table_sql)
        self.con.commit()
        log_path = "./Hydra_log.log"
        logfilename = 'Hydra_log.log'
        id = (None,)
        re_ = re.compile(r'\[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?\]?)\]\|',
                         re.DOTALL)
        if not isFileExists(log_path):
            print('no file')
            return

        for file in get_target_file(logfilename):
            f = open('./' + file)
            content = f.read()
            file_data = re_.findall(content)
            for data_one in file_data:
                data = id + data_one
                self.insert(data)

            f.close()

        self.con.commit()
        # self.con.close()


if __name__ == '__main__':
    db = LogDB()
    db.get_logdb()
    # print(db.find_oprt_id_via_string('1594878912', 'V9jGOP2v'))
    # print(db.get_string_id('1594963387'))
    # print(db.get_time_via_unique_str('1595209399','jMPFwXy2'))
    # print(db.get_time_via_str('1595209399','123213'))
    # print(db.get_exception('1595296861'))
    # print(db.get_cmd_result(''))
    # print(db.get_time_via_str('1595396085','Start iscsi login'))
    # print(db.get_last_one('1595409897'))
    print(db.get_all_transaction())
    # print(db.get_oprt_id_via_db_id(''))
    # print(db.get_time_via_str('1595295584','Start to create lun, name: log_test_203'))
    # print(db.get_cmd_via_tid('1594879092'))
    # res = db.get_transaction_id_via_date('2021/07/13 13:45:57','2021/07/13 13:51:55')
