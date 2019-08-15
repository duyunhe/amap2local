# -*- coding: utf-8 -*-
# @Time    : 2019/2/14 14:13
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : ocl2lite.py

import os
import sqlite3
from collections import defaultdict

import cx_Oracle

from geo import bl2xy, xy2bl, wgs84_to_gcj02
from refineMap import dog_last

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


class Segment(object):
    def __init__(self, sid, name, direction, length, rank):
        self.sid, self.name, self.direction, self.length, self.rank = sid, name, direction, length, rank


class Point(object):
    def __init__(self, pid, sid, seq, longti, lati):
        self.pid, self.sid, self.seq, self.longti, self.lati = pid, sid, seq, longti, lati


def txt():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    sql = "select * from tb_segment where s_id <= 6701"
    cursor.execute(sql)
    seg_list = []
    for item in cursor:
        s_id, s_name, direction, length, rank = item[0], item[1], item[4], item[5], item[9]
        segment = Segment(s_id, s_name, direction, length, rank)
        seg_list.append(segment)

    fp_sp = open("tb_segment.csv", 'w')
    fp_pt = open("tb_seg_point.csv", 'w')

    pt_dict = defaultdict(list)
    sql = "select * from tb_seg_point order by s_id, seq"
    cursor.execute(sql)

    for item in cursor:
        pid, s_id, seq, longti, lati = item[:]
        pt = Point(pid, s_id, seq, longti, lati)
        pt_dict[s_id].append(pt)
    print "select over"

    for seg in seg_list:
        pt_list = list(pt_dict[seg.sid])
        if seg.direction == 2:
            pt_list = reversed(pt_list)
            seg.direction = 1
        else:
            seg.direction = 0
        str_line = "{0},{1},{2},{3},{4}\n".format(seg.sid, seg.name, seg.direction, seg.length, seg.rank)
        fp_sp.write(str_line)
        for i, pt in enumerate(pt_list):
            str_line = "{0},{1},{2},{3},{4}\n".format(pt.pid, pt.sid, i, pt.longti, pt.lati)
            fp_pt.write(str_line)

    fp_pt.close()
    fp_sp.close()


def simplify(point_dict):
    pid = 0
    for sid, pt_list in point_dict.iteritems():
        xy_list = []
        for pt in pt_list:
            x, y = bl2xy(pt.lati, pt.longti)
            xy_list.append([x, y])
        path = dog_last(xy_list)
        new_pt_list = []
        for i, xy in enumerate(path):
            x, y = xy[:]
            lat, lng = xy2bl(x, y)
            pt = Point(pid, sid, i, lng, lat)
            pid += 1
            new_pt_list.append(pt)
        point_dict[sid] = new_pt_list
    return point_dict


def main():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    conn_lite = sqlite3.connect("./hz1.db")
    cursor = conn.cursor()
    sql = "select * from tb_segment"
    cursor.execute(sql)
    seg_list = []
    for item in cursor:
        s_id, s_name, begin_pid, end_pid, direction, length, rank = item[0], item[1], item[2],\
                                                                    item[3], int(item[4]), item[5], item[9]
        segment = Segment(s_id, s_name, direction, length, rank)
        if rank is not None:
            seg_list.append(segment)

    pt_dict = defaultdict(list)
    sql = "select * from tb_seg_point order by s_id, seq"
    cursor.execute(sql)

    for item in cursor:
        pid, s_id, seq, longti, lati = item[:]
        pt = Point(pid, s_id, seq, longti, lati)
        pt_dict[s_id].append(pt)
    print "select over"

    pt_dict = simplify(pt_dict)

    seg_tup_list = []
    pt_tup_list = []

    for j, seg in enumerate(seg_list):
        # cursor.execute(sql)
        pt_list = list(pt_dict[seg.sid])
        seg.sid = j
        if seg.direction == 2:
            pt_list = reversed(pt_list)
            seg.direction = 1
        elif seg.direction == 3:
            seg.direction = 0
        uname = u""
        if seg.name is not None:
            try:
                uname = seg.name.decode('utf-8')
            except UnicodeDecodeError:
                print seg.name
        try:
            urank = seg.rank.decode('utf-8')
        except UnicodeDecodeError:
            print "error", seg.rank
        t = (seg.sid, uname, seg.direction, urank, seg.length)
        # print seg.direction
        seg_tup_list.append(t)

        for i, pt in enumerate(pt_list):
            t = (pt.pid, seg.sid, i + 1, pt.longti, pt.lati)
            pt_tup_list.append(t)

    conn_lite.executemany("insert into tb_seg_point(point_id, s_id, seq, longi, lati) "
                          "values(?,?,?,?,?)", pt_tup_list)
    conn_lite.commit()
    conn_lite.executemany("insert into tb_segment(s_id, S_NAME, direction, rank, s_len) "
                          "values (?,?,?,?,?)", seg_tup_list)
    conn_lite.commit()

    conn.close()
    conn_lite.close()


def trans():
    c2 = sqlite3.connect("./hz2.db")
    cur = c2.cursor()
    sql = "select * from tb_seg_point"
    cur.execute(sql)
    tup_list = []
    for item in cur:
        pid, sid, seq, lng, lat = item[:]
        mlng, mlat = wgs84_to_gcj02(lng, lat)
        x, y = bl2xy(mlat, mlng)
        tup_list.append((pid, sid, seq, x, y))
    cur.close()
    c2.close()

    c3 = sqlite3.connect("./hz3.db")
    cur = c3.cursor()
    cur.executemany("insert into tb_seg_point(point_id, s_id, seq, px, py) "
                    "values (?,?,?,?,?)", tup_list)
    c3.commit()
    cur.close()
    c3.close()


trans()
