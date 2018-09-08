# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 15:26
# @Author  : 
# @简介    : segment去重
# @File    : refineMap.py

import json
import math
import numpy as np
# from DBConn import oracle_util
from geo import bl2xy, xy2bl, calc_dist, point2segment, line2grid,\
    get_segment_cross_point, is_segment_cross, get_parallel


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


def xylist2polyline(xy_list):
    str_list = ["{0:.2f},{1:.2f}".format(xy[0], xy[1]) for xy in xy_list]
    return ';'.join(str_list)


def polyline2xylist(polyline):
    """
    :param polyline: string
    :return: [pt0, pt1...ptn]
    """
    coords = polyline.split(';')
    xylist = []
    for coord in coords:
        px, py = map(float, coord.split(',')[0:2])
        xylist.append([px, py])
    return xylist


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
    road_data = load_model('./road/raw.txt')
    for road in road_data:
        pl = road['polyline']
        name = road['name']
        ort = road['orientation']
        pos0 = ort.find(u'从')
        pos1 = ort.find(u'到')
        road_begin = ort[pos0 + 1:pos1]
        road_end = ort[pos1 + 1:]
        lcodes = map(int, road['lcodes'].split(','))
        coords = pl.split(';')
        path = []
        for crd in coords:
            path.append(crd)
        try:
            road_temp[name].append((path, lcodes, road_begin, road_end))
        except KeyError:
            road_temp[name] = [(path, lcodes, road_begin, road_end)]

    # for ... brute
    road_data = []

    for road, path_info in road_temp.iteritems():
        # 分方向
        path_list0, path_list1 = [], []
        path_desc0, path_desc1 = [], []
        for path in path_info:          # path: [path, lcodes, road_begin, road_end]
            if path[1][0] > 0:
                path_list0.append(path[0])
                path_desc0.append([path[2:]])   # begin, end
            else:
                path_list1.append(path[0])
                path_desc1.append([path[2:]])
        print road
        merge_path_list = []          # 可能在同方向上有两条path
        l = len(path_list0)
        prev, suc = [-1] * l, [-1] * l
        for i, p0 in enumerate(path_list0):
            for j, p1 in enumerate(path_list0):
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
                m_path, m_road_be = [], []      # 道路起止
                for j, t in enumerate(idx):
                    if j != 0:
                        m_path.extend(path_list0[t][1:])
                    else:
                        m_path.extend(path_list0[t])
                    m_road_be.extend(path_desc0[t])
                merge_path_list.append([m_path, m_road_be])
        for path, desc in merge_path_list:
            road_info = {'name': road, 'polyline': path2polyline(path),
                         'begin': desc[0][0], 'end': desc[-1][1]}
            road_data.append(road_info)

        merge_path_list = []
        l = len(path_list1)
        prev, suc = [-1] * l, [-1] * l
        for i, p0 in enumerate(path_list1):
            for j, p1 in enumerate(path_list1):
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
                m_path, m_road_be = [], []
                for j, t in enumerate(idx):
                    if j != 0:
                        m_path.extend(path_list1[t][1:])
                    else:
                        m_path.extend(path_list1[t])
                    m_road_be.extend(path_desc1[t])
                merge_path_list.append([m_path, m_road_be])
        for path, desc in merge_path_list:
            road_info = {'name': road, 'polyline': path2polyline(path),
                         'begin': desc[0][0], 'end': desc[-1][1]}
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
    road_data = load_model('./road/merge.txt')
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
    road_index = 10001
    for road in road_data:
        name, path = road['name'], polyline2path(road['polyline'])
        sql = "insert into tb_road_statevalues(rid, road_name, road_" \
              "level, road_desc) (:1, :2, :3, :4)"
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


def dog_last(path):
    """
    简化道路，道格拉斯算法
    :param path: [[x,y]...[x,y]]
    :return: 
    """
    if len(path) == 2:
        return path
    max_dist, sel = -1e10, -1
    pt0, pt1 = path[0], path[-1]

    for i, pt in enumerate(path):
        dist = point2segment(pt, pt0, pt1)
        if dist > max_dist:
            max_dist, sel = dist, i
    new_path = []
    if max_dist > 0.5:
        path0, path1 = dog_last(path[:sel + 1]), dog_last(path[sel:])
        new_path.extend(path0[:-1])
        new_path.extend(path1)
    else:
        new_path = [pt0, pt1]
    return new_path


