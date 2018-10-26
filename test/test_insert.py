# -*- coding: utf-8 -*-
# @Time    : 2018/10/16 9:00
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : test_insert.py

import cx_Oracle

conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
cursor = conn.cursor()
tup_list = []
sql = "insert into tb_road_def_speed values(:1,:2)"
for i in range(330, 5432):
    tup = (i, 50.0)
    tup_list.append(tup)
cursor.executemany(sql, tup_list)
conn.commit()
cursor.close()
conn.close()
