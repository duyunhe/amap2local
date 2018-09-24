# -*- coding: utf-8 -*-
# @Time    : 2018/9/22
# @Author  : Clark Du
# @简介    : 平行线处理
# @File    : par.py

from refineMap import save_model, load_model2road, save_road2model, \
    point_list2polyline, get_cross
from geo import get_cross_point, is_segment_cross, get_parallel, point2segment2, calc_include_angle2, \
    get_dist
from map_struct import Road, Point, Segment


def par():
    PAR = 30
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
                seg0, seg1 = get_parallel(last_pt, pt, PAR)
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
        if road.name == u'文三路':
            road0.point_list = reversed(road0.point_list)
            road1.point_list = reversed(road1.point_list)
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


def par_divide(road0, road1):
    """
    as center divide, divide cross point for each other
    :param road0:
    :param road1:
    :return:
    """
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
                return


def par_offset(road0, road1):
    """
    边缘点的起点或终点从路中央偏移到路上
    :param road0: Road 目标道路
    :param road1: Road 待偏移到的道路
    :return:
    """
    # 当端点接近某道路且该道路没有路口交点时，需要偏移该端点，延长至下一个道路
    bp, ep = road0.point_list[0], road0.point_list[-1]
    min_dist = 1e10
    sel_seg = None
    for seg in road1.seg_list:
        dist = point2segment2(bp, seg)
        if dist < min_dist:
            min_dist, sel_seg = dist, seg
    # 寻找延长至的道路线段
    if min_dist < 50:
        min_dist = 1e10
        for pt in road1.cross_list:
            dist = get_dist(pt, bp)
            min_dist = min(dist, min_dist)
        if min_dist > 50:
            _, px, py = get_cross_point(sel_seg, road0.seg_list[0])
            cr = Point(px, py)
            # 该延长线应落在预计道路sel_seg上
            # 不然与其余道路有可能偏离在50米内
            extended_segment = Segment(cr, bp)
            if not is_segment_cross(extended_segment, sel_seg):
                return
            pt_list = [cr]
            pt_list.extend(road0.point_list[:])
            road0.set_point_list(pt_list)
            road0.gene_segment()
            return

    min_dist = 1e10
    sel_seg = None
    for seg in road1.seg_list:
        dist = point2segment2(ep, seg)
        if dist < min_dist:
            min_dist, sel_seg = dist, seg
    if min_dist < 50:
        min_dist = 1e10
        for pt in road1.cross_list:
            dist = get_dist(pt, ep)
            min_dist = min(dist, min_dist)
        if min_dist > 50:
            _, px, py = get_cross_point(sel_seg, road0.seg_list[-1])
            cr = Point(px, py)
            extended_segment = Segment(cr, bp)
            if not is_segment_cross(extended_segment, sel_seg):
                return
            road0.point_list.append(cr)
            road0.gene_segment()
            return


def par0():
    """
    对平行线的优化，
    :return:
    """
    road_data = load_model2road('./road/parallel.txt')
    for i, road0 in enumerate(road_data):
        for j, road1 in enumerate(road_data):
            if road0.name == road1.name:
                continue
            if i < j:
                par_divide(road0, road1)
    for i, road0 in enumerate(road_data):
        for j, road1 in enumerate(road_data):
            if road0.name == road1.name:
                continue
            par_offset(road0, road1)
    save_road2model('./road/par0.txt', road_data)


def par_simplify(road):
    last_pt = None
    pt_list = []
    for pt in road.point_list:
        if last_pt is not None:
            dist = get_dist(last_pt, pt)
            if dist > 1e-5:
                pt_list.append(pt)
        else:
            pt_list.append(pt)
        last_pt = pt
    road.point_list = pt_list
    road.gene_segment()


def par_cut(road):
    pt_list = []
    for i, pt in enumerate(road.point_list):
        pt_list.append(pt)
        last_cr = None
        for j, cr in enumerate(road.cross_list):
            if cr.cross_seg == i:
                if last_cr is None or get_dist(cr, last_cr) > 1e-5:
                    pt_list.append(cr)
                last_cr = cr
    road.point_list = pt_list
    cr_flag = 0
    cr_cnt = 0
    bp = road.point_list[0]
    for cr in road.cross_list:
        if get_dist(bp, cr) < 50:
            cr_cnt += 1
    # 假如是路口内部，则附近应有一个cross点
    # 假如是路口外部，则附近应有两个或0个cross点（证明略）
    if cr_cnt == 1:
        cr_flag = 1
    pt_list = []
    # 只有三种情况：
    # 起点段在路口内；终点段在路口内；两端均不在路口内
    for pt in road.point_list:
        if cr_flag:
            if pt.cross == 1:
                # 路口点，应恢复正常
                cr_flag = 0
                pt_list.append(pt)
            else:
                pass
        else:
            if pt.cross == 1:
                # 路口点，应cut
                pt_list.append(pt)
                cr_flag = 1
            else:
                pt_list.append(pt)
    road.set_point_list(pt_list)
    road.gene_segment()


def par1():
    """
    切路口
    :return:
    """
    road_data = load_model2road('./road/par0.txt')
    for road in road_data:
        par_simplify(road)

    for i, road0 in enumerate(road_data):
        for j, road1 in enumerate(road_data):
            if road0.name == road1.name:
                continue
            if i < j:
                par_divide(road0, road1)

    # 切掉路口那段
    for road in road_data:
        par_cut(road)
    save_road2model('./road/par1.txt', road_data)


par1()
