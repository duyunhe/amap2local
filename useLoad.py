# -*- coding: utf-8 -*-
# @Time    : 2018/7/25 15:10
# @Author  : 
# @简介    : 
# @File    : useLoad.py

from loadAMapAPI import batch_path_fetch
import cx_Oracle
import time


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
    try:
        gps_data = {}
        fp = open('./road/road3.txt', 'w')
        conn = cx_Oracle.connect('hz', 'hz', '192.168.11.88/orcl')
        sql = "select vehicle_num, px, py from tb_gps_1805 where speed_time > to_date(" \
              "'2018-05-01 11:00:00', 'yyyy-mm-dd hh24:mi:ss')" \
              "and speed_time < to_date('2018-05-01 12:00:00', 'yyyy-mm-dd hh24:mi:ss')"
        cursor = conn.cursor()
        cursor.execute(sql)
        for item in cursor:
            data = map(float, item)

        conn.close()
    except Exception as e:
        print e.message



