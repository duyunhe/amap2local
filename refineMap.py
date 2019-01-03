# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 15:26
# @Author  : 
# @简介    : segment去重
# @File    : refineMap.py

import json
import math

from DBConn import oracle_util
from geo import bl2xy, xy2bl, calc_dist, point2segment, get_cross_point, is_segment_cross, get_parallel, point2segment2, \
    calc_include_angle2, cut_x, cut_y
from map_struct import Road, Point, Segment


def grid(x, y):
    """
    用于网格化
    :param x: 平面坐标 
    :param y: 
    :return: 
    """
    minx, maxx, miny, maxy = 60000, 100000, 60000, 100000
    if x < minx:
        x = minx
    elif x > maxx:
        x = maxx
    if y < miny:
        y = miny
    elif y > maxy:
        y = maxy
    ix, iy = int((x - minx) / 1000), int((y - miny) / 1000)
    idx = ix * 40 + iy
    return idx


def road_near(road0, road1):
    """
    用网格辅助判断道路是否可能相交
    :param road0: Road
    :param road1: Road
    :return: True 在同一个网格内 False 反之
    """
    return len(road0.grid_set & road1.grid_set) > 0


def save_model(filename, road_data):
    """
    :param filename: string 
    :param road_data: list of road
    :return: 
    """
    js = json.dumps(road_data, ensure_ascii=False).encode('utf-8')
    fp = open(filename, 'w')
    fp.write(js)
    fp.write('\n')
    fp.close()


def save_road2model(filename, road_list):
    """
    :param filename: 
    :param road_list: list of Road
    注意：Road中的数据为unicode编码 即：value为str类型时，需转码为unicode类型
    :return: 
    """
    network = []
    for road in road_list:
        try:
            road_info = {'name': road.name, 'rid': road.rid,
                         'polyline': point_list2polyline(road.point_list), 'level': road.level}
        except ValueError:
            print road.name, 'Value Error'
        try:
            road_info['grid'] = list(road.grid_set)
        except TypeError:       # empty
            pass
        network.append(road_info)
    save_model(filename, network)


def load_model2road_by_grid(filename, grid_num):
    """
    调试用
    :param filename: 
    :param grid_num: 格子index
    :return: 在格子内经过的所有道路
    """
    data = load_model(filename)
    road_list = []
    for i, road_info in enumerate(data):
        name, point_list = road_info['name'], polyline2pt_list(road_info['polyline'])
        try:
            cross_list = []
        except KeyError:
            cross_list = []
        try:
            grid_set = set(road_info['grid'])
        except KeyError:
            grid_set = None
        if grid_num not in grid_set:
            continue
        # Road
        road = Road(name, 0, i)
        # mark = road_info['mark']
        # road.set_mark(mark)
        road.set_grid_set(grid_set)
        road.set_point_list(point_list)
        road.set_cross_list(cross_list)
        road.gene_segment()
        road_list.append(road)
    return road_list


def load_model2road(filename):
    data = load_model(filename)
    road_list = []
    for i, road_info in enumerate(data):
        name, point_list = road_info['name'], polyline2pt_list(road_info['polyline'])
        rid, level = road_info['rid'], road_info['level']
        try:
            cross_list = []
        except KeyError:
            cross_list = []
        try:
            grid_set = set(road_info['grid'])
        except KeyError:
            grid_set = None
        # Road
        level = 1 if main_road(name) else 0
        road = Road(name, level, rid)
        # mark = road_info['mark']
        # road.set_mark(mark)
        road.set_grid_set(grid_set)
        road.set_point_list(point_list)
        road.set_cross_list(cross_list)
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
    # print len(road_data)
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


def save_speed():
    conn = oracle_util.get_connection()
    cursor = conn.cursor()
    sql = "insert into tb_road_def_speed values(:1, :2)"
    tup_list = []
    for i in range(330):
        tup = (i, 40)
        tup_list.append(tup)
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()
    conn.close()


def update_road():
    conn = oracle_util.get_connection()
    cursor = conn.cursor()
    sql = "update tb_road_state set direction = 0"
    cursor.execute(sql)
    sql = "update tb_road_state set direction = 1 where rid = :1"
    tup_list = []
    for i in range(140, 148, 1):
        tup = (i, )
        tup_list.append(tup)
    for i in range(275, 295, 2):
        tup = (i, )
        tup_list.append(tup)
    for i in range(88, 106, 2):
        tup = (i, )
        tup_list.append(tup)
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()
    conn.close()


def save_db():
    # 原型
    # road_data = load_model('./road/20_offset/par0.txt')
    conn = oracle_util.get_connection()
    cursor = conn.cursor()
    # for road in road_data:
    #     name, path, road_index = road['name'], polyline2path(road['polyline']), road['rid']
    #     sql = "insert into tb_road_state (rid, road_name, direction, road_" \
    #           "level, road_desc, def_speed) values (:1, :2, :3, :4, :5, :6)"
    #     tup = (road_index, name, 0, 0, 0, 0)
    #     cursor.execute(sql, tup)
    #     sql = "insert into tb_road_point(rid, seq, longitude, " \
    #           "latitude, road_level) values(:1, :2, :3, :4, :5)"
    #     tup_list = []
    #     for i, pt in enumerate(path):
    #         px, py = map(float, pt.split(',')[0:2])
    #         lat, lng = xy2bl(px, py)
    #         tup = (road_index, i, lng, lat, 0)
    #         tup_list.append(tup)
    #     cursor.executemany(sql, tup_list)
    #     road_index += 1
    # conn.commit()
    # 宽的道路
    road_data = load_model('./road_new/par1.txt')
    for road in road_data:
        name, path, road_index = road['name'], polyline2path(road['polyline']), road['rid']
        sql = "insert into tb_road_state (rid, road_name, direction, map_" \
              "level, road_desc, def_speed) values (:1, :2, :3, :4, :5, :6)"
        tup = (road_index, name, 0, 1, 0, 0)
        cursor.execute(sql, tup)
        sql = "insert into tb_road_point_on_map(rid, seq, longitude, " \
              "latitude, map_level) values(:1, :2, :3, :4, 1)"
        tup_list = []
        for i, pt in enumerate(path):
            try:
                px, py = map(float, pt.split(',')[0:2])
            except ValueError:
                continue
            lat, lng = xy2bl(px, py)
            tup = (road_index, i, lng, lat)
            tup_list.append(tup)
        cursor.executemany(sql, tup_list)
        # road_index += 1
    conn.commit()
    cursor.close()
    conn.close()


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
    center_data = load_model('./road/center0.txt')
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


def trans():
    """
    先转换merge后的坐标系
    :return: 
    """
    road_list = load_model('./road/merge.txt')
    for road in road_list:
        pll = road['polyline']
        bllist = polyline2xylist(pll)
        xylist = []
        for lng, lat in bllist:
            x, y = bl2xy(lat, lng)
            xylist.append([x, y])
        strxy = xylist2polyline(xylist)
        road['polyline'] = strxy.decode('utf-8')
    save_model('./road/merge_xy.txt', road_list)


def main_road(name):
    m = [u'上塘', u'德胜', u'高速', u'中河', u'秋涛', u'石桥']
    for key in m:
        try:
            if name.find(key) != -1:
                return True
        except AttributeError:
            return False
    return False


# save_db()
