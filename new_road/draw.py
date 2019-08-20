# -*- coding: utf-8 -*-
# @Time    : 2019/7/8 16:57
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : draw.py


import copy
import os
from Queue import Queue
from collections import defaultdict
from datetime import datetime, timedelta
from time import clock

import cx_Oracle
import matplotlib.pyplot as plt
import numpy as np

from geo import bl2xy, calc_dist, xy2bl
from refineMap import dog_last

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'
GRID = 5


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "analysis.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


def in_area(pt, area_pt):
    return calc_dist(pt, area_pt) < 200


@debug_time
def save_txt():
    fp = open("../data/yhtl_2.txt", 'w')
    conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
    cursor = conn.cursor()
    lp = [120.129157, 30.297211]
    rp = [120.083538, 30.291544]
    x0, y0 = bl2xy(lp[1], lp[0])
    x1, y1 = bl2xy(rp[1], rp[0])
    sql = "select vehicle_num, px, py, direction, speed_time from tb_gps_1805" \
          " where speed_time > :1 and speed_time < :2 and carstate = '0' order by speed_time"
    bt = datetime(2018, 5, 1, 12)
    et = bt + timedelta(hours=6)
    tup = (bt, et)
    cursor.execute(sql, tup)
    traces = defaultdict(list)
    for item in cursor:
        veh = item[0]
        px, py = map(float, item[1:3])
        angle = int(item[3])
        st = item[4].strftime("%Y-%m-%d %H:%M:%S")
        if rp[0] < px < lp[0] and rp[1] < py < lp[1]:
            x, y = bl2xy(py, px)
            line = "{2},{0:.2f},{1:.2f},{4},{3}\n".format(x, y, veh, st, angle)
            fp.write(line)
            traces[veh].append([x, y])
    cursor.close()
    conn.close()
    fp.close()


def load_txt():
    xy_list = []
    fp = open("../data/yhtl.txt")
    for line in fp.readlines():
        items = line.strip('\n').split(',')
        veh, x, y, st = items[:]
        xy_list.append([x, y])
    fp.close()
    return xy_list


def get_data():
    # for veh, trace in traces.items():
    #     if (in_area(trace[0], lpt) and in_area(trace[-1], rpt))\
    #             or (in_area(trace[0], rpt) and in_area(trace[-1], lpt)):
    #         line_trace[veh] = trace
    #         xy_list.extend(trace)
    grid = defaultdict(int)
    xy_list = load_txt()
    for item in xy_list:
        x, y = map(float, item[:])
        ipx, ipy = int(x / GRID), int(y / GRID)
        pos = ipx * 100000 + ipy
        grid[pos] += 1

    weight_grid = {}
    trim_grid = {}
    for pos, value in grid.items():
        x, y = int(pos / 100000) * GRID, (pos % 100000) * GRID
        if value >= 2:
            # xy_list.append([x, y])
            try:
                trim_grid[x][y] = 1
            except KeyError:
                trim_grid[x] = {y: 1}
            try:
                weight_grid[x][y] = value
            except KeyError:
                weight_grid[x] = {y: value}
    color = paint_color(trim_grid)
    filter_color(color)
    out_xy_list = []
    xy_list = []
    trim_list = []

    used_color = defaultdict(list)
    for x, c in color.items():
        for y, value in c.items():
            if value == 1:      # trim
                out_xy_list.append([x, y])
            elif value == 2:
                xy_list.append([x, y])
                used_color[x].append(y)
            elif value == 3:
                trim_list.append([x, y])
    print len(xy_list)

    line_list = []
    for x, y_list in used_color.items():
        s, w = .0, .0
        for y in y_list:
            s += y * weight_grid[x][y]
            w += weight_grid[x][y]
        s /= w
        line_list.append([x, s])
    line_list.sort(key=lambda t: t[0])

    line_list2 = []
    for x, y_list in used_color.items():
        y = np.mean(y_list)
        line_list2.append([x, y])
    line_list2.sort(key=lambda t: t[0])

    line_list3 = []
    line_len = len(line_list)
    for i, item in enumerate(line_list2):
        l = max(0, i - 10)
        r = min(line_len, i + 11)
        vec = line_list[l: r]
        v = np.mean(vec, axis=0)
        line_list3.append([item[0], v[1]])

    return xy_list, out_xy_list, trim_list, line_list, line_list2, line_list3


