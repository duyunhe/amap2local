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


def path2polyline(path):
    return ';'.join(path)


def coord2xy(coord):
    lng, lat = map(float, coord.split(',')[0:2])
    px, py = bl2xy(lat, lng)
    return px, py


def process(coord, path_list):
    cx, cy = coord2xy(coord)
    cross = False
    min_dist, min_pt = 1e10, None
    for path in path_list:
        path_dist, path_pt = 1e10, None
        for pt in path:
            px, py = coord2xy(pt)
            dist = calc_dist([cx, cy], [px, py])
            if dist == 0:
                cross = True
                continue
            if dist < path_dist:
                path_dist, path_pt = dist, pt
        if path_dist < min_dist:
            min_dist, min_pt = path_dist, path_pt
    if cross:
        print 'cross', min_dist, min_pt
    return cross, min_dist, min_pt


def merge():
    road_temp = {}
    road_data = load_model('./road/road.txt')
    for road in road_data:
        pl = road['polyline']
        name = road['name']
        coords = pl.split(';')
        path = []
        for crd in coords:
            path.append(crd)
        try:
            road_temp[name].append(path)
        except KeyError:
            road_temp[name] = [path]

    # for ... brute
    road_data = []

    for road, path_list in road_temp.iteritems():
        print road
        merge_path_list = []
        l = len(path_list)
        prev, suc = [-1] * l, [-1] * l
        for i, p0 in enumerate(path_list):
            for j, p1 in enumerate(path_list):
                if p0[0] == p1[-1]:
                    prev[i] = j
                    suc[j] = i
                elif p0[-1] == p1[0]:
                    prev[j] = i
                    suc[i] = j

        idx_list = []
        for i in range(l):
            if prev[i] == -1:
                idx = [i]
                j = suc[i]
                while j != -1:
                    idx.append(j)
                    j = suc[j]
                idx_list.append(idx)
                m_path = []
                for j, t in enumerate(idx):
                    if j != 0:
                        m_path.extend(path_list[t][1:])
                    else:
                        m_path.extend(path_list[t])
                merge_path_list.append(m_path)
        print idx_list
        for path in merge_path_list:
            road_info = {'name': road, 'polyline': path2polyline(path)}
            road_data.append(road_info)

    # js = json.dumps(road_info)
    js = json.dumps(road_data, ensure_ascii=False).encode('utf-8')
    fp = open('./road/merge.txt', 'w')
    fp.write(js)
    fp.write('\n')
    fp.close()


def main():
    road_info = {}
    road_data = load_model('./road/road.txt')
    for road in road_data:
        pl = road['polyline']
        name = road['name']
        coords = pl.split(';')
        path = []
        for crd in coords:
            path.append(crd)
        try:
            road_info[name].append(path)
        except KeyError:
            road_info[name] = [path]

    for road, path_list in road_info.iteritems():
        for path in path_list:
            for road_c, path_list_c in road_info.iteritems():
                if road == road_c:
                    continue
                print road, road_c
                p0, p1 = path[0], path[-1]
                cross, dist, pt = process(p0, path_list_c)
                cross, dist, pt = process(p1, path_list_c)


def build():
    nodes = {}

    road_data = load_model('./road/road.txt')
    for road in road_data:
        pl = road['polyline']
        name = road['name']
        coords = pl.split(';')
        for crd in coords:
            try:
                nodes[crd].add(name)
            except KeyError:
                nodes[crd] = {name}

    road_split_data = []
    for road in road_data:
        path = []
        pl = road['polyline']
        name = road['name']
        coords = pl.split(';')
        last_road = ""

        for crd in coords:
            path.append(crd)
            if len(nodes[crd]) > 1:
                new_road = None
                for n in nodes[crd]:
                    if n != name:
                        new_road = n
                if len(path) > 0:
                    ort = u"{0},{1}".format(last_road, new_road)
                    last_road = new_road
                    pll = path2polyline(path)
                    path = [crd]
                    road_info = {'name': name, 'ort': ort, 'polyline': pll}
                    road_split_data.append(road_info)

        ort = u"{0},{1}".format(last_road, "")
        pll = path2polyline(path)
        road_info = {'name': name, 'ort': ort, 'polyline': pll}
        road_split_data.append(road_info)

    js = json.dumps(road_split_data, ensure_ascii=False).encode('utf-8')
    fp = open('./road/split.txt', 'w')
    fp.write(js)
    fp.write('\n')
    fp.close()


build()
