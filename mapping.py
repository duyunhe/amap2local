# -*- coding: utf-8 -*-
# @Time    : 2019/1/9 15:03
# @Author  : yhdu@tongwoo.cn
# @简介    : 映射单向路到双向路上面
# @File    : mapping.py


import os

import cx_Oracle

from geo import bl2xy, get_segment_distance, calc_include_angle3
from map_struct import Road, Point

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def get_st_road():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    sql = "select sp.s_id, sp.seq, sp.longti, sp.lati, s.s_name, s.direction " \
          "from tb_segment s, tb_seg_point sp where sp.s_id = s.s_id and " \
          "s.s_name like '%德胜%' and (s.rank != '快速路' and s.rank != '匝道')" \
          " order by s_id, seq"
    cursor.execute(sql)

    xy_dict = {}
    name_dic = {}  # name
    dir_dict = {}  # direction
    for items in cursor:
        rid = int(items[0])
        l, b = map(float, items[2:4])
        x, y = bl2xy(b, l)
        pt = Point(x, y)
        name = items[4]
        ort = int(items[5])
        try:
            xy_dict[rid].append(pt)
        except KeyError:
            xy_dict[rid] = [pt]
            name_dic[rid] = name
            dir_dict[rid] = ort
    road_list = []
    # cnt0, cnt1 = 0, 0
    for rid, items in xy_dict.iteritems():
        ort = dir_dict[rid]
        if ort == 2:
            items.reverse()
        r = Road(name_dic[rid], ort, rid)
        r.set_point_list(items)
        r.gene_segment()
        # cnt0 += len(r.point_list)
        road_list.append(r)

    conn.close()
    return road_list


def get_main_road():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    sql = "select sp.s_id, sp.seq, sp.longti, sp.lati, s.s_name, s.direction " \
          "from tb_segment s, tb_seg_point sp where sp.s_id = s.s_id and " \
          "s.s_name like '%德胜%' and (s.rank = '快速路')" \
          " order by s_id, seq"
    cursor.execute(sql)

    xy_dict = {}
    name_dic = {}  # name
    dir_dict = {}  # direction
    for items in cursor:
        rid = int(items[0])
        l, b = map(float, items[2:4])
        x, y = bl2xy(b, l)
        pt = Point(x, y)
        name = items[4]
        ort = int(items[5])
        try:
            xy_dict[rid].append(pt)
        except KeyError:
            xy_dict[rid] = [pt]
            name_dic[rid] = name
            dir_dict[rid] = ort
    road_list = []
    # cnt0, cnt1 = 0, 0
    for rid, items in xy_dict.iteritems():
        ort = dir_dict[rid]
        if ort == 2:
            items.reverse()
        r = Road(name_dic[rid], ort, rid)
        r.set_point_list(items)
        r.gene_segment()
        # cnt0 += len(r.point_list)
        road_list.append(r)

    conn.close()
    return road_list


def main():
    fp = open('mapping.txt', 'a')
    zh_road = get_st_road()
    main_road = get_main_road()

    for road0 in main_road:
        rd, sel, sel_a = 1e10, -1, 0
        for road1 in zh_road:
            min_d, sa = 1e10, 0
            for seg0 in road0.seg_list:
                for seg1 in road1.seg_list:
                    d = get_segment_distance(seg0, seg1)
                    # print road0.rid, road1.rid, d
                    angle = calc_include_angle3(seg0, seg1)
                    if d < min_d:
                        min_d, sa = d, angle
            if min_d < rd:
                rd, sel, sel_a = min_d, road1.rid, sa
        if rd < 50:
            print road0.rid, sel, rd, sel_a
            map_rid = sel * 2 if sel_a >= 0 else sel * 2 + 1
            fp.write("{0},{1}\n".format(road0.rid, map_rid))

    fp.close()

    # for road in zh_road:
    #     x_list, y_list = [], []
    #     for pt in road.point_list:
    #         x_list.append(pt.px)
    #         y_list.append(pt.py)
    #     plt.plot(x_list, y_list, 'b')
    #     plt.text((x_list[0] + x_list[-1]) / 2, (y_list[0] + y_list[-1]) / 2, road.rid)
    #
    # for road in main_road:
    #     x_list, y_list = [], []
    #     for pt in road.point_list:
    #         x_list.append(pt.px)
    #         y_list.append(pt.py)
    #     plt.plot(x_list, y_list, 'b')
    #     plt.text((x_list[0] + x_list[-1]) / 2, (y_list[0] + y_list[-1]) / 2, road.rid)
    # plt.show()


main()