def bfs(grid, x, y, color_grid):
    q = Queue()
    q.put([x, y])
    color_grid[x][y] = 2
    d_list = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            d_list.append([i, j])
    # d_list = [[0, 1], [0, -1], [1, -2], [1, -1], [1, 0], [1, 1], [1, 2], [-1, -2],
    #           [-1, -1], [-1, 0], [-1, 1], [-1, 2]]
    while not q.empty():
        pos = q.get()
        x, y = pos[:]
        for d in d_list:
            dx, dy = d[:]
            nx, ny = x + dx * GRID, y + dy * GRID
            try:
                if grid[nx][ny] == 1 and color_grid[nx][ny] != 2:
                    q.put([nx, ny])
                    color_grid[nx][ny] = 2
            except KeyError:
                pass


def paint_col(color_grid, x, value):
    for y in color_grid[x].keys():
        if color_grid[x][y] == 2:
            color_grid[x][y] = value


def filter_color(color_grid):
    # 1: outside
    # 2: inside
    # 3: trim cross line
    width = {}
    up_lower = {}
    x_list = sorted(color_grid.keys())
    for x in x_list:
        y_list = color_grid[x].keys()
        y_list.sort()
        max_y, min_y = 0, 0
        for y in y_list:
            if color_grid[x][y] == 2:
                min_y = y
                break
        for y in reversed(y_list):
            if color_grid[x][y] == 2:
                max_y = y
                break
        up_lower[x] = [min_y, max_y]
        w = max_y - min_y
        width[x] = w

    med_w = np.median(width.values())
    s = .0
    trim_list = []      # cols to be trim
    for i, x in enumerate(x_list):
        if i >= 10:
            last_x = x_list[i - 10]
            s = s - width[last_x] + width[x]
            ave_w = s / 10
            if width[x] >= ave_w * 1.25 and width[x] >= 1.25 * med_w:
                # paint_col(color_grid, x, 3)
                trim_list.append(x)
                s = s - width[x] + ave_w
        else:
            s += width[x]

    trim_set = set(trim_list)
    for x in trim_list:
        ul_list = []
        dx = x
        while True:
            dx -= GRID
            if dx in trim_set:
                continue
            try:
                ul_list.append(up_lower[dx])
            except KeyError:
                break
            if len(ul_list) >= 10:
                break
        dx = x
        while True:
            dx += GRID
            if dx in trim_set:
                continue
            try:
                ul_list.append(up_lower[dx])
            except KeyError:
                break
            if len(ul_list) >= 20:
                break
        ul_vec = np.array(ul_list)
        u, l = np.mean(ul_vec, axis=0)[:]
        u, l = u - GRID, l + GRID         # loosen
        for y, value in color_grid[x].items():
            if value == 2 and not u <= y <= l:
                color_grid[x][y] = 3


def paint_color(grid):
    color_grid = copy.copy(grid)
    bx = sorted(grid.keys())[0]
    by = sorted(grid[bx])[0]
    bfs(grid, bx, by, color_grid)
    bx = 74800
    by = sorted(grid[bx])[0]
    bfs(grid, bx, by, color_grid)
    return color_grid


def save_road(xy_list):
    fp = open("road.txt", 'w')
    bl_list = []
    for x, y in xy_list:
        lat, lng = xy2bl(x, y)
        bl_list.append("{0:.6f},{1:.6f}".format(lng, lat))
    str_line = ";".join(bl_list)
    fp.write(str_line)
    fp.close()


def main():
    xy_list, out_xy_list, trim_list, line, line2, line3 = get_data()
    x_list, y_list = zip(*xy_list)
    plt.plot(x_list, y_list, marker='+', linestyle='', alpha=.3)
    x_list, y_list = zip(*out_xy_list)
    plt.plot(x_list, y_list, marker='+', linestyle='', color='r')
    x_list, y_list = zip(*trim_list)
    plt.plot(x_list, y_list, marker='+', linestyle='', color='orange', alpha=.3)

    x_list, y_list = zip(*line3)
    plt.plot(x_list, y_list, linestyle='-', linewidth=1, color='b', alpha=.3)
    # x_list, y_list = zip(*line2)
    # plt.plot(x_list, y_list, linestyle='-', linewidth=1, color='k')
    line4 = dog_last(line3)
    save_road(line4)
    x_list, y_list = zip(*line4)
    plt.plot(x_list, y_list, linestyle='-', linewidth=1, color='k', alpha=1)

    plt.xlim(72500, 73314)
    plt.ylim(85200, 85600)
    plt.show()


def draw_pt():
    xy_list = load_txt()
    x_list, y_list = zip(*xy_list)
    plt.plot(x_list, y_list, marker='+', linestyle='', alpha=.1)
    plt.show()


save_txt()
# save_txt()
