# -*- coding: utf-8 -*-
# @Time    : 2018/11/9 10:28
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : read_sqlite.py

import sqlite3

import matplotlib.pyplot as plt

from geo import bl2xy
from refineMap import Road, Point, dog_last


def main():
    road_list = load_sqlite_road()
    for road in road_list:
        x_list, y_list = [], []
        for pt in road.point_list:
            x, y = pt.px, pt.py
            x_list.append(x)
            y_list.append(y)
        plt.plot(x_list, y_list)
    plt.show()


def remove():
    conn = sqlite3.connect('./data/hz.db3')
    cursor = conn.cursor()
    fp = open('./data/rm.txt')
    for line in fp.readlines():
        item = int(line.strip())
        sql = "delete from tb_seg_point where s_id = :1"
        cursor.execute(sql, (item,))
        # ok
    conn.commit()
    conn.close()


def road_simplify(road):
    """
    简化
    :param road: Road
    :return:
    """
    pts = road.point_list
    xy_list = []
    for pt in pts:
        xy_list.append([pt.px, pt.py])
    xy_list = dog_last(xy_list)
    road.point_list = []
    for xy in xy_list:
        pt = Point(xy[0], xy[1])
        road.add_point(pt)
    road.gene_segment()


def load_sqlite_road():
    """
    从sqlite3中读取路网
    :return: 
    """
    conn = sqlite3.connect('./data/hz.db3')
    cursor = conn.cursor()
    cursor.execute("select s_id, seq, longti, lati from tb_seg_point order by s_id, seq")
    xy_dict = {}
    for items in cursor:
        rid = int(items[0])
        l, b = map(float, items[2:4])
        x, y = bl2xy(b, l)
        pt = Point(x, y)
        try:
            xy_dict[rid].append(pt)
        except KeyError:
            xy_dict[rid] = [pt]
    road_list = []
    # cnt0, cnt1 = 0, 0
    for rid, items in xy_dict.iteritems():
        r = Road("", 0, rid)
        r.set_point_list(items)
        # cnt0 += len(r.point_list)
        road_list.append(r)
        road_simplify(r)
        # cnt1 += len(r.point_list)
    cursor.close()
    conn.close()
    return road_list


main()