def get_diff(seg_list0, seg_list1, point):
    min_dist0 = 1e10
    for seg in seg_list0:
        dist = point2segment(point, seg[0], seg[1])
        min_dist0 = min(dist, min_dist0)
    min_dist1 = 1e10
    for seg in seg_list1:
        dist = point2segment(point, seg[0], seg[1])
        min_dist1 = min(dist, min_dist1)
    return math.fabs(min_dist0 - min_dist1), min_dist0 + min_dist1


def center():
    road_data = load_model('./road/merge.txt')
    road_dict = {}
    for road_info in road_data:
        name = road_info['name']
        try:
            road_dict[name].append(road_info)
        except KeyError:
            road_dict[name] = [road_info]

    road_center_list = []
    for name, road_list in road_dict.iteritems():
        # if name == u'文一路':
        #     continue
        xy_list = grid_center_line(name, road_list)
        polyline = xylist2polyline(xy_list)
        center_line = {'name': name, 'polyline': polyline}
        road_center_list.append(center_line)
    save_model('./road/center.txt', road_center_list)


def grid_center_line(road_name, road_list):
    print road_name
    road_xy_data = []

    sel_y = {}          # 用于每个y值需要扫描的栅格
    sel_x = {}

    test_road = road_list[0]
    pll = test_road['polyline']
    pt_list = []
    coord_list = polyline2path(pll)
    for coord in coord_list:
        px, py = coord2xy(coord)
        pt_list.append([px, py])
    dx = pt_list[0][0] - pt_list[-1][0]
    dy = pt_list[0][1] - pt_list[-1][1]
    k = math.fabs(dy / dx)
    scan_by_x = k < 1   # 沿着X轴或Y轴扫描

    line_xy = []
    for road_info in road_list:
        pll = road_info['polyline']
        coord_list = polyline2path(pll)
        seg_list = []
        lastx, lasty = 0, 0
        for i, coord in enumerate(coord_list):
            px, py = coord2xy(coord)
            if i > 0:
                seg_list.append(([lastx, lasty], [px, py]))
                grid_set = line2grid([lastx, lasty], [px, py])
                for x, y in grid_set:
                    line_xy.append([x, y])
                    if scan_by_x:
                        try:
                            sel_x[x].append(y)
                        except KeyError:
                            sel_x[x] = [y]
                    else:
                        try:
                            sel_y[y].append(x)
                        except KeyError:
                            sel_y[y] = [x]
            lastx, lasty = px, py
        road_xy_data.append(seg_list)

    plot_xy = []
    calc_cnt = 0

    if scan_by_x:
        # X scan
        x_coord = {}
        for x, y_list in sel_x.iteritems():
            # x_list = sel_y[y]
            y_list.sort()
            for y in np.arange(y_list[0], y_list[-1] + 1, 0.5):
                calc_cnt += 1
                diff, dist = get_diff(road_xy_data[0], road_xy_data[1], [x, y])
                if diff < 0.1:
                    try:
                        last_diff, last_dist, _ = x_coord[x]
                    except KeyError:
                        x_coord[x] = [diff, dist, y]
                        continue
                    if diff < last_diff:
                        x_coord[x] = [diff, dist, y]
                    elif diff == last_diff and dist < last_dist:
                        x_coord[x] = [diff, dist, y]
        print "calc cost ", calc_cnt
        keys = x_coord.keys()
        keys.sort()
        for x in keys:
            y = x_coord[x][2]
            plot_xy.append([x, y])

    else:
        # Y scan
        y_coord = {}
        for y, x_list in sel_y.iteritems():
            # x_list = sel_y[y]
            x_list.sort()
            for x in np.arange(x_list[0], x_list[-1] + 1, 0.5):
                calc_cnt += 1
                diff, dist = get_diff(road_xy_data[0], road_xy_data[1], [x, y])
                if diff < 0.1:
                    try:
                        last_diff, last_dist, _ = y_coord[y]
                    except KeyError:
                        y_coord[y] = [diff, dist, x]
                        continue
                    if diff < last_diff:
                        y_coord[y] = [diff, dist, x]
                    elif diff == last_diff and dist < last_dist:
                        y_coord[y] = [diff, dist, x]
        print "calc cost ", calc_cnt
        keys = y_coord.keys()
        keys.sort()
        for y in keys:
            x = y_coord[y][2]
            plot_xy.append([x, y])

    plot_xy = dog_last(plot_xy)
    return plot_xy
    # new_xy0, new_xy1 = [], []
    # last_seg = None
    # for i, seg in enumerate(plot_xy):
    #     if i > 0:
    #         nseg0, nseg1 = get_parallel(last_seg, seg, 20)
    #         new_xy0.append(nseg0)
    #         new_xy1.append(nseg1)
    #     last_seg = seg

    # main_show2(plot_xy, new_xy0, new_xy1)


