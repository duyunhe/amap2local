# -*- coding: utf-8 -*-
# @Time    : 2018/9/22
# @Author  : Clark Du
# @简介    : 平行线处理
# @File    : par.py

from geo import get_cross_point, is_segment_cross, get_parallel, point2segment2, calc_include_angle2, \
    get_dist
from map_struct import Road, Point, Segment
from refineMap import save_model, load_model2road, save_road2model, \
    point_list2polyline, grid, road_near, dog_last


def save_par(filename, par_road):
    """
    :param filename: string 存放的文件
    :param par_road: list of Road(struct) 生成的道路列表
    :return: 
    """
    road_list = []
    # Road list
    for road in par_road:
        cross_list = []
        try:
            road_info = {'name': road.name, 'polyline': point_list2polyline(road.point_list), 'rid': road.rid,
                         'cross': point_list2polyline(cross_list)}
            road_list.append(road_info)
        except ValueError:
            print road.name
            pass

    save_model(filename, road_list)


def par():
    PAR = 20
    road_data = load_model2road('./road_new/center1.txt')
    par_road = []
    # road_index = 0
    for i, road in enumerate(road_data):
        name, point_list = road.name, road.point_list
        rid = road.rid
        last_pt = None
        road0, road1 = Road(name, 0, rid * 2), Road(name, 0, rid * 2 + 1)
        road0.set_grid_set(road.grid_set)
        road1.set_grid_set(road.grid_set)
        # road_index += 2
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
        for j, seg in enumerate(seg_list0):
            if last_seg is None:
                road0.add_point(seg.begin_point)
            else:
                _, px, py = get_cross_point(last_seg, seg)
                if px is None:      # 平行
                    road0.add_point(seg.begin_point)
                else:
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
                if px is None:      # 平行
                    road1.add_point(seg.begin_point)
                else:
                    cp = Point(px, py)
                    road1.add_point(cp)
            last_seg = seg
        road1.add_point(last_seg.end_point)
        # 并生成线段
        road0.gene_segment()
        road1.gene_segment()

        par_road.append(road0)
        par_road.append(road1)

    # for test
    # save_par('./road_test/par_0.txt', par_road)
    # return

    # 端点处有merge的可能
    for i, road0 in enumerate(par_road):
        for j, road1 in enumerate(par_road):
            if i < j and road_near(road0, road1):
                par_merge(road0, road1)

    save_par('./road_new/par.txt', par_road)
    par_mark()


def par_merge(road0, road1):
    """
    一条线段的起点与另一条(平行线段）的终点相接
    :param road0: 
    :param road1: 
    :return: road0, road1重新生成道路
    """
    THREAD = 10
    bp0, ep0, bp1, ep1 = road0.point_list[0], road0.point_list[-1], road1.point_list[0], road1.point_list[-1]
    try:
        if bp0 == ep1 or bp1 == ep0:
            return
    except TypeError:
        print 'par merge', road0.rid, road1.rid, 'TypeError'
        return
    # 在生成平行线后两条道路之间必然（除非是一直线上）有空隙或者交叉
    # 这个THREAD值不能太大，否则和对向车道也能查找到一起
    if get_dist(bp0, ep1) < THREAD:
        begin_seg, end_seg = road0.seg_list[0], road1.seg_list[-1]
        # 首先是平行
        if calc_include_angle2(begin_seg, end_seg) <= 0.8:
            return
        if is_segment_cross(begin_seg, end_seg):
            # 相交时cut
            _, px, py = get_cross_point(begin_seg, end_seg)
            cr = Point(px, py)
            road0.point_list[0] = cr
            road1.point_list[-1] = cr
            road0.gene_segment()
            road1.gene_segment()
        else:
            # 不相交时延长
            _, px, py = get_cross_point(begin_seg, end_seg)
            cr = Point(px, py)
            pt_list = [cr]
            pt_list.extend(road0.point_list)
            road0.point_list = pt_list
            road1.point_list.append(cr)
            road0.gene_segment()
            road1.gene_segment()
    elif get_dist(bp1, ep0) < THREAD:
        begin_seg, end_seg = road1.seg_list[0], road0.seg_list[-1]
        # 首先是平行
        if calc_include_angle2(begin_seg, end_seg) <= 0.8:
            return
        if is_segment_cross(begin_seg, end_seg):
            # 相交时cut
            _, px, py = get_cross_point(begin_seg, end_seg)
            cr = Point(px, py)
            road1.point_list[0] = cr
            road0.point_list[-1] = cr
            road0.gene_segment()
            road1.gene_segment()
        else:
            # 不相交时延长
            _, px, py = get_cross_point(begin_seg, end_seg)
            cr = Point(px, py)
            pt_list = [cr]
            pt_list.extend(road1.point_list)
            road1.point_list = pt_list
            road0.point_list.append(cr)
            road0.gene_segment()
            road1.gene_segment()


