# -*- coding: utf-8 -*-
# @Time    : 2019/3/29 16:06
# @Author  : yhdu@tongwoo.cn
# @简介    : 对sqlite中的数据库进行完善
# @File    : refineDB.py


import sqlite3
from collections import defaultdict

import numpy as np

from geo import bl2xy, xy2bl, calc_dist

DIST_THREAD = 600


def add_pt(last_pt, pt):
    pt_list = []
    v0 = np.array(last_pt)
    v1 = np.array(pt)
    dv = v1 - v0
    dist = calc_dist(pt, last_pt)
    uv = dv / dist
    cv = v0
    while dist > DIST_THREAD * 2:
        v = cv + uv * DIST_THREAD
        dist -= DIST_THREAD
        pt_list.append([v[0], v[1]])
        cv = v
    v = cv + uv * dist / 2
    pt_list.append([v[0], v[1]])
    return pt_list


def split_road():
    conn1 = sqlite3.connect("../map_info/hz1.db")
    cursor = conn1.cursor()
    sql = "select * from TB_SEG_POINT order by s_id, seq;"
    cursor.execute(sql)
    roads = defaultdict(list)
    for item in cursor:
        s_id, seq, lng, lat = item[1:]
        x, y = bl2xy(lat, lng)
        roads[s_id].append([x, y])

    pt_tup_list = []
    for sid, pt_list in roads.iteritems():
        last_pt = None
        new_pt_list = []
        for pt in pt_list:
            if last_pt is not None:
                dist = calc_dist(pt, last_pt)
                if dist > DIST_THREAD:
                    for n_pt in add_pt(last_pt, pt):
                        new_pt_list.append(n_pt)
            last_pt = pt
            new_pt_list.append(pt)
        roads[sid] = new_pt_list
        for i, pt in enumerate(new_pt_list):
            b, l = xy2bl(pt[0], pt[1])
            t = (sid, i + 1, l, b)
            pt_tup_list.append(t)

    cursor.close()
    conn1.close()

    conn2 = sqlite3.connect("../map_info/hz2.db")
    cursor = conn2.cursor()
    sql2 = "insert into tb_seg_point(point_id, s_id, seq, longi, lati) values(0,?,?,?,?)"
    cursor.executemany(sql2, pt_tup_list)
    conn2.commit()
    cursor.close()


split_road()
