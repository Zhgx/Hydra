import re
import os
import subprocess
import sqlite3
import pprint

list_cmd = []


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
    """
    [2020/06/29 15:19:19] [1593415151] [DATA] [output] [re_result] [['UpToDate']]
    [2020/06/29 15:19:19] [1593415151] [INFO] [info] [] [res_logtest1_184 DRBD check successful]
    """

    create_table_sql = '''
    create table if not exists logtable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time DATE(30),
        transaction_id varchar(20),
        type varchar(20),
        describe1 TEXT,
        describe2 TEXT,
        describe3 TEXT,
        data TEXT
        );'''

    insert_sql = '''
    replace into logtable
    (
        id,
        time,
        transaction_id,
        type,
        describe1,
        describe2,
        describe3,
        data
        )
    values(?,?,?,?,?,?,?,?)
    '''


    drop_table_sql = "DROP TABLE if exists logtable "

    def __init__(self):
        self.con = sqlite3.connect("logDB.db", check_same_thread=False)
        self.cur = self.con.cursor()
        self.drop_tb()
        self.cur.execute(self.create_table_sql)
        self.con.commit()

    def insert(self, data):
        self.cur.execute(self.insert_sql, data)

    def drop_tb(self):
        self.cur.execute(self.drop_table_sql)
        self.con.commit()

    # 获取表单行数据的通用方法
    def sql_fetch_one(self, sql):
        self.cur.execute(sql)
        date_set = self.cur.fetchone()
        return date_set

    # 获取表全部数据的通用方法
    def sql_fetch_all(self, sql):
        cur = self.cur
        cur.execute(sql)
        date_set = cur.fetchall()
        return list(date_set)

    def get_all_via_tid(self, transaction_id):
        sql = "SELECT type,describe1,describe2,describe3,data FROM logtable WHERE transaction_id = '%s'" % transaction_id
        return self.sql_fetch_all(sql)

    def get_cmd_data(self,cmd_id):
        if cmd_id == '':
            return
        sql = "SELECT data FROM logtable WHERE describe3 = '%s'" % cmd_id
        result = self.sql_fetch_all(sql)
        if len(result) == 2:
            print(f'执行的命令:{result[0][0]} ｜结果:{result[1][0]}')
        else:
            print(f'执行命令或结果：',result[0][0])

    def replay_via_tid(self,transaction_id):
        data = self.get_all_via_tid(transaction_id)
        print('=========== * replay * ============')
        for i in data:
            if i[0] == 'INFO' and i[2] == 'start':
                print('--------------------')
                print(i[4])
                continue

            if i[0] == 'OPRT' and i[1] == 'cmd':
                self.get_cmd_data(i[3])

            elif i[2] == 're':
                print(f'regular result:{i[4]}')

            #[2020 / 07 / 01 14: 23:59] [1593584622][DATA][result][re][][['10.203.1.199']]
            elif i[1] != 'output' and i[2] != 'cmd':
                print(i[4])



    def get_info_via_tid(self, transaction_id):
        sql = "SELECT data FROM logtable WHERE type = 'INFO' and transaction_id = '%s'" % transaction_id
        return self.sql_fetch_all(sql)

    def get_userinput_from_tid(self, transaction_id):
        sql = "SELECT data FROM logtable WHERE type = 'INFO' and transaction_id = '%s'" % transaction_id
        return self.sql_fetch_one(sql)[0]


    def get_result_from_time(self,start_time,end_time):
        sql = "SELECT data FROM logtable WHERE type = 'result_to_show' and time >= '%s' and time <= '%s'"%(start_time,end_time)
        return self.sql_fetch_all(sql)

    def get_data_via_tid(self, transaction_id):
        sql = "SELECT data FROM logtable WHERE type = 'DATA' and transaction_id = '%s'"% transaction_id
        return self.sql_fetch_all(sql)

    def produce_logdb(self):
        log_path = "./Hydra_log.log"
        logfilename = 'Hydra_log.log'
        id = (None,)
        re_ = re.compile(r'\[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?\]?)\]', re.DOTALL)
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