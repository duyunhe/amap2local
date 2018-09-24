# -*- coding: utf-8 -*-
# @Time    : 2018/9/21
# @Author  : Clark Du
# @简介    : 中心线的处理
# @File    : center.py

import json
import math
import numpy as np
from geo import bl2xy, xy2bl, calc_dist, point2segment, line2grid, \
    get_cross_point, is_segment_cross, get_parallel, point2segment2, calc_include_angle2, \
    cut_x, cut_y, get_dist, get_segment_length, cut_from_segment
from map_struct import Road, Point, Segment
from refineMap import load_model, save_model, xylist2polyline, dog_last, \
    polyline2xylist, polyline2path, coord2xy, get_diff, load_model2road, save_road2model


def center():
    road_data = load_model('./road/merge.txt')
    road_dict = {}
    for road_info in road_data:
        name = road_info['name']
        try:
            road_dict[name].append(road_info)
        except KeyError:
            road_dict[name] = [road_info]

    temp_list = load_model('./road/center.txt')
    exist_road = []
    for road_info in temp_list:
        name = road_info['name']
        exist_road.append(name)
    road_center_list = temp_list
    for name, road_list in road_dict.iteritems():
        if name in exist_road:
            continue
        xy_list = grid_center_line(name, road_list)
        polyline = xylist2polyline(xy_list)
        center_line = {'name': name, 'polyline': polyline}
        road_center_list.append(center_line)
    save_model('./road/center.txt', road_center_list)


def grid_center_line(road_name, road_list):
    print road_name
    if len(road_list) == 1:
        # 单行线
        test_road = road_list[0]
        pll = test_road['polyline']
        pt_list = []
        coord_list = polyline2path(pll)
        for coord in coord_list:
            px, py = coord2xy(coord)
            pt_list.append([px, py])
        pt_list = dog_last(pt_list)
        return pt_list
    road_xy_data = []

    sel_y = {}          # 用于每个y值需要扫描的栅格
    sel_x = {}

    test_road = road_list[0]
    pll = test_road['polyline']
    pt_list = []
    coord_list = polyline2path(pll)
    for coord in coord_list:
        px, py = coord2xy(coord)
        pt_list.append([px, py])
    dx = pt_list[0][0] - pt_list[-1][0]
    dy = pt_list[0][1] - pt_list[-1][1]
    k = math.fabs(dy / dx)
    scan_by_x = k < 1   # 沿着X轴或Y轴扫描

    line_xy = []
    for road_info in road_list:
        pll = road_info['polyline']
        coord_list = polyline2path(pll)
        seg_list = []
        lastx, lasty = 0, 0
        for i, coord in enumerate(coord_list):
            px, py = coord2xy(coord)
            if i > 0:
                seg_list.append(([lastx, lasty], [px, py]))
                grid_set = line2grid([lastx, lasty], [px, py])
                for x, y in grid_set:
                    line_xy.append([x, y])
                    if scan_by_x:
                        try:
                            sel_x[x].append(y)
                        except KeyError:
                            sel_x[x] = [y]
                    else:
                        try:
                            sel_y[y].append(x)
                        except KeyError:
                            sel_y[y] = [x]
            lastx, lasty = px, py
        road_xy_data.append(seg_list)

    plot_xy = []
    calc_cnt = 0

    if scan_by_x:
        # X scan
        x_coord = {}
        for x, y_list in sel_x.iteritems():
            # x_list = sel_y[y]
            y_list.sort()
            for y in np.arange(y_list[0], y_list[-1] + 1, 0.5):
                calc_cnt += 1
                diff, dist = get_diff(road_xy_data[0], road_xy_data[1], [x, y])
                if diff < 0.1:
                    try:
                        last_diff, last_dist, _ = x_coord[x]
                    except KeyError:
                        x_coord[x] = [diff, dist, y]
                        continue
                    if diff < last_diff:
                        x_coord[x] = [diff, dist, y]
                    elif diff == last_diff and dist < last_dist:
                        x_coord[x] = [diff, dist, y]
        print "calc cost ", calc_cnt
        keys = x_coord.keys()
        keys.sort()
        for x in keys:
            y = x_coord[x][2]
            plot_xy.append([x, y])

    else:
        # Y scan
        y_coord = {}
        for y, x_list in sel_y.iteritems():
            # x_list = sel_y[y]
            x_list.sort()
            for x in np.arange(x_list[0], x_list[-1] + 1, 0.5):
                calc_cnt += 1
                diff, dist = get_diff(road_xy_data[0], road_xy_data[1], [x, y])
                if diff < 0.1:
                    try:
                        last_diff, last_dist, _ = y_coord[y]
                    except KeyError:
                        y_coord[y] = [diff, dist, x]
                        continue
                    if diff < last_diff:
                        y_coord[y] = [diff, dist, x]
                    elif diff == last_diff and dist < last_dist:
                        y_coord[y] = [diff, dist, x]
        print "calc cost ", calc_cnt
        keys = y_coord.keys()
        keys.sort()
        for y in keys:
            x = y_coord[y][2]
            plot_xy.append([x, y])

    plot_xy = dog_last(plot_xy)
    return plot_xy
    # new_xy0, new_xy1 = [], []
    # last_seg = None
    # for i, seg in enumerate(plot_xy):
    #     if i > 0:
    #         nseg0, nseg1 = get_parallel(last_seg, seg, 20)
    #         new_xy0.append(nseg0)
    #         new_xy1.append(nseg1)
    #     last_seg = seg

    # main_show2(plot_xy, new_xy0, new_xy1)


