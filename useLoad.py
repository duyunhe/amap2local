# -*- coding: utf-8 -*-
# @Time    : 2018/7/25 15:10
# @Author  :
# @简介    : 使用loadAMapAPI并保存到原始文件
# @File    : useLoad.py

from loadAMapAPI import batch_path_fetch
import cx_Oracle
import time
from geo import bl2xy, xy2bl, calc_dist


def gene_from_order():
    """
    从订单中生成出发地点 到达地点
    调用高德API
    :return: 
    """
    try:
        fp = open('./road/road2.txt', 'w')
        conn = cx_Oracle.connect('hz', 'hz', '192.168.11.88/orcl')
        sql = "select dep_longi, dep_lati, dest_longi, dest_lati, dist from tb_order where dep_time >= to_date" \
              "('2018-05-01 11:00:00', 'yyyy-mm-dd hh24:mi:ss') " \
              "and dep_time < to_date('2018-05-01 12:00:00', 'yyyy-mm-dd hh24:mi:ss')"
        cursor = conn.cursor()
        cursor.execute(sql)
        pa_list = []
        cnt, idx = 0, 0
        for item in cursor:
            l0, b0, l1, b1, dist = map(float, item[0:5])
            if dist < 10:
                continue
            pa_list.append([l0, b0, l1, b1])
            idx += 1
            if idx >= 20:
                batch_path_fetch(pa_list, fp)
                time.sleep(0.2)
                pa_list = []
                idx = 0
                cnt += 1
                print "batch" + str(cnt)
                if cnt >= 500:
                    break
                # break
        fp.close()
    except Exception as e:
        print e.message


def gene_from_gps_data():
    """
    从gps点记录里面获取轨迹，并生成出发点和到达点
    :return: 
    """
    try:
        gps_data = {}
        # gps_data 用于存放每辆车的轨迹
        fp = open('./road/road.txt', 'w')
        conn = cx_Oracle.connect('hz', 'hz', '192.168.11.88/orcl')
        sql = "select vehicle_num, px, py from tb_gps_1805 where speed_time > to_date(" \
              "'2018-05-01 9:00:00', 'yyyy-mm-dd hh24:mi:ss')" \
              "and speed_time < to_date('2018-05-01 10:00:00', 'yyyy-mm-dd hh24:mi:ss')"
        cursor = conn.cursor()
        bt = time.clock()
        cursor.execute(sql)
        cnt = 0
        for item in cursor:
            data = map(float, item[1:3])
            lng, lat = data[0:2]
            if lng > 121 or lng < 119 or lat > 31 or lat < 29:
                continue
            x, y = bl2xy(lat, lng)
            veh = item[0][-6:]
            try:
                gps_data[veh].append([x, y])
            except KeyError:
                gps_data[veh] = [[x, y]]
            cnt += 1

        conn.close()
        et = time.clock()
        print et - bt
        s = 0
        req_list = []

        for veh, data_list in gps_data.iteritems():
            s += len(data_list)
            use_list = data_list[::10]
            for i in range(len(use_list) - 1):
                req_list.append([data_list[i][0], data_list[i][1], data_list[i + 1][0], data_list[i + 1][1]])

        print s
        pa_list, cnt, idx = [], 0, 0
        for req in req_list:
            x0, y0, x1, y1 = req[0:4]
            if calc_dist([x0, y0], [x1, y1]) > 2000:
                b0, l0 = xy2bl(x0, y0)
                b1, l1 = xy2bl(x1, y1)
                pa_list.append([l0, b0, l1, b1])
                idx += 1
                if idx >= 20:
                    batch_path_fetch(pa_list, fp)
                    time.sleep(0.2)
                    pa_list = []
                    idx = 0
                    cnt += 1
                    print "batch" + str(cnt)
                    if cnt >= 1000:
                        break
        fp.close()

    except Exception as e:
        print e.message


gene_from_gps_data()