def path2seg(path):
    """
    :param path: [pt0, pt1... ptn]
    :return: [seg0, seg1....seg n-1]
    """
    last_pt = None
    seg_list = []
    for pt in path:
        if last_pt is not None:
            seg_list.append([last_pt, pt])
        last_pt = pt
    return seg_list


def get_cross(path0, path1):
    """
    :param path0: 第一条道路的路径list
    :param path1: 第二条道路的路径list
    :return: cross point
    """
    cross_point = None
    seg_list0, seg_list1 = path2seg(path0), path2seg(path1)
    for s0 in seg_list0:
        for s1 in seg_list1:
            if is_segment_cross(s0, s1):
                _, px, py = get_segment_cross_point(s0, s1)
                cross_point = [px, py]
                break
    return cross_point


def get_cross_divide(path0, path1):
    """
    :param path0: list of points [pt0, pt1, ... ptn]
    :param path1:
    :return: list of points which add cross point
    """
    seg_list0, seg_list1 = path2seg(path0), path2seg(path1)
    sel_i, sel_j, cross_point = -1, -1, None
    for i, s0 in enumerate(seg_list0):
        for j, s1 in enumerate(seg_list1):
            if is_segment_cross(s0, s1):
                _, px, py = get_segment_cross_point(s0, s1)
                cross_point = [px, py]
                sel_i, sel_j = i, j
    new_path0, new_path1 = [], []


def seg2path(seg_list):
    """
    用于不连续线段补全交点
    :param seg_list: 线段的list
    :return:
    """
    xylist = [seg_list[0][0]]
    last_seg = None
    for seg in seg_list:
        if last_seg is not None:
            _, px, py = get_segment_cross_point(last_seg, seg)
            xylist.append([px, py])
        last_seg = seg
    xylist.append(seg_list[-1][1])
    return xylist


def par():
    road_data = load_model('./road/center.txt')
    pt = None
    for i, road0 in enumerate(road_data):
        for j, road1 in enumerate(road_data[i + 1:]):
            path0, path1 = polyline2xylist(road0['polyline']),\
                           polyline2xylist(road1['polyline'])
            pt = get_cross(path0, path1)

    par_road = []
    for road in road_data:
        name, path = road['name'], polyline2xylist(road['polyline'])
        last_pt = None
        par_seg0, par_seg1 = [], []
        for pt in path:
            if last_pt is not None:
                seg0, seg1 = get_parallel(last_pt, pt, 20)
                par_seg0.append(seg0)
                par_seg1.append(seg1)
            last_pt = pt
        path0, path1 = seg2path(par_seg0), seg2path(par_seg1)
        road_info = {'name': name, 'polyline': xylist2polyline(path0)}
        par_road.append(road_info)
        road_info = {'name': name, 'polyline': xylist2polyline(path1)}
        par_road.append(road_info)

    for i, road0 in enumerate(par_road):
        for j, road1 in enumerate(par_road[i + 1:]):
            path0, path1 = polyline2xylist(road0['polyline']), \
                           polyline2xylist(road1['polyline'])
            name0, name1 = road0['name'], road1['name']
            if name0 == name1:
                continue
            cross_pt = get_cross(path0, path1)
            if cross_pt is not None:
                pass

    save_model('./road/parallel.txt', par_road)
    return None

# center()
par()
