# -*- coding: utf-8 -*-
# @Time    : 2018/9/30 14:56
# @Author  : 
# @简介    : 计算拓扑关系
# @File    : topo.py


import cx_Oracle

from refineMap import load_model2road

conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
cursor = conn.cursor()
sql = "insert into tb_road_topo values(:1, :2)"
road_list = load_model2road('./road/10_offset/par0.txt')
tup_list = []
for i, road0 in enumerate(road_list):
    for j, road1 in enumerate(road_list):
        et0, bt0, et1, bt1 = road0.point_list[-1], \
                             road0.point_list[0], road1.point_list[-1], road1.point_list[0]
        if et0 == bt1 or bt0 == et1:
            tup = (road0.rid, road1.rid)
            tup_list.append(tup)
    for cross in road0.cross_list:
        rid1 = cross['name']
        tup = (road0.rid, rid1)
        tup_list.append(tup)
cursor.executemany(sql, tup_list)
conn.commit()
cursor.close()
conn.close()
