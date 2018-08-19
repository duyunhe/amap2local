# -*- coding: utf-8 -*-
# @Time    : 2018/7/26 17:06
# @Author  : 
# @简介    : 
# @File    : plotMap.py

import matplotlib.pyplot as plt
from saveMap import raw2model, test_model
import json
from geo import bl2xy


def main():
    road_list = test_model()
    for road in road_list:
        x, y = zip(*road)
        plt.plot(x, y)
    plt.show()


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


def main_show2():
    """
    显示地图
    :return: 
    """
    fig1 = plt.figure(figsize=(12, 6))
    ax = fig1.add_subplot(111)
    filename = './road/split.txt'
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
        plt.plot(x_list, y_list, marker='o', markersize=5)

    plt.xlim(75550, 78948)
    plt.ylim(83080, 84958)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    plt.savefig("road.png", dpi=200)
    plt.show()


main_show2()
