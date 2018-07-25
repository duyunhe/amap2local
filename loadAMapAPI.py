# -*- coding: utf-8 -*-
# @Time    : 2018/7/25 9:43
# @Author  : yhdu@tongwoo.cn
# @简介    : 从高德路径API中获取数据
# @File    : loadAMapAPI.py


import urllib2
import json

idx = 0
param_list = []
my_key = "b41e8fba1baa7e243b8f09d8aa4d941c"
jt_key = "0a54a59bdc431189d9405b3f2937921a"


def fetch_path_list(dep_lng, dep_lat, dest_lng, dest_lat):
    url = "http://restapi.amap.com/v3/direction/driving?" \
          "origin={0},{1}&destination={2},{3}&strategy=2" \
          "&output=json&key={4}".format(dep_lng, dep_lat, dest_lng, dest_lat, my_key)
    temp = urllib2.urlopen(url)
    temp = json.loads(temp.read())
    route = temp['route']
    path = route['paths'][0]
    dist = int(path['distance'])
    steps = path['steps']
    global idx
    for step in steps:
        try:
            print idx, step['road'], step['orientation']
        except KeyError:
            print idx, '无名'
        idx += 1
        print step['polyline']
    return dist


def process_json(url_json):
    for data in url_json:
        try:
            body = data['body']
            route = body['route']
            path = route['paths'][0]
            steps = path['steps']
            global idx
            for step in steps:
                try:
                    print idx, step['road'], step['orientation']
                except KeyError:
                    print idx, '无名'
                idx += 1
                print step['polyline']
        except Exception as e:
            print e.message


def fetch_path_batch(query_list):
    try:
        ops_list = []
        for query in query_list:
            dep_lng, dep_lat, dest_lng, dest_lat = query[0:4]
            url = "/v3/direction/driving?origin={0},{1}&destination={2},{3}" \
                  "&strategy=2&output=json&key={4}".format(dep_lng, dep_lat, dest_lng, dest_lat, my_key)
            ops = {"url": url}
            ops_list.append(ops)
        data = {"ops": ops_list}
        body = json.dumps(data)
        req = urllib2.Request('https://restapi.amap.com/v3/batch?key={0}'.format(my_key),
                              body, {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        response = f.read()
        # print response
        temp = json.loads(response)
        process_json(temp)
        f.close()
    except urllib2.URLError, e:
        print e


# fetch_path_list(120.170994, 30.277794, 120.166719, 30.276362)
path_list = [[120.119415, 30.282204, 120.122334, 30.27646], [120.170994, 30.277794, 120.166719, 30.276362]]
fetch_path_batch(path_list)