def center_offset(road0, road1):
    """
    起点和终点偏移到路上
    :param road0: Road 目标道路
    :param road1: Road 待偏移到的道路
    :return:
    """
    # 当端点接近某路口时，需要偏移该端点，修正为路口
    bp, ep = road0.point_list[0], road0.point_list[-1]
    for pt in road1.cross_list:
        dist = get_dist(pt, bp)
        if 1e-5 < dist < 20:
            pt.cross = 0
            if pt.cross_name == road0.name:     # 说明与road0相交
                pos = pt.cross_other_seg + 1
            else:
                pos = 0
            pt_list = [pt]
            pt_list.extend(road0.point_list[pos:])
            road0.set_point_list(pt_list)
            road0.gene_segment()
            return

    for pt in road1.cross_list:
        dist = get_dist(pt, ep)
        if 1e-5 < dist < 20:
            pt.cross = 0
            if pt.cross_name == road0.name:  # 说明与road0相交
                pos = pt.cross_other_seg + 1
            else:
                pos = len(road0.point_list)
            pt_list = road0.point_list[:pos]
            pt_list.append(pt)
            road0.set_point_list(pt_list)
            road0.gene_segment()
            # print road0.name, "end point fix to ", road1.name, pt.px, pt.py
            return


def center_divide(road0, road1):
    bp0, ep0, bp1, ep1 = road0.point_list[0], road0.point_list[-1], road1.point_list[0], road1.point_list[-1]
    if bp0 == bp1 or bp0 == ep1 or ep0 == bp1 or ep0 == ep1:
        return
    for i, seg0 in enumerate(road0.seg_list):
        for j, seg1 in enumerate(road1.seg_list):
            if is_segment_cross(seg0, seg1):
                _, px, py = get_cross_point(seg0, seg1)
                cr0 = Point(px, py)
                cr0.cross, cr0.cross_name, cr0.cross_other_seg = 1, road1.name, j
                cr0.cross_seg = i
                bp, ep = seg0.begin_point, seg0.end_point
                w0, w1 = get_dist(cr0, bp), get_dist(cr0, ep)
                if w0 > 1e-5 and w1 > 1e-5:
                    road0.cross_list.append(cr0)

                cr1 = Point(px, py)
                cr1.cross, cr1.cross_name, cr1.cross_other_seg = 1, road0.name, i
                cr1.cross_seg = j
                bp, ep = seg1.begin_point, seg1.end_point
                w0, w1 = get_dist(cr1, bp), get_dist(cr1, ep)
                if w0 > 1e-5 and w1 > 1e-5:
                    road1.cross_list.append(cr1)
                return


