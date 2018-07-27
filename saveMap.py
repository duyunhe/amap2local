# -*- coding: utf-8 -*-
# @Time    : 2018/7/25 18:28
# @Author  : 
# @简介    : 
# @File    : saveMap.py

from time import clock
from geo import bl2xy

way_raw_nodes = {}          # 存放原始数据
way_nodes = {}              # 存放修改后的数据


def put_road(road, coords):
    try:
        way_raw_nodes[road].append(coords)
    except KeyError:
        way_raw_nodes[road] = [coords]


def build_road_list(next_table, xy_table, head):
    road_list = []
    while True:
        road_list.append(xy_table[head])
        try:
            head = next_table[head]
        except KeyError:
            break
    return road_list


def build_network():
    road_network = {}
    for road, crd_list in way_raw_nodes.iteritems():
        if road == 'noname':
            continue
        # if road != '教工路,东北':
        #     continue
        path_list, _ = build_road(road, crd_list)
        name, ort = road.split(',')
        try:
            road_network[name][ort] = path_list
        except KeyError:
            road_network[name] = {}
            road_network[name][ort] = path_list
    return road_network


def build_road(road, raw_path_list):
    """
    :param road: 路名
    :param raw_path_list: 原始路径list 
    :return: 
    """
    # print road
    node_id = {}        # 用经度做hash记录每个点的id
    xy_table = {}       # 记录每个id代表的经纬度
    prev_table = {}
    # 对确定的点对重建反向链表，即每一点对能确定道路的最小单元
    # 将路径拆成最小单元，对于prev->id的拓扑关系，记录每个id的prev_id
    # 并使得当prev_id == -1时，该点为合并后新路径的起点
    next_table = {}
    # 使用正向链表重建序列

    for crds in raw_path_list:
        prev_id = -1
        for crd in crds:
            x, y = bl2xy(crd[1], crd[0])
            uuid = str(crd[0]) + ',' + str(crd[1])
            # node id
            try:
                nid = node_id[uuid]
            except KeyError:
                nid = len(node_id)
                node_id[uuid] = nid
                xy_table[nid] = [x, y]
            # 当已经存在拓扑关系时，跳过
            if nid not in prev_table or prev_table[nid] == -1:
                prev_table[nid] = prev_id
            # if prev_id != -1 and prev_id not in next_table:
                next_table[prev_id] = nid
            prev_id = nid

    path_list = []
    for nid, pid in prev_table.iteritems():
        if pid == -1:
            path = build_road_list(next_table, xy_table, nid)
            path_list.append(path)
    return path_list, xy_table


def read_text(filename):
    """
    放到全局变量way_raw_nodes中处理
    :param filename: 
    :return: 
    """
    fp = open(filename)
    while True:
        line = fp.readline()
        if line == '':
            break
        data_index, road_cnt = line.split(',')
        # print data_index
        road_cnt = int(road_cnt)
        for i in range(road_cnt):
            line = fp.readline()
            item = line.strip('\n').split(',', 1)
            road = item[1]
            line = fp.readline()
            if road == 'noname':
                continue
            coords = line.strip('\n').split(';')
            cor_list = []
            for coord in coords:
                x, y = map(float, coord.split(','))
                cor_list.append([x, y])
            if i == 0:
                cor_list = cor_list[1:]
            elif i == road_cnt - 1:
                cor_list = cor_list[:-1]
            if len(cor_list) >= 2:
                put_road(road, cor_list)
    fp.close()


def combine_path_str(path):
    str_path = []
    for coord in path:
        x, y = coord[0:2]
        x, y = round(x, 2), round(y, 2)
        temp = "{0},{1}".format(x, y)
        str_path.append(temp)
    return ';'.join(str_path) + '\n'


def save_model(road_network):
    fp = open('road_network.txt', 'w')
    idx = 0
    for road, item in road_network.iteritems():
        fp.write("#road{0},{1},{2}\n".format(idx, road, len(item)))
        idx += 1
        for ort, path_list in item.iteritems():
            fp.write("$orientation,{0},{1}\n".format(ort, len(path_list)))
            for path in path_list:
                str_line = combine_path_str(path)
                fp.write(str_line)


def raw2model():
    read_text('road.txt')
    road_list = build_network()
    save_model(road_list)
    return road_list


def load_model():
    fp = open('road_network.txt', 'r')
    while True:
        line = fp.readline().strip('\n')
        if line == '':
            break
        _, road, road_cnt = line.split(',')
        road_cnt = int(road_cnt)
        way_nodes[road] = {}
        for i in range(road_cnt):
            line = fp.readline().strip('\n')
            _, ort, seg_cnt = line.split(',')
            seg_cnt = int(seg_cnt)
            way_nodes[road][ort] = []
            for j in range(seg_cnt):
                seg = []
                line = fp.readline().strip('\n')
                crds = line.split(';')
                for crd in crds:
                    x, y = map(float, crd.split(','))
                    seg.append([x, y])
                way_nodes[road][ort].append(seg)
    fp.close()
    return way_nodes


def test_model():
    read_text('road.txt')
    road = '教工路,东北'
    return way_raw_nodes[road]


raw2model()
