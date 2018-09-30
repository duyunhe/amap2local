# -*- coding: utf-8 -*-
# @Time    : 2018/9/28 16:58
# @Author  : 
# @简介    : 道路自由流下速度
# @File    : test_road_free_speed.py


import cx_Oracle
import numpy as np


conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
cursor = conn.cursor()
tup_list = []
for i in range(330):
    sql = "select t.*, s.road_name from TB_ROAD_SPEED_PRE t, " \
          "tb_road_state s where t.rid = s.rid and t.rid = {0}".format(i)
    cursor.execute(sql)
    speed_list = []
    for item in cursor:
        speed_list.append(float(item[1]))
    if len(speed_list) == 0:
        continue
    try:
        std, mean = np.std(speed_list), np.mean(speed_list)
        per75 = np.percentile(speed_list, 75)
        b = 1
        lower_bound, upper_bound = mean - b * std, mean + b * std
        lower_cnt = np.sum(list(map(lambda x: x < lower_bound, speed_list)))
        upper_cnt = np.sum(list(map(lambda x: x > upper_bound, speed_list)))
        radio = max(speed_list) / min(speed_list)
        print i, std, lower_cnt, upper_cnt, upper_bound, per75, radio
        tup_list.append((min(70, per75), i))
    except IndexError:
        pass
sql = "update tb_road_def_speed set speed = :1 where rid = :2"
cursor.executemany(sql, tup_list)
conn.commit()
cursor.close()
conn.close()
