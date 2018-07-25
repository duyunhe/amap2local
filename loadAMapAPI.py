# -*- coding: utf-8 -*-
# @Time    : 2018/7/25 9:43
# @Author  : yhdu@tongwoo.cn
# @简介    : 从高德路径API中获取数据
# @File    : loadAMapAPI.py


import urllib2
import json

data_idx = 0
param_list = []
my_key = "b41e8fba1baa7e243b8f09d8aa4d941c"
jt_key = "0a54a59bdc431189d9405b3f2937921a"


def process_json(url_json, fp):
    # fp = open('road.txt', 'w')
    global data_idx
    for data in url_json:
        print "data", data_idx
        data_idx += 1
        idx = 0
        try:
            body = data['body']
            route = body['route']
            path = route['paths'][0]
            steps = path['steps']
            fp.write("#{0},{1}\n".format(data_idx, len(steps)))
            for step in steps:
                try:
                    print idx, step['road'], step['orientation']
                    unc_line = u"{0},{1},{2}\n".format(idx, step['road'], step['orientation'])
                    str_line = unc_line.encode('utf-8')
                    fp.write(str_line)
                except KeyError:
                    print idx, '无名'
                    fp.write("{0},{1}\n".format(idx, 'noname'))
                idx += 1
                polyline = step['polyline']
                unc_line = u"{0}\n".format(polyline)
                # print step['polyline']
                str_line = unc_line.encode('utf-8')
                fp.write(str_line)

        except Exception as e:
            print e.message


def batch_path_fetch(query_list, fp):
    """
    :param query_list: 参数list
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

