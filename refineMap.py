# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 15:26
# @Author  : 
# @简介    : segment去重
# @File    : refineMap.py

import json
import math

import numpy as np

from DBConn import oracle_util
from geo import bl2xy, xy2bl, calc_dist, point2segment, line2grid, \
    get_cross_point, is_segment_cross, get_parallel, point2segment2, calc_include_angle2, \
    cut_x, cut_y, get_dist, get_segment_length, cut_from_segment
from map_struct import Road, Point, Segment


def save_model(filename, road_data):
    js = json.dumps(road_data, ensure_ascii=False).encode('utf-8')
    fp = open(filename, 'w')
    fp.write(js)
    fp.write('\n')
    fp.close()


def save_road2model(filename, road_list):
    network = []
    for road in road_list:
        road_info = {'name': road.name, 'rid': road.rid,
                     'polyline': point_list2polyline(road.point_list)}
        cross_list = []
        for pt in road.cross_list:
            if pt.cross == 1:
                cross_list.append({'px': pt.px, 'py': pt.py, 'name': pt.cross_name})
        road_info['cross'] = cross_list
        network.append(road_info)
    save_model(filename, network)


def load_model2road(filename):
    data = load_model(filename)
    road_list = []
    for i, road_info in enumerate(data):
        name, point_list = road_info['name'], polyline2pt_list(road_info['polyline'])
        # Road
        road = Road(name, 0, i)
        road.set_point_list(point_list)
        road.gene_segment()
        road_list.append(road)
    return road_list


def load_model(filename):
    try:
        fp = open(filename)
        line = fp.readline().strip('\n')
        data = json.loads(line)
        fp.close()
    except ValueError:
        data = []
    except IOError:
        data = []
    return data


def path2polyline(path):
    return ';'.join(path)


def polyline2path(pll):
    items = pll.split(';')
    return items


def xylist2polyline(xy_list):
    str_list = ["{0:.2f},{1:.2f}".format(xy[0], xy[1]) for xy in xy_list]
    return ';'.join(str_list)


def point_list2polyline(point_list):
    str_list = ["{0:.2f},{1:.2f}".format(point.px, point.py) for point in point_list]
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


def polyline2pt_list(polyline):
    """
    :param polyline: string
    :return: [Point0, Point1...Pointn]
    """
    coords = polyline.split(';')
    point_list = []
    for coord in coords:
        px, py = map(float, coord.split(',')[0:2])
        pt = Point(px, py)
        point_list.append(pt)
    return point_list


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
    if max_dist > 2:
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

    temp_list = load_model('./road/center.txt')
    exist_road = []
    for road_info in temp_list:
        name = road_info['name']
        exist_road.append(name)
    road_center_list = temp_list
    for name, road_list in road_dict.iteritems():
        if name in exist_road:
            continue
        xy_list = grid_center_line(name, road_list)
        polyline = xylist2polyline(xy_list)
        center_line = {'name': name, 'polyline': polyline}
        road_center_list.append(center_line)
    save_model('./road/center.txt', road_center_list)


def grid_center_line(road_name, road_list):
    print road_name
    if len(road_list) == 1:
        # 单行线
        test_road = road_list[0]
        pll = test_road['polyline']
        pt_list = []
        coord_list = polyline2path(pll)
        for coord in coord_list:
            px, py = coord2xy(coord)
            pt_list.append([px, py])
        pt_list = dog_last(pt_list)
        return pt_list
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


def get_cross(road0, road1):
    """
    :param road0: Road
    :param road1: 
    :return: cross point
    """
    cross_point = None
    seg_list0, seg_list1 = road0.seg_list, road1.seg_list
    for i, s0 in enumerate(seg_list0):
        for j, s1 in enumerate(seg_list1):
            if is_segment_cross(s0, s1):
                d, px, py = get_cross_point(s0, s1)
                cross_point = Point(px, py)
                # d <0代表进路口 > 0代表出路口
                if d < 0:
                    s0.add_entrance(cross_point)
                else:
                    s0.add_exit(cross_point)
    return cross_point


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
            _, px, py = get_cross_point(last_seg, seg)
            xylist.append([px, py])
        last_seg = seg
    xylist.append(seg_list[-1][1])
    return xylist