def center_split(road):
    road_pt_list = []
    temp = []
    for pt in road.point_list:
        temp.append(pt)
        if pt.cross == 1:
            road_pt_list.append(temp)
            temp = [pt]
    road_pt_list.append(temp)

    road_list = []
    for pts in road_pt_list:
        road = Road(road.name, 0, -1)
        road.set_point_list(pts)
        road.gene_segment()
        road_list.append(road)
    return road_list


def center_split3(road):
    """
    将道路切分为THREAD米一段的路段
    最后一段小于100米时合并
    :param road: Road
    :return: road list
    """
    THREAD = 350
    road_seg_list = []
    temp = []
    dist = 0
    for seg in road.seg_list:
        d = get_segment_length(seg)
        last_dist = dist
        dist += d
        while dist > THREAD:
            left = THREAD - last_dist
            s0, seg = cut_from_segment(seg, left)
            temp.append(s0)
            road_seg_list.append(temp)
            temp = []
            dist -= THREAD
            last_dist = 0
        temp.append(seg)
    dist0 = 0
    for seg in temp:
        dist0 += get_segment_length(seg)
    if dist0 < 100 and len(road_seg_list) > 0:
        road_seg_list[-1].extend(temp)
    else:
        road_seg_list.append(temp)

    road_list = []
    for seg_list in road_seg_list:
        road = Road(road.name, -1, -1)
        pt_list = [seg_list[0].begin_point]
        for seg in seg_list:
            pt_list.append(seg.end_point)
        road.set_point_list(pt_list)
        road.gene_segment()
        road_list.append(road)
    return road_list


def center_simplify(road):
    """
    最后再做一次简化
    :param road:
    :return:
    """
    pts = road.point_list
    xy_list = []
    for pt in pts:
        xy_list.append([pt.px, pt.py])
    xy_list = dog_last(xy_list)
    r = Road(road.name, 0, -1)
    for xy in xy_list:
        pt = Point(xy[0], xy[1])
        r.add_point(pt)
    r.gene_segment()
    return r


def center3():
    """
    中心线最后分隔
    :return:
    """
    center_road = load_model2road('./road/center0.txt')
    new_center_road = center_road[:]
    center_road = []
    for road in new_center_road:
        center_road.append(center_simplify(road))
    new_center_road = []
    for road in center_road:
        new_center_road.extend(center_split3(road))
    # rid
    for i, road in enumerate(new_center_road):
        road.set_rid(i)
    save_road2model('./road/center1.txt', new_center_road)


def center_insert_cross(road):
    pt_list = []
    # split
    for i, pt in enumerate(road.point_list):
        pt_list.append(pt)
        last_cr = None
        for j, cr in enumerate(road.cross_list):
            if cr.cross_seg == i:
                if last_cr is None or get_dist(cr, last_cr) > 1e-5:
                    pt_list.append(cr)
                last_cr = cr
    road.set_point_list(pt_list)
    road.gene_segment()


