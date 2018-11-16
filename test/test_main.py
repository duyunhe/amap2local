# -*- coding: utf-8 -*-
# @Time    : 2018/11/7 15:53
# @Author  : yhdu@tongwoo.cn
# @简介    : 主要道路查询
# @File    : test_main.py


import os

import cx_Oracle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def quick_road(road):
    road_list = ['中河高架', '上塘高架', '秋石快速路', '留石快速路',
                 '艮山东路', '艮山西路', '秋涛路', '秋涛北路', '石大快速路',
                 '德胜路', '德胜东路', '德胜中路', '文一路', '文一西路', '时代大道']
    return road in road_list


conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
cursor = conn.cursor()
sql = "select rid, road_name from tb_road_state where map_level = 1"
cursor.execute(sql)
name_dict = {}
ns = set()
for item in cursor:
    rid, name = int(item[0]), item[1]
    name_dict[rid] = name
cnt = [[] for i in range(5432)]
sql = "select rid, sample_num from TB_ROAD_SPEED_RESTORE t"
cursor.execute(sql)
for item in cursor:
    rid, num = int(item[0]), int(item[1])
    cnt[rid].append(num)
for i in range(5432):
    ft = np.mean(cnt[i])
    cnt[i] = ft
    if ft > 34:
        ns.add(name_dict[i])
print len(ns)
sql = "update tb_road_state set direction = 1 where map_level = 1 and road_name = :1"
tup_list = []
for name in ns:
    if not quick_road(name):
        tup_list.append((name,))
        print name
cursor.executemany(sql, tup_list)
conn.commit()
cursor.close()
conn.close()

plt.style.use("ggplot")
plt.rcParams['axes.unicode_minus'] = False
df = pd.DataFrame()
df["eng"] = cnt
plt.boxplot(x=df.values, labels=df.columns, whis=1.5, medianprops={'linestyle': '--', 'color': 'orange'})
plt.show()
