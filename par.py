# -*- coding: utf-8 -*-
# @Time    : 2018/9/22
# @Author  : Clark Du
# @简介    : 平行线处理
# @File    : par.py

from refineMap import save_model, load_model2road, save_road2model, \
    point_list2polyline, get_cross
from geo import get_cross_point, is_segment_cross, get_parallel, point2segment2, calc_include_angle2
from map_struct import Road, Point


def par():
    road_data = load_model2road('./road/center0.txt')
    par_road = []
    road_index = 0
    for road in road_data:
        name, point_list = road.name, road.point_list
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
        road_info = {'name': road.name, 'polyline': point_list2polyline(road.get_path()),
                     'entrance': point_list2polyline(tlist), 'rid': road.rid,
                     'exit': point_list2polyline(elist), 'cross': point_list2polyline(cross_list)}
        road_list.append(road_info)

    save_model('./road/parallel.txt', road_list)
    return


def par_cross(road0, road1):
    """
    类似center cross函数
    :param road0:
    :param road1:
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
        if is_segment_cross(road0.seg_list[-1], sel_seg) or \
                calc_include_angle2(road0.seg_list[-1], sel_seg) > 0.8:
            return
        _, px, py = get_cross_point(road0.seg_list[-1], sel_seg)
        road0.add_point(Point(px, py))
        road0.gene_segment()


def par0():
    """
    对平行线的优化
    :return:
    """
    road_data = load_model2road('./road/parallel.txt')
    for road0 in road_data:
        for road1 in road_data:
            if road0.name == road1.name:
                continue
            par_cross(road0, road1)
    save_road2model('./road/par0.txt', road_data)


par0()
