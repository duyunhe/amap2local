# -*- coding: utf-8 -*-
# @Time    : 2018/9/10 10:55
# @Author  : 
# @简介    : 道路数据结构
# @File    : map_data_struct.py


class Segment:
    def __init__(self, begin_pt, end_pt):
        """
        :param begin_pt: Point
        :param end_pt: Point
        """
        self.begin_point, self.end_point = begin_pt, end_pt


class Point(object):
    def __init__(self, x=0, y=0):
        self.x, self.y = x, y
        self.pid = None


class LinkDesc:
    def __init__(self, line, seq, ort):
        self.line, self.seq, self.ort = line, seq, ort


"""''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
MapPoint 表示点
MapLine 表示整条道路，道路由线段组成
MapLine point_list按顺序加入MapPoint
相交的道路通过同一个MapPoint pid关联
即在pid点处相交
MapPoint的link_list存放该点相关的道路路段信息list(line(道路MapLine), seq(道路中的第几个线段), ort)
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''"""


class MapPoint(Point):
    """
    点表示
    x, y, pid, link_list, rlink_list
    在全局维护list, 
    """
    def __init__(self, x, y):
        super(MapPoint, self).__init__(x, y)
        self.link_list = []
        self.rlink_list = []

    def add_link(self, link_desc, point):
        """
        :param link_desc: LinkDesc, (line, seq, ort)
        :param point: MapPoint (link to next point)
        :return: 
        """
        self.link_list.append([link_desc, point])

    def add_rlink(self, link_desc, point):
        """
        for oneway side, add one reverse link
        :param link_desc: LinkDesc, (line, seq, ort)
        :param point: MapPoint (link to prev point)
        :return: 
        """
        self.rlink_list.append([link_desc, point])

    def __str__(self):
        return "{0:.2f},{1:.2f}".format(self.x, self.y)

    def __hash__(self):
        return self.pid

    def __eq__(self, other):
        return self.pid == other.pid


class MapLine:
    def __init__(self, lid):
        self.point_list = []
        self.name, self.rank, self.ort = None, None, None
        self.lid = lid

    def add_point(self, map_point):
        self.point_list.append(map_point)


class SpeedLine:
    def __init__(self, lid, fwd):
        self.lid, self.fwd = lid, fwd
        self.uid = lid * 2 + int(fwd)

    def __hash__(self):
        return self.uid

    def __eq__(self, other):
        return self.uid == other.uid

    def __lt__(self, other):
        return self.uid < other.uid

    def __str__(self):
        return "{0},{1}".format(self.lid, self.fwd)