def cut():
    road_data = load_model('./road/center.txt')
    temp = []
    for road in road_data:
        name, point_list = road['name'], polyline2pt_list(road['polyline'])
        new_point_list = cut_y(point_list, 86000)
        new_point_list = cut_x(new_point_list, 72500)
        road_info = {'name': name, 'polyline': point_list2polyline(new_point_list)}
        temp.append(road_info)
    save_model('./road/cut.txt', temp)


def par():
    road_data = load_model('./road/cut.txt')
    par_road = []
    road_index = 0
    for road in road_data:
        name, point_list = road['name'], polyline2pt_list(road['polyline'])
        last_pt = None
        road0, road1 = Road(name, 0, road_index), Road(name, 0, road_index + 1)
        road_index += 2
        seg_list0, seg_list1 = [], []
        for pt in point_list:
            if last_pt is not None:
                # 获取两条平移线段
                seg0, seg1 = get_parallel(last_pt, pt, 10)
                seg_list0.append(seg0)
                seg1.set_invert()
                seg_list1.append(seg1)
            last_pt = pt
        # 计算线段之间的交点
        last_seg = None
        for seg in seg_list0:
            if last_seg is None:
                road0.add_point(seg.begin_point)
            else:
                _, px, py = get_cross_point(last_seg, seg)
                cp = Point(px, py)
                road0.add_point(cp)
            last_seg = seg
        road0.add_point(last_seg.end_point)
        last_seg = None
        for seg in reversed(seg_list1):
            if last_seg is None:
                road1.add_point(seg.begin_point)
            else:
                _, px, py = get_cross_point(last_seg, seg)
                cp = Point(px, py)
                road1.add_point(cp)
            last_seg = seg
        road1.add_point(last_seg.end_point)
        # 并生成线段
        road0.gene_segment()
        road1.gene_segment()

        par_road.append(road0)
        par_road.append(road1)

    for i, road0 in enumerate(par_road):
        for j, road1 in enumerate(par_road):
            name0, name1 = road0.name, road1.name
            if name0 == name1:
                continue
            get_cross(road0, road1)

    road_list = []
    # Road list
    for road in par_road:
        # path_list = road.get_path_without_crossing()
        # for path in path_list:
        #     road_info = {'name': road.name, 'path': point_list2polyline(path),
        #                  'rid': road.rid}
        #     road_list.append(road_info)
        tlist, elist = road.get_entrance(), road.get_exit()
        cross_list = []
        cross_list.extend(tlist)
        cross_list.extend(elist)
        road_info = {'name': road.name, 'path': point_list2polyline(road.get_path()),
                     'entrance': point_list2polyline(tlist), 'rid': road.rid,
                     'exit': point_list2polyline(elist), 'cross': point_list2polyline(cross_list)}
        road_list.append(road_info)

    save_model('./road/parallel.txt', road_list)
    return None


def add_end_point(src_road, target_road):
    pt = src_road.seg_list[-1].end_point
    min_dist, sel_seg = 1e10, None
    for seg in target_road.seg_list:
        p0, p1 = seg.begin_point, seg.end_point
        d = point2segment([pt.px, pt.py], [p0.px, p0.py], [p1.px, p1.py])
        if min_dist > d:
            min_dist, sel_seg = d, seg
    _, px, py = get_cross_point(src_road.seg_list[-1], sel_seg)
    cross_pt = Point(px, py)
    src_road.add_segment(Segment(pt, cross_pt))


def add_begin_point(src_road, target_road):
    pt = src_road.seg_list[0].begin_point
    min_dist, sel_seg = 1e10, None
    for seg in target_road.seg_list:
        p0, p1 = seg.begin_point, seg.end_point
        d = point2segment([pt.px, pt.py], [p0.px, p0.py], [p1.px, p1.py])
        if min_dist > d:
            min_dist, sel_seg = d, seg
    _, px, py = get_cross_point(src_road.seg_list[0], sel_seg)
    cross_pt = Point(px, py)
    seg_list = src_road.seg_list
    temp = [Segment(cross_pt, pt)]
    for seg in seg_list:
        temp.append(seg)
    src_road.seg_list = temp


