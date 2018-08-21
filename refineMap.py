# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 15:26
# @Author  : 
# @简介    : segment去重
# @File    : refineMap.py

import json

from DBConn import oracle_util
from geo import bl2xy, xy2bl, calc_dist, point2segment


def save_model(filename, road_data):
    js = json.dumps(road_data, ensure_ascii=False).encode('utf-8')
    fp = open(filename, 'w')
    fp.write(js)
    fp.write('\n')
    fp.close()


def load_model(filename):
    fp = open(filename)
    line = fp.readline().strip('\n')
    data = json.loads(line)
    fp.close()
    return data


def path2polyline(path):
    return ';'.join(path)


def polyline2path(pll):
    items = pll.split(';')
    return items


def coord2xy(coord):
    lng, lat = map(float, coord.split(',')[0:2])
    px, py = bl2xy(lat, lng)
    return [px, py]


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


def doglas(path):
    if len(path) == 2:
        return [path]
    max_dist, sel = 0, -1
    pt0, pt1 = coord2xy(path[0]), coord2xy(path[-1])

    for i, str_pt in enumerate(path):
        pt = coord2xy(str_pt)
        dist = point2segment(pt, pt0, pt1)
        if dist > max_dist:
            max_dist, sel = dist, i
    path_list = []
    if max_dist > 20:
        path0, path1 = doglas(path[:sel + 1]), doglas(path[sel:])
        path_list.extend(path0)
        path_list.extend(path1)
    else:
        path_list.append(path)
    return path_list


def refine_road(road):
    pl = road['polyline']
    path = polyline2path(pl)
    sp_path = doglas(path)
    return sp_path


def simplify():
    road_data = load_model('./road/split.txt')
    new_data = []
    for road in road_data:
        name = road['name']
        if True:
            road_paths = refine_road(road)
            for i, path in enumerate(road_paths):
                new_road = {'name': name, 'ort': road['ort'] + ',{0}'.format(i),
                            'polyline': path2polyline(path)}
                new_data.append(new_road)
        # new_data.append(road)
    save_model('./road/simply.txt', new_data)


def split_road(road):
    path = polyline2path(road['polyline'])
    temp_length = 0
    last_pt, last_coord = None, None
    path_list = []
    new_path = []
    for coord in path:
        pt = coord2xy(coord)
        if last_pt is None:
            new_path.append(coord)
            last_pt, last_coord = pt, coord
            continue
        dist = calc_dist(last_pt, pt)
        temp_length += dist
        if temp_length > 400:   # divide
            x, y = (last_pt[0] + pt[0]) / 2, (last_pt[1] + pt[1]) / 2
            lat, lng = xy2bl(x, y)
            lat, lng = round(lat, 6), round(lng, 6)
            new_coord = u"{0},{1}".format(lng, lat)
            new_path.append(new_coord)
            path_list.append(new_path)
            new_path = [new_coord, coord]
            temp_length = dist / 2
        elif temp_length > 250:
            new_path.append(coord)
            path_list.append(new_path)
            new_path = [coord]
            temp_length = 0
        else:
            new_path.append(coord)
        last_pt, last_coord = pt, coord
    if len(new_path) >= 2:
        if temp_length > 100:
            path_list.append(new_path)
        else:
            try:
                temp_path = path_list[-1]
                temp_path.extend(new_path)
                path_list[-1] = temp_path
            except IndexError:          # path_list empty
                path_list.append(new_path)
    return path_list


def split():
    road_data = load_model('./road/road.txt')
    new_data = []
    for road in road_data:
        name = road['name']
        if True:
            split_road(road)
            road_paths = split_road(road)
            for i, path in enumerate(road_paths):
                new_road = {'name': name, 'ort': road['ort'] + ',{0}'.format(i),
                            'polyline': path2polyline(path)}
                new_data.append(new_road)
    save_model('./road/split.txt', new_data)


def save_db():
    road_data = load_model('./road/split.txt')
    conn = oracle_util.get_connection()
    cursor = conn.cursor()
    road_index = 1000001
    for road in road_data:
        name, path = road['name'], polyline2path(road['polyline'])
        sql = "insert into tb_road_state(rid, road_name, road_" \
              "level, road_desc) values(:1, :2, :3, :4)"
        tup = (road_index, name, 2, road['ort'])
        cursor.execute(sql, tup)
        sql = "insert into tb_road_point(rid, seq, longitude, " \
              "latitude) values(:1, :2, :3, :4)"
        tup_list = []
        for i, pt in enumerate(path):
            lng, lat = map(float, pt.split(',')[0:2])
            tup = (road_index, i, lng, lat)
            tup_list.append(tup)
        cursor.executemany(sql, tup_list)
        road_index += 1
    conn.commit()


save_db()
