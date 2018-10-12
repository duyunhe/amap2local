# -*- coding: utf-8 -*-
# @Time    : 2018/10/9 10:12
# @Author  : 
# @简介    : 整个流程
# @File    : test_all.py


from geo import bl2xy
from refineMap import load_model, save_model, polyline2xylist, xylist2polyline


# main1()
# merge()
# trans()


def trans_txt():
    road_data = load_model('./road/cw_wh.txt')
    for road in road_data:
        polyline = road['polyline']
        bllist = polyline2xylist(polyline)
        xylist = []
        for lng, lat in bllist:
            x, y = bl2xy(lat, lng)
            xylist.append([x, y])
        road['polyline'] = xylist2polyline(xylist)
    save_model('./road/add.txt', road_data)


print "{0:0>8}".format(hex(200)[2:])
