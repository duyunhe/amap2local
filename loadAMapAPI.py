# -*- coding: utf-8 -*-
# @Time    : 2018/7/25 9:43
# @Author  : yhdu@tongwoo.cn
# @简介    : 从高德路径API中获取数据
# @File    : loadAMapAPI.py


import json
import urllib2

data_idx = 0
param_list = []
my_key = "b41e8fba1baa7e243b8f09d8aa4d941c"
jt_key = "0a54a59bdc431189d9405b3f2937921a"


def get_all_main_roads(lng0, lat0, lng1, lat1):
    """
    获取给定矩形范围内的主要道路名称
    :param lng0: longitude 0
    :param lat0: latitude 0
    :param lng1: longitude 1
    :param lat1: latitude 1
    :return: name set
    """
    req = 'https://restapi.amap.com/v3/traffic/status/rectangle?city=杭州市' \
          '&key={0}&extensions=all&level=4&rectangle=' \
          ''.format(jt_key)

    try:
        f = urllib2.urlopen(req)
        response = f.read()
        temp = json.loads(response)
        ti = temp['trafficinfo']
        roads = ti['roads']
        x = set()
        for r in roads:
            try:
                name = r['name']
            except KeyError:
                continue
            x.add(name)

    except Exception as e:
        print e.message
    return x


def process_traffic_status(road_name):
    req = 'https://restapi.amap.com/v3/traffic/status/road?name={1}&city=杭州市' \
               '&key={0}&extensions=all'.format(jt_key, road_name)
    try:
        f = urllib2.urlopen(req)
        response = f.read()
        temp = json.loads(response)
        ti = temp['trafficinfo']
        roads = ti['roads']
        x = []
        for r in roads:
            try:
                ort = r['direction']
                name = r['name']
                polyline = r['polyline']
                lcode = r['lcodes']
            except KeyError:
                continue
            road_data = {'orientation': ort, 'name': name, 'polyline': polyline,
                         'lcodes': lcode}
            x.append(road_data)

    except Exception as e:
        print e.message
    return x


def process_json(url_json, fp):
    """
    没啥好说的，就是解析
    :param url_json: url
    :param fp: file opened
    :return: 
    """
    # fp = open('road.txt', 'w')
    global data_idx
    for data in url_json:
        print "data", data_idx
        data_idx += 1
        idx = 0
        last_xy = None
        try:
            body = data['body']
            route = body['route']
            path = route['paths'][0]
            steps = path['steps']
            line_list = []
            for step in steps:
                ins = step['instruction']
                ins = ins.encode('utf-8')
                road = step['road']
                r = road.encode('utf-8')
                if ins.find('调头') != -1:
                    last_xy = None
                    continue
                if ins.find('途径') != -1 or ins.find('途经') != -1:
                    road += u',途经'
                else:
                    road += u',道路'
                # if r != '虎跑路':
                #     continue
                try:
                    print idx, road, step['orientation']
                    unc_line = u"{0},{1},{2}\n".format(idx, road, step['orientation'])
                    str_line = unc_line.encode('utf-8')
                    line_list.append(str_line)
                except KeyError:
                    print idx, '无名'
                    line_list.append("{0},{1}\n".format(idx, 'noname'))
                idx += 1
                polyline = step['polyline']
                xy_items = polyline.split(';')
                begin_xy, end_xy = xy_items[0], xy_items[-1]
                joinline = None
                if last_xy is not None and last_xy != begin_xy:
                    polyline = last_xy + ';' + polyline
                last_xy = end_xy
                # if joinline is not None:
                #     unc_line = u"{0}\n".format(joinline)
                #     # print step['polyline']
                #     str_line = unc_line.encode('utf-8')
                #     line_list.append(str_line)

                unc_line = u"{0}\n".format(polyline)
                # print step['polyline']
                str_line = unc_line.encode('utf-8')
                line_list.append(str_line)

            fp.write("#{0},{1}\n".format(data_idx, idx))
            for line in line_list:
                fp.write(line)

        except Exception as e:
            print e.message


def batch_path_fetch(query_list, fp):
    """
    :param query_list: 参数list [depart_lng, depart_lat, dest_lng, dest_lat]
    :param fp: 文件fp
    :return: 
    """
    try:
        ops_list = []
        for query in query_list:
            dep_lng, dep_lat, dest_lng, dest_lat = query[0:4]
            url = "/v3/direction/driving?origin={0},{1}&destination={2},{3}" \
                  "&strategy=2&output=json&key={4}".format(dep_lng, dep_lat, dest_lng, dest_lat, jt_key)
            ops = {"url": url}
            ops_list.append(ops)
        data = {"ops": ops_list}
        body = json.dumps(data)
        req = urllib2.Request('https://restapi.amap.com/v3/batch?key={0}'.format(jt_key),
                              body, {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        response = f.read()
        # print response
        temp = json.loads(response)
        process_json(temp, fp)
        f.close()
    except urllib2.URLError, e:
        print e


def main():
    js_data = []
    road_list = ['文一路', '文二路', '文三路', '古翠路', '保俶北路', '天目山路',
                 '学院路', '教工路', '莫干山路', '文一西路', '文二西路', '文三西路',
                 '古墩路', '丰潭路', '紫金港路', '余杭塘路']

    fp = open('./road/raw.txt', 'w')
    for road_name in road_list:
        js_data.extend(process_traffic_status(road_name))
    js = json.dumps(js_data, ensure_ascii=False).encode('utf-8')
    fp.write(js)
    fp.write('\n')
    fp.close()


# main()


def get():
    l1, b1 = 120.376929, 30.09851
    l0, b0 = 120.046824, 30.362365
    dl, db = 120.095039 - 120.058991, 30.309158 - 30.348718
    while b0 <= b1:
        lt = l0
        while l0 <= l1:
            r = get_all_main_roads(l0, l0 + dl + )
            l0 += dl
    r = get_all_main_roads()
    for x in r:
        print x


get()
