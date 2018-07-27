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


def main3():
    fig1 = plt.figure(figsize=(12, 6))
    ax = fig1.add_subplot(111)
    way_nodes = load_model()
    for road, item in way_nodes.iteritems():
        for ort, path in item.iteritems():
            for seg in path:
                x, y = zip(*seg)
                plt.plot(x, y)
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.05, top=0.96)
    plt.savefig("road", dpi=200)
    plt.show()


# main()
main3()
