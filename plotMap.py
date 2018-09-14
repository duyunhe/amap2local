# -*- coding: utf-8 -*-
# @Time    : 2018/7/26 17:06
# @Author  : 
# @简介    : 
# @File    : plotMap.py

import json

import matplotlib.pyplot as plt

from geo import bl2xy, get_cross_point
from saveMap import raw2model, test_model


def main():
    road_list = test_model()
    for road in road_list:
        x, y = zip(*road)
        plt.plot(x, y)
    plt.show()


def plot_path(path, c):
    if path == u'':
        return
    xy_items = path.split(';')
    x_list, y_list = [], []
    for xy in xy_items:
        x, y = map(float, xy.split(',')[0:2])
        # x, y = bl2xy(lat, lng)
        x_list.append(x)
        y_list.append(y)
    plt.plot(x_list, y_list, linestyle='', color=c, marker='o', markersize=5)
    # plt.plot(x_list, y_list, color='k')


def main2():
    road_list = raw2model()
    print 'total ', len(road_list)
    for road in road_list:
        for path in road:
            x, y = zip(*path)
            plt.plot(x, y)
    plt.show()


def load_model(filename):
    fp = open(filename)
    line = fp.readline().strip('\n')
    data = json.loads(line)
    fp.close()
    return data

# main()
# main_show()


def draw_seg(seg_list):
    last_seg = None
    cross_point = []
    for seg in seg_list:
        x_list, y_list = zip(*seg)
        plt.plot(x_list, y_list, marker='None', color='k', linestyle='-')
        if last_seg is not None:
            d, px, py = get_cross_point(seg, last_seg)
            cross_point.append([px, py])
            # plt.text(x_list[0] + 5, y_list[0] + 5, "{0:2f}".format(d))
        last_seg = seg
    x_list, y_list = zip(*cross_point)
    plt.plot(x_list, y_list, marker='o', color='k', linestyle='', markersize=3)


def main_show2(xy_list, seg_list0, seg_list1):
    """
    显示地图
    :return: 
    """
    fig1 = plt.figure(figsize=(12, 6))
    ax = fig1.add_subplot(111)
    filename = './road/merge.txt'
    data = load_model(filename)
    for road in data:
        pl = road['polyline']
        xy_items = pl.split(';')
        x_list, y_list = [], []
        for xy in xy_items:
            lng, lat = map(float, xy.split(',')[0:2])
            x, y = bl2xy(lat, lng)
            x_list.append(x)
            y_list.append(y)
        # plt.plot(x_list, y_list, marker='o', markersize=5)
        plt.plot(x_list, y_list)
    center_x, center_y = zip(*xy_list)
    plt.plot(center_x, center_y, marker='o', linestyle='-', markersize=2)
    draw_seg(seg_list0)
    draw_seg(seg_list1)
    # plt.xlim(75550, 78948)
    # plt.ylim(83080, 84958)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    # plt.savefig("road.png", dpi=200)
    plt.show()


def main_show():
    """
    显示地图
    :return: 
    """
    fig1 = plt.figure(figsize=(12, 6))
    ax = fig1.add_subplot(111)
    filename = './road/merge.txt'
    data = load_model(filename)
    for road in data:
        pl = road['polyline']
        xy_items = pl.split(';')
        x_list, y_list = [], []
        for xy in xy_items:
            lng, lat = map(float, xy.split(',')[0:2])
            x, y = bl2xy(lat, lng)
            x_list.append(x)
            y_list.append(y)
        # plt.plot(x_list, y_list, marker='o', markersize=5)
        plt.plot(x_list, y_list)

    plt.xlim(75550, 78948)
    plt.ylim(83080, 84958)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    # plt.savefig("road.png", dpi=200)
    plt.show()


def main_show1():
    """
    显示地图
    :return: 
    """
    fig1 = plt.figure(figsize=(12, 6))
    ax = fig1.add_subplot(111)

    filename = './road/road.txt'
    data = load_model(filename)
    for road in data:
        pl = road['polyline']
        # rid = road['rid']
        xy_items = pl.split(';')
        x_list, y_list = [], []
        for i, xy in enumerate(xy_items):
            x, y = map(float, xy.split(',')[0:2])
            # x, y = bl2xy(lat, lng)
            x_list.append(x)
            y_list.append(y)
            # plt.text(x + 5, y + 5, str(i))
        # plt.plot(x_list, y_list, color='darkblue')
        plt.plot(x_list, y_list, marker='', markersize=2, color='darkblue', linewidth=1)
        # plt.text(x_list[0], y_list[0], str(rid))

        # if rid == 1:
        #     try:
        #         entrance = road['entrance']
        #         plot_path(entrance, 'r')
        #         ext = road['exit']
        #         plot_path(ext, 'g')
        #     except KeyError:
        #         pass

    plt.xlim(75550, 78948)
    plt.ylim(83080, 84958)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    # plt.savefig("road.png", dpi=200)
    plt.show()


main_show1()
