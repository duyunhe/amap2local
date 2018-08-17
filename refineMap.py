# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 15:26
# @Author  : 
# @简介    : segment去重
# @File    : refineMap.py

import json
from geo import bl2xy, calc_dist


def load_model(filename):
    fp = open(filename)
    line = fp.readline().strip('\n')
    data = json.loads(line)
    fp.close()
    return data


def main():
    road_info = {}
    node = {}           # check road link

    road_data = load_model('./road/road.txt')
    for road in road_data:
        pl = road['polyline']
        name = road['name']
        coords = pl.split(';')
        path = []
        for crd in coords:
            try:
                node[crd].add(name)
            except KeyError:
                node[crd] = set()
                node[crd].add(name)
            lng, lat = map(float, crd.split(',')[0:2])
            px, py = bl2xy(lat, lng)
            path.append([px, py])
        try:
            road_info[name].append(path)
        except KeyError:
            road_info[name] = [path]

    road_link = {}
    for c, road_set in node.iteritems():
        temp = []
        for r in road_set:
            temp.append(r)
        if len(road_set) == 2:
            try:
                road_link[temp[0]].add(temp[1])
            except KeyError:
                road_link[temp[0]] = set()
                road_link[temp[0]].add(temp[1])

            try:
                road_link[temp[1]].add(temp[0])
            except KeyError:
                road_link[temp[1]] = set()
                road_link[temp[1]].add(temp[0])
    for r, link in road_link.iteritems():
        print r
        for l in link:
            print l,
        print '\n'

main()