def center_offset(road0, road1):
    """
    起点和终点偏移到路上
    :param road0: Road 目标道路
    :param road1: Road 待偏移到的道路
    :return: 
    """
    # 当端点接近某路口时，需要偏移该端点，修正为路口
    bp, ep = road0.point_list[0], road0.point_list[-1]
    for pt in road1.cross_list:
        dist = get_dist(pt, bp)
        if 1e-5 < dist < 20:
            pt.cross = 0
            if pt.cross_name == road0.name:     # 说明与road0相交
                pos = pt.cross_other_seg + 1
            else:
                pos = 0
            pt_list = [pt]
            pt_list.extend(road0.point_list[pos:])
            road0.set_point_list(pt_list)
            road0.gene_segment()
            return

    for pt in road1.cross_list:
        dist = get_dist(pt, ep)
        if 1e-5 < dist < 20:
            pt.cross = 0
            if pt.cross_name == road0.name:  # 说明与road0相交
                pos = pt.cross_other_seg + 1
            else:
                pos = len(road0.point_list)
            pt_list = road0.point_list[:pos]
            pt_list.append(pt)
            road0.set_point_list(pt_list)
            road0.gene_segment()
            return


def center_divide(road0, road1):
    bp0, ep0, bp1, ep1 = road0.point_list[0], road0.point_list[-1], road1.point_list[0], road1.point_list[-1]
    if bp0 == bp1 or bp0 == ep1 or ep0 == bp1 or ep0 == ep1:
        return
    for i, seg0 in enumerate(road0.seg_list):
        for j, seg1 in enumerate(road1.seg_list):
            if is_segment_cross(seg0, seg1):
                _, px, py = get_cross_point(seg0, seg1)
                cr0 = Point(px, py)
                cr0.cross, cr0.cross_name, cr0.cross_other_seg = 1, road1.name, j
                cr0.cross_seg = i
                bp, ep = seg0.begin_point, seg0.end_point
                w0, w1 = get_dist(cr0, bp), get_dist(cr0, ep)
                if w0 > 1e-5 and w1 > 1e-5:
                    road0.cross_list.append(cr0)

                cr1 = Point(px, py)
                cr1.cross, cr1.cross_name, cr1.cross_other_seg = 1, road0.name, i
                cr1.cross_seg = j
                bp, ep = seg1.begin_point, seg1.end_point
                w0, w1 = get_dist(cr1, bp), get_dist(cr1, ep)
                if w0 > 1e-5 and w1 > 1e-5:
                    road1.cross_list.append(cr1)


def center_split(road):
    road_pt_list = []
    temp = []
    for pt in road.point_list:
        temp.append(pt)
        if pt.cross == 1:
            road_pt_list.append(temp)
            temp = [pt]
    road_pt_list.append(temp)

    road_list = []
    for pts in road_pt_list:
        road = Road(road.name, 0, -1)
        road.set_point_list(pts)
        road.gene_segment()
        road_list.append(road)
    return road_list


def center_split3(road):
    """
    将道路切分为THREAD米一段的路段
    最后一段小于100米时合并
    :param road: Road 
    :return: road list
    """
    THREAD = 350
    road_seg_list = []
    temp = []
    dist = 0
    for seg in road.seg_list:
        d = get_segment_length(seg)
        last_dist = dist
        dist += d
        while dist > THREAD:
            left = THREAD - last_dist
            s0, seg = cut_from_segment(seg, left)
            temp.append(s0)
            road_seg_list.append(temp)
            temp = []
            dist -= THREAD
            last_dist = 0
        temp.append(seg)
    dist0 = 0
    for seg in temp:
        dist0 += get_segment_length(seg)
    if dist0 < 100 and len(road_seg_list) > 0:
        road_seg_list[-1].extend(temp)
    else:
        road_seg_list.append(temp)

    road_list = []
    for seg_list in road_seg_list:
        road = Road(road.name, -1, -1)
        pt_list = [seg_list[0].begin_point]
        for seg in seg_list:
            pt_list.append(seg.end_point)
        road.set_point_list(pt_list)
        road.gene_segment()
        road_list.append(road)
    return road_list


