# -*- coding: utf-8 -*-
# @Time    : 2018/12/26 9:47
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : db2txt.py


import os
from collections import defaultdict
from time import clock

import cx_Oracle

from common import wgs84togcj02
from geo import bl2xy
from map_struct import Road, Point
from refineMap import save_road2model

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


class RoadSegment(object):
    def __init__(self, rid, bid, eid, direction, name, length):
        self.rid = rid
        self.bid, self.eid, self.direction, self.name, self.length = bid, eid, direction, name, length
        self.point_list = []

    def add_pt(self, point):
        self.point_list.append(point)


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "db2txt.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


def gene_one_road(road_list):
    """
    :param road_list: [RoadSegment]
    :return: ret_list: [Road]
    """
    prev = [-1] * len(road_list)
    nxt = [-1] * len(road_list)

    sbid = {'德胜高架路': 5991, '钱江三桥（西兴大桥）': 1411, '上塘高架路': 6281}
    seid = {'德胜高架路': 1937, '钱江三桥（西兴大桥）': 4771, '上塘高架路': 965}

    eds = {}
    name = None
    for i, road in enumerate(road_list):
        eds[road.eid] = i
        name = road.name
    for i, road in enumerate(road_list):
        try:
            j = eds[road.bid]
            prev[i] = j
            nxt[j] = i
        except KeyError:
            prev[i] = -1

    cnt = 0
    for i in range(len(road_list)):
        if prev[i] == -1:
            cnt += 1
    print name, cnt
    uname = name.decode('utf-8')

    ret_list = []
    if cnt == 1:
        bi = None
        for i in range(len(road_list)):
            if prev[i] == -1:
                bi = i
                break
        ti = bi
        last_length = -1
        while nxt[ti] != -1:
            length = road_list[ti].length
            if last_length == length:
                break
            print road_list[ti].rid
            r = Road(uname, 0, road_list[ti].rid)
            ret_list.append(r)
            ti = nxt[ti]
            last_length = length
    elif cnt == 0:
        bi = None
        for i, road in enumerate(road_list):
            if road.rid == sbid[name]:
                bi = i
                break
        ti = bi
        last_length = -1
        while True:
            length = road_list[ti].length
            if road_list[ti].rid == seid[name]:
                break
            print road_list[ti].rid
            r = Road(uname, 0, road_list[ti].rid)
            ret_list.append(r)
            ti = nxt[ti]
            last_length = length
    elif cnt == 3:
        bi = None
        for i, road in enumerate(road_list):
            if road.rid == sbid[name]:
                bi = i
                break
        ti = bi
        last_length = -1
        while True:
            length = road_list[ti].length
            print road_list[ti].rid
            r = Road(uname, 0, road_list[ti].rid)
            ret_list.append(r)
            if road_list[ti].rid == seid[name]:
                break

            ti = nxt[ti]
            last_length = length

    elif cnt == 2:
        bi = None
        for i, road in enumerate(road_list):
            if prev[i] == -1:
                bi = i
                break
        ti = bi
        last_length = -1
        while ti != -1:
            length = road_list[ti].length
            print road_list[ti].rid
            r = Road(uname, 0, road_list[ti].rid)
            ret_list.append(r)
            ti = nxt[ti]
            last_length = length

    print "____________"
    return ret_list


def load_double_road():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    cursor.execute("select sp.s_id, sp.seq, sp.longti, sp.lati, s.s_name, s.direction, s.begin_id, s.end_id"
                   ", s.length from tb_seg_point sp, tb_segment s where sp.s_id = s.s_id and s.rank = '快速路'"
                   " order by sp.s_id, sp.seq")
    xy_dict = {}
    info_dict = defaultdict(list)
    road_name = {}
    for items in cursor:
        rid = int(items[0])
        l, b = map(float, items[2:4])
        l, b = wgs84togcj02(l, b)
        x, y = bl2xy(b, l)
        pt = Point(x, y)
        name = items[4]
        uname = name.decode('utf-8')
        road_name[rid] = uname
        # if name is not None:
        #     name = name.decode('utf-8')
        if name != '艮山西路':
            continue
        direction = items[5]
        if direction == '3':
            continue
        bid, eid = items[6:8]
        length = items[8]
        if direction == '2':
            bid, eid = eid, bid
        try:
            xy_dict[rid].append(pt)
        except KeyError:
            xy_dict[rid] = [pt]
            rs = RoadSegment(rid, bid, eid, direction, name, length)
            info_dict[name].append(rs)

    # add rid
    rid_list = []
    for name, road_list in info_dict.iteritems():
        rid_list.extend(gene_one_road(road_list))

    road_list = []
    for road in rid_list:
        rid = road.rid
        pt_list = xy_dict[rid]
        new_road = Road(road_name[rid], 0, rid)
        new_road.set_point_list(pt_list)
        road_list.append(new_road)

    return road_list


@debug_time
def load_oracle_road():
    """
    从oracle中读取路网 
    :return: list of Road
    """
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    cursor.execute("select sp.s_id, sp.seq, sp.longti, sp.lati, s.s_name, s.direction"
                   " from tb_seg_point sp, tb_segment s " 
                   "where sp.s_id = s.s_id and (s.rank = '快速路' or s.rank = '高速公路' or s.s_name = '天目山路'"
                   " or s.s_name = '艮山西路' or s.s_name = '文一路' or s.s_name = '文一西路')"
                   " order by s_id, seq")
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
        if name != u'艮山西路':
            continue
        direction = items[5]
        if direction != '3':
            continue
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
    ret_list = []
    data_list1 = load_oracle_road()
    data_list2 = load_double_road()
    ret_list.extend(data_list1)
    ret_list.extend(data_list2)
    # data1 = load_double_road()
    save_road2model('../road_test/center.txt', ret_list)


# save()

