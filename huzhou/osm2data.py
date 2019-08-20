# -*- coding: utf-8 -*-
# @Time    : 2019/8/15 16:02
# @Author  : yhdu@tongwoo.cn
# @简介    : open street map
# @File    : osm2data.py


import xml.etree.cElementTree as ET

import matplotlib.pyplot as plt

from geo import bl2xy


class OSMPoint(object):
    def __init__(self, pid, lat, lng, x, y):
        self.pid = pid
        self.lng, self.lat = lng, lat
        self.x, self.y = x, y


class OSMLine(object):
    def __init__(self, point_list, rank):
        self.point_list = point_list
        self.rank = rank


def draw_line(line):
    x_list, y_list = [], []
    for point in line.point_list:
        x_list.append(point.x)
        y_list.append(point.y)
    color = {'primary': 'r', 'secondary': 'b', 'tertiary': 'c', 'motorway': 'orange', 'trunk': 'brown',
             'construction': 'orange'}
    c = color.get(line.rank, 'k')
    if line.rank.find('link') != -1:
        c = 'pink'
    if c == 'k':
        return
    plt.plot(x_list, y_list, c)


def draw_map(line_dict):
    for lid, line in line_dict.items():
        draw_line(line)
    plt.show()


def main():
    tree = ET.ElementTree(file="./map_data/map")
    root = tree.getroot()
    point_dict = {}
    line_dict = {}
    for elem in tree.iter():
        if elem.tag == 'node':
            att = elem.attrib
            pid, lng, lat = int(att['id']), float(att['lon']), float(att['lat'])
            x, y = bl2xy(lat, lng)
            point = OSMPoint(pid, lat, lng, x, y)
            point_dict[pid] = point
        if elem.tag == 'way':
            att = elem.attrib
            lid = int(att['id'])
            point_list = []
            for child in elem:
                if child.tag == 'nd':
                    att = child.attrib
                    pid = int(att['ref'])
                    point_list.append(point_dict[pid])
                if child.tag == 'tag':
                    att = child.attrib
                    k, v = att['k'], att['v']
                    if k == 'highway':
                        line = OSMLine(point_list, v)
                        line_dict[lid] = line
    draw_map(line_dict)


main()