def center_simplify(road):
    """
    最后再做一次简化
    :param road: 
    :return: 
    """
    pts = road.point_list
    xy_list = []
    for pt in pts:
        xy_list.append([pt.px, pt.py])
    xy_list = dog_last(xy_list)
    r = Road(road.name, 0, -1)
    for xy in xy_list:
        pt = Point(xy[0], xy[1])
        r.add_point(pt)
    r.gene_segment()
    return r


def center3():
    """
    中心线最后分隔
    :return: 
    """
    center_road = load_model2road('./road/center0.txt')
    new_center_road = center_road[:]
    center_road = []
    for road in new_center_road:
        center_road.append(center_simplify(road))
    new_center_road = []
    for road in center_road:
        new_center_road.extend(center_split3(road))
    # rid
    for i, road in enumerate(new_center_road):
        road.set_rid(i)
    save_road2model('./road/center1.txt', new_center_road)


def center2():
    """
    中心线的优化
    :return: 
    """
    center_road = load_model2road('./road/center.txt')

    # 合并平行连接的道路
    for i, road0 in enumerate(center_road):
        for j, road1 in enumerate(center_road):
            if j < i:
                center_merge(road0, road1)
    # 交叉点
    for i, road0 in enumerate(center_road):
        for j, road1 in enumerate(center_road):
            if i != j:
                center_cross(road0, road1)

    for i, road0 in enumerate(center_road):
        # if road0.name != u'文一西路':
        #     continue
        # print road0.name
        for j, road1 in enumerate(center_road):
            if j < i:
                center_divide(road0, road1)
    print "divide 1"
    # 端点落到道路
    for i, road0 in enumerate(center_road):
        for j, road1 in enumerate(center_road):
            if i != j:
                center_offset(road0, road1)

    for road in center_road:
        road.cross_list = []
    for i, road0 in enumerate(center_road):
        # print road0.name
        for j, road1 in enumerate(center_road):
            if j < i:
                center_divide(road0, road1)
    print "divide 2"
    # cross list
    for road in center_road:
        pt_list = []
        # split
        for i, pt in enumerate(road.point_list):
            pt_list.append(pt)
            for j, cr in enumerate(road.cross_list):
                if cr.cross_seg == i:
                    pt_list.append(cr)
        road.set_point_list(pt_list)
        road.gene_segment()

    new_center_road = []
    for road in center_road:
        new_center_road.extend(center_split(road))

    for i, road in enumerate(new_center_road):
        road.set_rid(i)

    save_road2model('./road/center0.txt', new_center_road)


def center_cross(road0, road1):
    """
    检查道路与其他道路的交叉，并且合并交叉点
    只有在道路尽头才会发生，因此和其他道路如有merge，应该不进行操作
    :param road0: Road
    :param road1: Road
    :return: 
    """
    bp, ep = road0.point_list[0], road0.point_list[-1]
    min_dist = 1e10
    sel_seg = None
    for seg in road1.seg_list:
        dist = point2segment2(bp, seg)
        if dist < min_dist:
            min_dist, sel_seg = dist, seg
    if min_dist < 50:
        if road0.bs == 1:
            return
        if is_segment_cross(road0.seg_list[0], sel_seg) or \
                calc_include_angle2(road0.seg_list[0], sel_seg) > 0.8:
            return
        _, px, py = get_cross_point(road0.seg_list[0], sel_seg)
        new_point_list = [Point(px, py)]
        for pt in road0.point_list:
            new_point_list.append(pt)
        road0.set_point_list(new_point_list)
        road0.gene_segment()
        return

    min_dist = 1e10
    sel_seg = None
    for seg in road1.seg_list:
        dist = point2segment2(ep, seg)
        if dist < min_dist:
            min_dist, sel_seg = dist, seg
    if min_dist < 50:
        if road0.es == 1:
            return
        if is_segment_cross(road0.seg_list[-1], sel_seg) or \
                calc_include_angle2(road0.seg_list[-1], sel_seg) > 0.8:
            return
        _, px, py = get_cross_point(road0.seg_list[-1], sel_seg)
        road0.add_point(Point(px, py))
        road0.gene_segment()


