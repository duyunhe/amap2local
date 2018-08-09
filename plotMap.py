# -*- coding: utf-8 -*-
# @Time    : 2018/7/26 17:06
# @Author  : 
# @简介    : 
# @File    : plotMap.py

import matplotlib.pyplot as plt
from saveMap import raw2model, test_model, load_model


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


def main_show():
    """
    显示地图
    :return: 
    """
    fig1 = plt.figure(figsize=(12, 6))
    ax = fig1.add_subplot(111)
    filename = './road/merge_network.txt'
    way_nodes = load_model(filename)
    for road, path in way_nodes.iteritems():
        # print road
        road_name, road_type, road_ort = road.split(',')
        for seg in path:
            x, y = zip(*seg)
            if road_name == '虎跑路' and road_type == '道路':
                plt.plot(x, y, alpha=1, color='r', linewidth=2)
            elif road_name == '南山路' and road_type == '道路':
                plt.plot(x, y, alpha=1, color='b', linewidth=2)
            else:
                plt.plot(x, y, alpha=.5, color='k')

    plt.xlim(52186, 110263)
    plt.ylim(66484, 98279)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    plt.savefig("road.png", dpi=200)
    plt.show()


# main()
main_show()
