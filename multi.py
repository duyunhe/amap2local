# -*- coding: utf-8 -*-
# @Time    : 2018/10/8 11:47
# @Author  : 
# @简介    : 多进程跑center程序
# @File    : multi.py

import math
import multiprocessing

import numpy as np

from refineMap import load_model, xylist2polyline, polyline2path, save_model


def work(idx, global_lock, road_list, return_list):
    """ 
    :param idx: 序号
    :param global_lock: 全局锁
    :param road_list: 待处理的道路
    :param return_list: 返回的center line道路
    :return: 
    """
    for name, road in road_list:
        xy_list = grid_center_line(global_lock, name, road)
        polyline = xylist2polyline(xy_list)
        center_line = {'name': name, 'polyline': polyline}
        return_list.append(center_line)


def get_diff(seg_list0, seg_list1, point):
    min_dist0 = 1e10
    for seg in seg_list0:
        dist = point2segment(point, seg[0], seg[1])
        min_dist0 = min(dist, min_dist0)
    min_dist1 = 1e10
    for seg in seg_list1:
        dist = point2segment(point, seg[0], seg[1])
        min_dist1 = min(dist, min_dist1)
    return math.fabs(min_dist0 - min_dist1), min_dist0 + min_dist1


def coord2xy(coord):
    """
    :param coord: u'x,y'
    :return: [x,y]
    """
    x, y = map(float, coord.split(',')[0:2])
    return [x, y]


def line2grid(segment_point0, segment_point1):
    x0, y0 = segment_point0[0:2]
    x1, y1 = segment_point1[0:2]

    dx, dy = x1 - x0, y1 - y0
    # 是否用x步进
    if dx == 0:
        x_step = False
    else:
        k = dy / dx
        x_step = math.fabs(k) < 1
    grid = []
    if x_step:
        if x0 > x1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        k = dy / dx
        x, y = int(x0), y0
        while x <= x1:
            grid.append([x, int(y)])
            # grid.append([x, int(y) + 1])
            x, y = x + 1, y + k
    else:
        if y0 > y1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        k = dx / dy
        x, y = x0, int(y0)
        while y <= y1:
            grid.append([int(x), y])
            # grid.append([int(x), y + 1])
            x, y = x + k, y + 1
    return grid


def grid_center_line(global_lock, road_name, road_list):
    with global_lock:
        print road_name, "begin grid"
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
            pt_list.append([px, py])
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
        with global_lock:
            print road_name, "calc cost ", calc_cnt
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
        with global_lock:
            print road_name, "calc cost ", calc_cnt
        keys = y_coord.keys()
        keys.sort()
        for y in keys:
            x = y_coord[y][2]
            plot_xy.append([x, y])

    plot_xy = dog_last(plot_xy)
    return plot_xy


def point2segment(point, segment_point0, segment_point1):
    """
    :param point: point to be matched, [px(double), py(double)] 
    :param segment_point0: segment [px, py]
    :param segment_point1: [px, py]
    :return: dist from point to segment
    """
    x, y = point[0:2]
    x0, y0 = segment_point0[0:2]
    x1, y1 = segment_point1[0:2]
    cr = (x1 - x0) * (x - x0) + (y1 - y0) * (y - y0)
    if cr <= 0:
        return math.sqrt((x - x0) * (x - x0) + (y - y0) * (y - y0))
    d2 = (x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0)
    if cr >= d2:
        return math.sqrt((x - x1) * (x - x1) + (y - y1) * (y - y1))
    r = cr / d2
    px = x0 + (x1 - x0) * r
    py = y0 + (y1 - y0) * r
    return math.sqrt((x - px) * (x - px) + (y - py) * (y - py))


def dog_last(path):
    """
    简化道路，道格拉斯算法
    :param path: [[x,y]...[x,y]]
    :return: 
    """
    if len(path) == 2:
        return path
    max_dist, sel = -1e10, -1
    pt0, pt1 = path[0], path[-1]

    for i, pt in enumerate(path):
        dist = point2segment(pt, pt0, pt1)
        if dist > max_dist:
            max_dist, sel = dist, i
    new_path = []
    if max_dist > 2:
        path0, path1 = dog_last(path[:sel + 1]), dog_last(path[sel:])
        new_path.extend(path0[:-1])
        new_path.extend(path1)
    else:
        new_path = [pt0, pt1]
    return new_path


if __name__ == "__main__":
    pro_list = []
    lock = multiprocessing.Lock()

    road_list = load_model('./road/merge_xy.txt')
    parse_list = []
    road_dict = {}
    for road_info in road_list:
        name = road_info['name']
        try:
            road_dict[name].append(road_info)
        except KeyError:
            road_dict[name] = [road_info]

    # 确定要处理的数据
    temp_list = load_model('./road/center.txt')
    exist_road = []
    for road_info in temp_list:
        name = road_info['name']
        exist_road.append(name)

    for name, road_list in road_dict.iteritems():
        if name in exist_road:
            continue
        parse_list.append([name, road_list])

    manager = multiprocessing.Manager()
    ret_list = manager.list()
    # for road in temp_list:
    #     ret_list.append(road)
    for i in range(12):
        p = multiprocessing.Process(target=work, args=(i, lock, parse_list[i::12], ret_list))
        # 加锁，并行处理
        p.daemon = True
        pro_list.append(p)
        p.start()
        # 多进程开始
    for p in pro_list:
        p.join()
        # 多进程等待结束
    print "ALL END"
    center_list = temp_list
    for road in ret_list:
        center_list.append(road)
    save_model('./road/new_center.txt', center_list)