def center_merge(road0, road1):
    """
    检查端点是否重合
    :return: 
    """
    r0s0, r0s1 = road0.seg_list[0], road0.seg_list[-1]
    r1s0, r1s1 = road1.seg_list[0], road1.seg_list[-1]
    r0_bp, r0_ep = road0.point_list[0], road0.point_list[-1]
    r1_bp, r1_ep = road1.point_list[0], road1.point_list[-1]
    if get_dist(r0_bp, r1_ep) < 50 and calc_include_angle2(r0s0, r1s1) > 0.8:
        # 头尾相接，并且平行，说明是在同一条道路里面
        road1.add_point(r0_bp)
        road1.gene_segment()
        road1.es, road0.bs = 1, 1
    elif get_dist(r1_bp, r0_ep) < 50 and calc_include_angle2(r1s0, r0s1) > 0.8:
        road0.add_point(r1_bp)
        road0.gene_segment()
        road0.es, road1.bs = 1, 1
    elif get_dist(r0_bp, r1_bp) < 50 and calc_include_angle2(r0s0, r1s0) > 0.8:
        # 有时遇到单芯线
        new_point_list = [r1_bp]
        for pt in road0.point_list:
            new_point_list.append(pt)
        road0.set_point_list(new_point_list)
        road0.gene_segment()
        road0.bs, road1.es = 1, 1
    elif get_dist(r0_ep, r1_ep) < 50 and calc_include_angle2(r0s1, r1s1) > 0.8:
        road0.add_point(r1_ep)
        road0.gene_segment()
        road0.es, road1.bs = 1, 1


def make_cross(raw_road, center_road, raw_dict):
    """
    生成道路交点
    :param raw_road: 原始道路 list of Road
    :param center_road: 道路中心线 list of Road
    :param raw_dict: 原始道路集，用于延伸 dict { name: list of Road }
                     表示该路的两条对向边
    :return: 
    """
    cross_flag = 0               # 0: 无相交  1: 起点和道路相交  2: 终点和道路相交
    # 检查道路两端点
    begin_pt, end_pt = raw_road.point_list[0], raw_road.point_list[-1]
    sel_seg = None
    for i, seg in enumerate(center_road.seg_list):
        if point2segment2(begin_pt, seg) < 50:
            cross_flag, sel_seg = 1, seg
            break
        elif point2segment2(end_pt, seg) < 50:
            cross_flag, sel_seg = 2, seg
            break
    # 起点延伸
    if cross_flag == 1:
        # 先检查是否平行
        name = center_road.name
        road_list = raw_dict[name]
        if calc_include_angle2(raw_road.seg_list[0], sel_seg) > 0.8:
            return
        # 两条对向车道
        # 首先确定最近的两条线段
        seg0, seg1 = None, None
        min_dist = 1e10
        for seg in road_list[0].seg_list:
            d = point2segment2(begin_pt, seg)
            if d < min_dist:
                min_dist, seg0 = d, seg
        min_dist = 1e10
        for seg in road_list[1].seg_list:
            d = point2segment2(begin_pt, seg)
            if d < min_dist:
                min_dist, seg1 = d, seg
        # 其次确定是否与道路已经相交
        cross0, cross1 = False, False
        for seg in raw_road.seg_list:
            if is_segment_cross(seg0, seg):
                cross0 = True
            if is_segment_cross(seg1, seg):
                cross1 = True
        if not cross0 and not cross1:       # 两道路均未相交
            d, px, py = get_cross_point(raw_road.seg_list[0], seg0)
            if d > 0:       # 左转路口
                pt1 = Point(px, py)
                d, px, py = get_cross_point(raw_road.seg_list[0], seg1)
                pt0 = Point(px, py)
            else:
                pt0 = Point(px, py)
                d, px, py = get_cross_point(raw_road.seg_list[0], seg1)
                pt1 = Point(px, py)
            new_pt_list = [pt0, pt1]
            for point in raw_road.point_list:
                new_pt_list.append(point)
            raw_road.point_list = new_pt_list
            raw_road.gene_segment()
        elif not cross0 and cross1:         # 与seg0未相交
            d, px, py = get_cross_point(raw_road.seg_list[0], seg0)
            # d必然<0，在右转路口，seg0为右转路段
            pt0 = Point(px, py)
            new_pt_list = [pt0]
            for point in raw_road.point_list:
                new_pt_list.append(point)
            raw_road.point_list = new_pt_list
            raw_road.gene_segment()
        elif not cross1 and cross0:
            d, px, py = get_cross_point(raw_road.seg_list[0], seg1)
            # d必然<0，在右转路口，seg1为右转路段
            pt0 = Point(px, py)
            new_pt_list = [pt0]
            for point in raw_road.point_list:
                new_pt_list.append(point)
            raw_road.point_list = new_pt_list
            raw_road.gene_segment()
    # 终点延伸
    if cross_flag == 2:
        # 先检查是否平行
        name = center_road.name
        road_list = raw_dict[name]
        if calc_include_angle2(raw_road.seg_list[-1], sel_seg) > 0.8:
            return
        # 两条对向车道
        # 首先确定最近的两条线段
        seg0, seg1 = None, None
        min_dist = 1e10
        for seg in road_list[0].seg_list:
            d = point2segment2(end_pt, seg)
            if d < min_dist:
                min_dist, seg0 = d, seg
        min_dist = 1e10
        for seg in road_list[1].seg_list:
            d = point2segment2(end_pt, seg)
            if d < min_dist:
                min_dist, seg1 = d, seg
        # 其次确定是否与道路已经相交
        cross0, cross1 = False, False
        for seg in raw_road.seg_list:
            if is_segment_cross(seg0, seg):
                cross0 = True
            if is_segment_cross(seg1, seg):
                cross1 = True
        if not cross0 and not cross1:       # 两道路均未相交
            d, px, py = get_cross_point(raw_road.seg_list[-1], seg0)
            if d > 0:       # 左转路口
                pt1 = Point(px, py)
                d, px, py = get_cross_point(raw_road.seg_list[-1], seg1)
                pt0 = Point(px, py)
            else:
                pt0 = Point(px, py)
                d, px, py = get_cross_point(raw_road.seg_list[-1], seg1)
                pt1 = Point(px, py)
            raw_road.point_list.append(pt0)
            raw_road.point_list.append(pt1)
            raw_road.gene_segment()
        elif not cross0 and cross1:         # 与seg0未相交
            d, px, py = get_cross_point(raw_road.seg_list[-1], seg0)
            pt0 = Point(px, py)
            raw_road.point_list.append(pt0)
            raw_road.gene_segment()
        elif not cross1 and cross0:
            d, px, py = get_cross_point(raw_road.seg_list[-1], seg1)
            pt0 = Point(px, py)
            raw_road.point_list.append(pt0)
            raw_road.gene_segment()