def par_divide(road0, road1):
    """
    as center divide, divide cross point for each other
    :param road0:
    :param road1:
    :return:
    """
    bp0, ep0, bp1, ep1 = road0.point_list[0], road0.point_list[-1], road1.point_list[0], road1.point_list[-1]
    if bp0 == bp1:
        road0.bs, road1.bs = 1, 1
        return
    elif bp0 == ep1:
        road0.bs, road1.es = 1, 1
        return
    elif ep0 == bp1:
        road0.es, road1.bs = 1, 1
        return
    elif ep0 == ep1:
        road0.es, road1.es = 1, 1
        return
    for i, seg0 in enumerate(road0.seg_list):
        for j, seg1 in enumerate(road1.seg_list):
            if calc_include_angle2(seg0, seg1) > 0.8:       # 平行
                continue
            if is_segment_cross(seg0, seg1):
                _, px, py = get_cross_point(seg0, seg1)
                cr0 = Point(px, py)
                cr0.cross, cr0.cross_name, cr0.cross_other_seg = 1, road1.rid, j
                cr0.cross_seg = i
                bp, ep = seg0.begin_point, seg0.end_point
                w0, w1 = get_dist(cr0, bp), get_dist(cr0, ep)
                if w0 > 1e-5 and w1 > 1e-5:
                    road0.cross_list.append(cr0)

                cr1 = Point(px, py)
                cr1.cross, cr1.cross_name, cr1.cross_other_seg = 1, road0.rid, i
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
    :param road1: Road 待偏移到的（垂直）道路
    :return:
    """
    OFFSET = 40
    # 当端点接近某道路且该道路没有路口交点时，需要偏移该端点，延长至下一个道路
    # 端点必须没有和其他线段相交
    if road1.rid & 1:
        return
    bp, ep = road0.point_list[0], road0.point_list[-1]
    # 首先是起点
    min_dist = 1e10
    sel_seg = None
    for seg in road1.seg_list:
        dist = point2segment2(bp, seg)
        if dist < min_dist:
            min_dist, sel_seg = dist, seg
    # 寻找延长至的道路线段
    if min_dist < OFFSET:
        if road0.bs == 1:
            return
        min_dist = 1e10
        for pt in road1.cross_list:
            dist = get_dist(pt, bp)
            min_dist = min(dist, min_dist)
        if min_dist > OFFSET:
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
    if min_dist < OFFSET:
        if road0.es == 1:
            return
        min_dist = 1e10
        for pt in road1.cross_list:
            dist = get_dist(pt, ep)
            min_dist = min(dist, min_dist)
        if min_dist > OFFSET:
            _, px, py = get_cross_point(sel_seg, road0.seg_list[-1])
            cr = Point(px, py)
            extended_segment = Segment(cr, bp)
            if not is_segment_cross(extended_segment, sel_seg):
                return
            road0.point_list.append(cr)
            road0.gene_segment()
            return


def par_insert_cross(road):
    pt_list = []
    # split
    for i, pt in enumerate(road.point_list):
        pt_list.append(pt)
        last_cr = None
        insert_list = []
        for j, cr in enumerate(road.cross_list):
            # 相同的线段内可能有几个cross点
            if cr.cross_seg == i:
                if last_cr is None or get_dist(cr, last_cr) > 1e-5:
                    # pt_list.append(cr)
                    # 排序后再插入
                    dist = get_dist(pt, cr)
                    insert_list.append((dist, cr))
                last_cr = cr
        for d, cr in sorted(insert_list):
            pt_list.append(cr)
    road.set_point_list(pt_list)
    road.gene_segment()


def par0():
    """ 
    对平行线的优化，
    组成可以使用的路网
    :return:
    """
    road_data = load_model2road('./road_new/par.txt')

    for i, road0 in enumerate(road_data):
        for j, road1 in enumerate(road_data):
            if i < j and road_near(road0, road1):
                try:
                    par_divide(road0, road1)
                except ZeroDivisionError:
                    print road0.rid, road1.rid

    print "par_divide 0"
    # 偏移终点起点的路口
    for i, road0 in enumerate(road_data):
        for j, road1 in enumerate(road_data):
            if road0.name == road1.name or not road_near(road0, road1):
                continue
            par_offset(road0, road1)
    print "par offset"

    for road in road_data:
        par_simplify(road)

    # 再做divide前需要清空
    for road in road_data:
        road.cross_list = []
    for i, road0 in enumerate(road_data):
        for j, road1 in enumerate(road_data):
            if road0.name == road1.name:
                continue
            if i < j and road_near(road0, road1):
                par_divide(road0, road1)

    for road in road_data:
        par_insert_cross(road)

    for road in road_data:
        par_simplify(road)

    for road in road_data:
        par_check(road)

    save_road2model('./road_new/par0.txt', road_data)
    print "par0"


def par_simplify(road):
    last_pt = None
    pt_list = []
    # 先除去重复点
    for pt in road.point_list:
        if last_pt is not None:
            dist = get_dist(last_pt, pt)
            if dist > 1e-5:
                pt_list.append(pt)
        else:
            pt_list.append(pt)
        last_pt = pt
    pts = road.point_list
    # 然后用doglas简化算法
    xy_list = []
    for pt in pts:
        xy_list.append([pt.px, pt.py])
    xy_list = dog_last(xy_list)
    road.point_list = []
    for xy in xy_list:
        pt = Point(xy[0], xy[1])
        road.add_point(pt)
    road.gene_segment()


def par_check(road):
    last_pt = None
    pt_list = []
    for i, pt in enumerate(road.point_list):
        if last_pt is not None and pt == last_pt:
            last_pt = pt
            continue
        pt_list.append(pt)
        last_pt = pt
    road.point_list = pt_list
    last_pt = None
    sel = -1
    for i, pt in enumerate(road.point_list):
        if last_pt is not None:
            dist = get_dist(last_pt, pt)
            if dist > 2000:
                print road.rid, road.name, 'dist', dist, i
                sel = i
                break
        last_pt = pt
    # if sel != -1:
    #     del(road.point_list[sel])


def par_cut(road):
    cr_flag = 0
    for i, pt in enumerate(road.point_list):
        if pt.cross == 1:
            cr_flag = 0
            break
        if pt.cross == 2:
            cr_flag = 1
            break
    pt_list = []
    for i, pt in enumerate(road.point_list):
        if not cr_flag:         # 不在路口
            if pt.cross == 1:
                if i != 0:
                    pt_list.append(pt)
                cr_flag = 1
            else:
                pt_list.append(pt)
        else:
            if pt.cross == 2:
                cr_flag = 0
                if i != len(road.point_list) - 1:   # 最后一个点不用加入
                    pt_list.append(pt)

    road.set_point_list(pt_list)
    road.gene_segment()


def par_cross(road0, road1):
    """
    类似par divide，但是要标记每个pt点的进出路口情况
    :param road0: 
    :param road1: 
    :return: 
    """
    rbp0, rep0, rbp1, rep1 = road0.point_list[0], road0.point_list[-1], road1.point_list[0], road1.point_list[-1]
    if rbp0 == rbp1 or rbp0 == rep1 or rep0 == rbp1 or rep0 == rep1:
        return
    for i, seg0 in enumerate(road0.seg_list):
        for j, seg1 in enumerate(road1.seg_list):
            if calc_include_angle2(seg0, seg1) > 0.8:  # 平行
                continue
            if is_segment_cross(seg0, seg1):
                d, px, py = get_cross_point(seg0, seg1)
                bp0, ep0 = seg0.begin_point, seg0.end_point
                bp1, ep1 = seg1.begin_point, seg1.end_point
                cr = Point(px, py)
                if bp0 == cr:
                    if cr == rep1 or cr == rbp1:
                        pass
                    else:
                        if d < 0:
                            road0.point_list[i].cross = 1
                        else:
                            road0.point_list[i].cross = 2
                elif ep0 == cr:
                    if cr == rep1 or cr == rbp1:
                        pass
                    else:
                        if d < 0 and not():
                            road0.point_list[i + 1].cross = 1
                        else:
                            road0.point_list[i + 1].cross = 2
                if bp1 == cr:
                    if cr == rep0 or cr == rbp0:
                        pass
                    else:
                        if d < 0:
                            road1.point_list[j].cross = 2
                        else:
                            road1.point_list[j].cross = 1
                elif ep1 == cr:
                    if cr == rep0 or cr == rbp0:
                        pass
                    else:
                        if d < 0:
                            road1.point_list[j + 1].cross = 2
                        else:
                            road1.point_list[j + 1].cross = 1
                return


def par1():
    """
    切路口
    :return:
    """
    road_data = load_model2road('./road/par0.txt')

    for i, road0 in enumerate(road_data):
        for j, road1 in enumerate(road_data):
            if i < j and road0.name != road1.name and road_near(road0, road1):
                par_cross(road0, road1)

    # 切掉路口那段
    for road in road_data:
        par_cut(road)
    save_road2model('./road/par1.txt', road_data)


def extend_grid(grid_set):
    """
    扩展集合至九个格子
    :param grid_set: 
    :return: 
    """
    ns = set()
    for n in grid_set:
        x, y = n / 40, n % 40
        for i in range(-1, 2):
            for j in range(-1, 2):
                nx, ny = x + i, y + j
                if nx < 0:
                    nx = 0
                if nx >= 40:
                    nx = 40
                if ny < 0:
                    ny = 0
                if ny >= 40:
                    ny = 40
                ns.add(nx * 40 + ny)
    return ns


def par_mark():
    road_data = load_model2road('./road_new/par.txt')
    # minx, maxx, miny, maxy = 1e10, 0, 1e10, 0
    for road in road_data:
        # par_simplify(road)
        par_check(road)
        xylist = road.point_list
        grid_set = set()
        try:
            for pt in xylist:
                grid_set.add(grid(pt.px, pt.py))
            road.set_grid_set(extend_grid(grid_set))
        except ValueError:
            print road.name

    save_road2model('./road_new/par.txt', road_data)


par0()
