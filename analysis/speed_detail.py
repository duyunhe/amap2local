# -*- coding: utf-8 -*-
# @Time    : 2019/4/24
# @Author  : Clark Du
# @简介    : from speed detail to final speed
# @File    : speed_detail.py


import cx_Oracle
from collections import defaultdict


def proc_list(speed_list):



def proc_detail():
    veh_dict = defaultdict(list)
    conn = cx_Oracle.connect('hz', 'hz', '192.168.11.88/orcl')
    cursor = conn.cursor()
    sql = "select * from TB_ROAD_SPEED_DETAIL t"
    cursor.execute(sql)
    for item in cursor:
        rid, ort, _, spd, dist = item[:]
        sid = rid * 2 + ort
        veh_dict[sid].append([spd, dist])
    for sid, spd_list in veh_dict.iteritems():
        proc_list(spd_list)
        break


proc_detail()