def cross():
    """
    读取parallel文件
    自动匹配相近的路口，并将其存为road.txt
    :return: 
    """
    center_data = load_model('./road/cut.txt')
    raw_data = load_model('./road/parallel.txt')
    raw_list = []       # Road
    center_list = []
    raw_dict = {}
    # 读取文件
    for road_info in raw_data:
        name, point_list = road_info['name'], polyline2pt_list(road_info['path'])
        # Road
        road = Road(name, 0, road_info['rid'])
        cross_list = polyline2pt_list(road_info['cross'])
        road.set_cross_list(cross_list)
        for pt in point_list:
            road.add_point(pt)
        road.gene_segment()
        raw_list.append(road)
        try:
            raw_dict[name].append(road)
        except KeyError:
            raw_dict[name] = [road]

    for i, road_info in enumerate(center_data):
        name, point_list = road_info['name'], polyline2pt_list(road_info['polyline'])
        # Road
        road = Road(name, 0, i)
        for pt in point_list:
            road.add_point(pt)
        road.gene_segment()
        center_list.append(road)
    # 处理
    for i, raw_road in enumerate(raw_list):
        for j, center_road in enumerate(center_list):
            name0, name1 = raw_road.name, center_road.name
            if name0 == name1:
                continue
            make_cross(raw_road, center_road, raw_dict)

    network = []
    for road in raw_list:
        road_info = {'name': road.name, 'rid': road.rid,
                     'polyline': point_list2polyline(road.point_list)}
        network.append(road_info)
    save_model('./road/road.txt', network)


center3()


