# -*- coding: utf-8 -*-
# @Time    : 2018/7/25 18:28
# @Author  : 
# @简介    : 
# @File    : saveMap.py

from time import clock


way_dict = {}

fp = open('road.txt')
while True:
    line = fp.readline()
    if line == '':
        break
    data_index, road_cnt = line.split(',')
    print data_index
    road_cnt = int(road_cnt)
    for i in range(road_cnt):
        line = fp.readline()
        try:
            item = line.strip('\n').split(',')
            road, ort = item[1:3]
        except ValueError:
            road, ort = item[1], ''
        road_desc = road + ort
        line = fp.readline()
        coords = line.strip('\n').split(';')
        for coord in coords:
            x, y = map(float, coord.split(','))