def center0():
    """
    中心线的优化
    :return:
    """
    center_road = load_model2road('./road/center.txt')

    # 合并平行连接的道路
    for i, road0 in enumerate(center_road):
        for j, road1 in enumerate(center_road):
            if j < i:
                center_merge(road0, road1)
    # 交叉点
    for i, road0 in enumerate(center_road):
        for j, road1 in enumerate(center_road):
            if i != j:
                center_cross(road0, road1)

    for i, road0 in enumerate(center_road):
        for j, road1 in enumerate(center_road):
            if j < i:
                center_divide(road0, road1)
    print "divide 1"
    # save_road2model('./road/center0.txt', center_road)
    # return

    # 端点落到道路
    for i, road0 in enumerate(center_road):
        for j, road1 in enumerate(center_road):
            if i != j:
                center_offset(road0, road1)
    # save_road2model('./road/center0.txt', center_road)
    # return

    # 重新计算交叉点
    for road in center_road:
        road.cross_list = []
    for i, road0 in enumerate(center_road):
        for j, road1 in enumerate(center_road):
            if j < i:
                center_divide(road0, road1)
    print "divide 2"

    # cross list
    for road in center_road:
        center_insert_cross(road)

    new_center_road = []
    for road in center_road:
        new_center_road.extend(center_split(road))

    for i, road in enumerate(new_center_road):
        road.set_rid(i)

    save_road2model('./road/center0.txt', new_center_road)


def center_cross(road0, road1):
    """
    检查道路与其他道路的交叉，并且合并交叉点
    只有在道路尽头才会发生，因此和其他道路如有merge，应该不进行操作
    :param road0: Road
    :param road1: Road
    :return:
    """
    bp, ep = road0.point_list[0], road0.point_list[-1]
    min_dist = 1e10
    sel_seg = None
    for seg in road1.seg_list:
        dist = point2segment2(bp, seg)
        if dist < min_dist:
            min_dist, sel_seg = dist, seg
    if min_dist < 50:
        if road0.bs == 1:
            return
        if is_segment_cross(road0.seg_list[0], sel_seg) or \
                calc_include_angle2(road0.seg_list[0], sel_seg) > 0.8:
            return
        _, px, py = get_cross_point(road0.seg_list[0], sel_seg)
        new_point_list = [Point(px, py)]
        for pt in road0.point_list:
            new_point_list.append(pt)
        road0.set_point_list(new_point_list)
        road0.gene_segment()
        return

    min_dist = 1e10
    sel_seg = None
    for seg in road1.seg_list:
        dist = point2segment2(ep, seg)
        if dist < min_dist:
            min_dist, sel_seg = dist, seg
    if min_dist < 50:
        if road0.es == 1:
            return
        if is_segment_cross(road0.seg_list[-1], sel_seg) or \
                calc_include_angle2(road0.seg_list[-1], sel_seg) > 0.8:
            return
        _, px, py = get_cross_point(road0.seg_list[-1], sel_seg)
        road0.add_point(Point(px, py))
        road0.gene_segment()


def center_merge(road0, road1):
    """
    检查端点是否重合
    :return:
    """
    r0s0, r0s1 = road0.seg_list[0], road0.seg_list[-1]
    r1s0, r1s1 = road1.seg_list[0], road1.seg_list[-1]
    r0_bp, r0_ep = road0.point_list[0], road0.point_list[-1]
    r1_bp, r1_ep = road1.point_list[0], road1.point_list[-1]
    if get_dist(r0_bp, r1_ep) < 50 and calc_include_angle2(r0s0, r1s1) > 0.8:
        # 头尾相接，并且平行，说明是在同一条道路里面
        road1.add_point(r0_bp)
        road1.gene_segment()
        road1.es, road0.bs = 1, 1
    elif get_dist(r1_bp, r0_ep) < 50 and calc_include_angle2(r1s0, r0s1) > 0.8:
        road0.add_point(r1_bp)
        road0.gene_segment()
        road0.es, road1.bs = 1, 1
    elif get_dist(r0_bp, r1_bp) < 50 and calc_include_angle2(r0s0, r1s0) > 0.8:
        # 有时遇到单芯线
        new_point_list = [r1_bp]
        for pt in road0.point_list:
            new_point_list.append(pt)
        road0.set_point_list(new_point_list)
        road0.gene_segment()
        road0.bs, road1.es = 1, 1
    elif get_dist(r0_ep, r1_ep) < 50 and calc_include_angle2(r0s1, r1s1) > 0.8:
        road0.add_point(r1_ep)
        road0.gene_segment()
        road0.es, road1.bs = 1, 1


center3()
