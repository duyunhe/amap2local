# -*- coding: utf-8 -*-
# @Time    : 2018/7/26 17:06
# @Author  : 
# @简介    : 
# @File    : plotMap.py

import matplotlib.pyplot as plt
from saveMap import raw2model, test_model


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


def load_model():
    """
    读取道路数据，存放至way_nodes
    way_nodes: {road: path_list}
    path_list: [[px, py], [px, py]...]
    :return: way_nodes
    """
    way_nodes = {}  # 存放修改后的数据
    fp = open('./road/road_network.txt', 'r')
    while True:
        line = fp.readline().strip('\n')
        if line == '':
            break
        _, road, ort, road_cnt = line.split(',')
        road_cnt = int(road_cnt)
        road = road + ',' + ort
        way_nodes[road] = []
        for i in range(road_cnt):
            seg = []
            line = fp.readline().strip('\n')
            crds = line.split(';')
            for crd in crds:
                x, y = map(float, crd.split(','))
                seg.append([x, y])
            way_nodes[road].append(seg)
    fp.close()
    return way_nodes


def main3():
    fig1 = plt.figure(figsize=(12, 6))
    ax = fig1.add_subplot(111)
    way_nodes = load_model()
    for road, path in way_nodes.iteritems():
        # print road
        r = road[0:9]
        for seg in path:
            x, y = zip(*seg)
            if r == '虎跑路':
                plt.plot(x, y, alpha=1, color='r', linewidth=2)
            else:
                plt.plot(x, y, alpha=.5, color='k')

    plt.xlim(52186, 110263)
    plt.ylim(66484, 98279)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    plt.savefig("road.png", dpi=200)
    plt.show()


# main()
# main3()