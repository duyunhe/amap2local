# -*- coding: utf-8 -*-
# @Time    : 2019/8/7 18:53
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : dba_scan.py


from collections import defaultdict
from datetime import datetime
from math import fabs, atan2, pi
from time import clock

import matplotlib.pyplot as plt
from queue import Queue
from sklearn.neighbors import KDTree

from geo import calc_dist


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "dba_scan.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


class TaxiData(object):
    def __init__(self, veh, x, y, angle, speed_time):
        self.x, self.y, self.angle, self.speed_time = x, y, angle, speed_time
        self.veh = veh
        self.ort = self.angle           # angle in fact

    def __sub__(self, other):
        return (self.speed_time - other.speed_time).total_seconds()


def data_dist(d0, d1):
    return calc_dist([d0.x, d0.y], [d1.x, d1.y])


def data_angle(last_data, cur_data):
    dy, dx = cur_data.y - last_data.y, cur_data.x - last_data.x
    angle = 90 - 180 * atan2(dy, dx) / pi
    if angle < 0:
        angle += 360
    if angle >= 360:
        angle -= 360
    return angle


@debug_time
def split_trace(xy_dict):
    trace_list = []
    for veh, gps_list in xy_dict.items():
        last_data = None
        trace = []
        for data in gps_list:
            if last_data:
                dist = data_dist(data, last_data)
                if dist < 20:
                    continue
                itv = data - last_data
                if itv >= 120:
                    if len(trace) > 2:
                        trace_list.append(trace)
                    trace = [data]
                else:
                    trace.append(data)
            last_data = data
        if len(trace) > 2:
            trace_list.append(trace)
    return trace_list


def calc_trace_angle(trace_list, merge_list):
    """
    将trace列表转换为xy坐标值列表，附带计算方向角
    为了计算index
    :param trace_list: list(list(TaxiData))
    :param merge_list: 原始为空的 list([x, y, angle]) 待转换
    :return: 
    """
    for trace in trace_list:
        for i, data in enumerate(trace):
            if i == len(trace) - 1:
                ort = data.angle
            else:
                ort = data_angle(data, trace[i + 1])
            data.ort = ort
            # if 75.0 < ort < 105:
            merge_list.append([data.x, data.y, ort])


def load_txt():
    """
    :return: all_list list[x, y, angle]  reverse index
    """
    xy_dict = defaultdict(list)
    fp = open("../data/yhtl.txt")
    idx = 0
    for line in fp.readlines():
        items = line.strip('\n').split(',')
        veh, x, y, angle, st = items[:]
        x, y = float(x), float(y)
        st = datetime.strptime(st, "%Y-%m-%d %H:%M:%S")
        angle = float(angle)
        data = TaxiData(veh, x, y, angle, st)
        xy_dict[veh].append(data)
        idx += 1
        if idx >= 50000:
            break
    fp.close()
    rev_index = {}
    all_list = []
    trace_list = split_trace(xy_dict)
    calc_trace_angle(trace_list, all_list)
    return all_list, rev_index


def mean_angle(angle_list):
    ans1, ans4, ans23 = 0, 0, 0
    n1, n4, n23 = 0, 0, 0
    for i, angle in enumerate(angle_list):
        if 0 <= angle < 90:
            ans1, n1 = ans1 + angle, n1 + 1
        elif 270 <= angle < 360:
            ans4, n4 = ans4 + angle, n4 + 1
        else:
            ans23, n23 = ans23 + angle, n23 + 1
    if n1 > 0 and n4 > 0:
        t = (((ans1 / n1) + 360) * n1 + ans4) / (n1 + n4)
        if t >= 360:
            t -= 360
        return t
    else:
        return (ans1 + ans23 + ans4) / (n1 + n23 + n4)


def draw_pt(labels, data_list):
    n = len(labels)
    x_list, y_list, angle_list = zip(*data_list)
    pts_dict = defaultdict(list)
    angle_dict = defaultdict(list)
    for i in range(n):
        pts_dict[labels[i]].append([x_list[i], y_list[i]])
        angle_dict[labels[i]].append(angle_list[i])

    colors = ['pink', 'orange', 'y',
              'blue', 'c', 'g', 'lime', 'red']
    for label, pt_list in pts_dict.items():
        if label == -2 or len(pt_list) < 30:
            draw_points(pt_list, '+', 'k', 0.3)
        else:
            angle_list = angle_dict[label]
            a = mean_angle(angle_list)
            idx = int(a / 45)
            # print a
            draw_points(pt_list, 'o', colors[idx], .8)


def draw_points(xy_list, marker, color, alpha):
    if len(xy_list) == 0:
        return
    x_list, y_list = zip(*xy_list)
    plt.plot(x_list, y_list, marker=marker, color=color, linestyle='', alpha=alpha)


def near_angle(a0, a1, delta):
    dif = fabs(a0 - a1)
    return dif < delta or dif > 360 - delta


def search_bf(ind, angle_list, label_list, init_pos, radius, count_thread, label_index):
    """
    :param ind: 
    :param angle_list:  
    :param label_list: 
    :param radius: A  anchor min radius
    :param init_pos: 
    :param count_thread: B min cluster point number
    :param label_index: 当前的index
    :return: 
    """
    que = Queue()
    anchor_cnt = 0
    que.put(init_pos)
    label_list[init_pos] = -2  # mark as visited
    # print init_pos
    while not que.empty():
        ci = que.get()
        # print cur
        near_list = []
        for i in ind[ci]:
            if near_angle(angle_list[i], angle_list[ci], 15):
                near_list.append(i)
        if len(near_list) >= count_thread:
            anchor_cnt += 1
            label_list[ci] = label_index
            for i in near_list:
                if label_list[i] == -1:
                    label_list[i] = -2
                    que.put(i)
    return anchor_cnt


@debug_time
def build_kdtree(data_list, A):
    x_list, y_list, a_list = zip(*data_list)
    data_list = []
    for i, a in enumerate(a_list):
        try:
            data_list.append((x_list[i], y_list[i], a_list[i]))
        except IndexError:
            print a

    x_list, y_list, a_list = zip(*data_list)
    xy_list = zip(x_list, y_list)
    kdt = KDTree(xy_list, leaf_size=10)
    ind = kdt.query_radius(X=xy_list, r=A)

    return ind, data_list


@debug_time
def DBA_SCAN(data_list, A, B):
    """
    :param data_list: list([x, y, angle])
    :param A: min radius 
    :param B: points count thread
    :return: 
    """
    n = len(data_list)
    ind, data_list = build_kdtree(data_list, A)
    _, _, angle_list = zip(*data_list)
    labels = [-1] * n
    li = 0      # label index
    for i in range(n):
        if labels[i] == -1:     # unvisited
            if search_bf(ind, angle_list, labels, i, A, B, li) > 0:
                li += 1
    return labels


def main():
    plt.xlim(72576, 76484)
    plt.ylim(84367, 86846)
    data_list, rev_index = load_txt()
    labels = DBA_SCAN(data_list, 30, 20)
    draw_pt(labels, data_list)
    plt.show()


main()
