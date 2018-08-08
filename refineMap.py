# -*- coding: utf-8 -*-
# @Time    : 2018/8/3 15:26
# @Author  : 
# @简介    : segment去重
# @File    : refineMap.py

from plotMap import load_model
from saveMap import save_model

seg_map = {}
seg_idx = 0
seg_name = []
way_raw_nodes = {}          # 存放原始数据


def refine():
    """
    首先从network.txt里面提取路网信息
    打散后重建
    :return: 
    """
    global seg_idx
    # 先提取道路，再提取连接线
    way_nodes = load_model()
    for road, path_list in way_nodes.iteritems():
        road_name, road_type, road_ort = road.split(',')
        if road_type == '途经':
            continue
        for path in path_list:
            for i in range(len(path)):
                if i == 0:
                    continue
                path0, path1 = path[i - 1], path[i]
                seg_str = "{0},{1}:{2},{3}".format(path0[0], path0[1], path1[0], path1[1])
                if seg_str in seg_map:
                    print road, " conflict with ", seg_name[seg_map[seg_str]]
                    continue
                seg_map[seg_str] = seg_idx
                seg_name.append(road)
                try:
                    way_raw_nodes[road].append([path0, path1])
                except KeyError:
                    way_raw_nodes[road] = [[path0, path1]]
                seg_idx += 1
    for road, path_list in way_nodes.iteritems():
        road_name, road_type, road_ort = road.split(',')
        if road_type == '道路':
            continue
        for path in path_list:
            for i in range(len(path)):
                if i == 0:
                    continue
                path0, path1 = path[i - 1], path[i]
                seg_str = "{0},{1}:{2},{3}".format(path0[0], path0[1], path1[0], path1[1])
                if seg_str in seg_map:
                    print road, " conflict with ", seg_name[seg_map[seg_str]]
                    continue
                seg_map[seg_str] = seg_idx
                seg_name.append(road)
                try:
                    way_raw_nodes[road].append([path0, path1])
                except KeyError:
                    way_raw_nodes[road] = [[path0, path1]]
                seg_idx += 1

    road_net = build_network()
    save_model(road_net, './road/_road_network.txt')


def build_road_list(next_table, xy_table, head):
    road_list = []
    while True:
        road_list.append(xy_table[head])
        try:
            head = next_table[head]
        except KeyError:
            break
    return road_list


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
    # 对确定的点对重建反向链表，即每一对能确定道路的点作为最小单元segment
    # 将路径拆成segment，对于prev->id的拓扑关系，记录每个id的prev_id
    # 并使得当prev_id == -1时，该点为合并后新路径的起点
    next_table = {}
    # 使用正向链表重建序列
    for crds in raw_path_list:
        prev_id = -1
        for crd in crds:
            x, y = crd
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


def build_network():
    """
    从way_raw_nodes建立路网络
    :return: 
    """
    road_network = {}
    for road, crd_list in way_raw_nodes.iteritems():
        path_list, _ = build_road(road, crd_list)
        # name, ort = road.split(',')
        road_network[road] = path_list
    return road_network


refine()
