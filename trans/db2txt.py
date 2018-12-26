# -*- coding: utf-8 -*-
# @Time    : 2018/12/26 9:47
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : db2txt.py


import os
from time import clock

import cx_Oracle

from common import wgs84togcj02
from geo import bl2xy
from map_struct import Road, Point
from refineMap import save_road2model

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "db2txt.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


@debug_time
def load_oracle_road():
    """
    从oracle中读取路网 
    :return: list of Road
    """
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    cursor.execute("select sp.s_id, sp.seq, sp.longti, sp.lati, s.s_name from tb_seg_point sp, tb_segment s "
                   "where sp.s_id = s.s_id and s.direction = 3 and (s.rank != '匝道' and s.rank != '步行街' "
                   "and s.rank != '连杆道路' and s.rank != '次要支路' and s.rank != '一级公路' and s.rank != '二级公路') "
                   "order by sp.s_id, sp.seq")
    xy_dict = {}
    road_name = {}
    for items in cursor:
        rid = int(items[0])
        l, b = map(float, items[2:4])
        l, b = wgs84togcj02(l, b)
        x, y = bl2xy(b, l)
        pt = Point(x, y)
        name = items[4]
        if name is not None:
            name = name.decode('utf-8')
        road_name[rid] = name
        try:
            last_pt = xy_dict[rid][-1]
            if last_pt == pt:
                continue
            xy_dict[rid].append(pt)
        except KeyError:
            xy_dict[rid] = [pt]
    road_list = []
    # cnt0, cnt1 = 0, 0
    for rid, items in xy_dict.iteritems():
        r = Road(road_name[rid], 0, rid)
        r.set_point_list(items)
        # cnt0 += len(r.point_list)
        road_list.append(r)
        # road_simplify(r)
        # cnt1 += len(r.point_list)
    cursor.close()
    conn.close()
    return road_list


def save():
    save_road2model('../road_new/center.txt', load_oracle_road())


save()
