# -*- coding: utf-8 -*-
# @Time    : 2018/9/29 17:03
# @Author  : 
# @简介    : 速度与样本数量的关系
# @File    : road_speed.py


import cx_Oracle
import matplotlib.pyplot as plt
import numpy as np


class KPoint:
    def __init__(self):
        self.xi, self.yi, self.index = 0, 0, 0


conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
cursor = conn.cursor()
sql = "select * from TB_ROAD_SPEED_BAK t"
x_list, y_list = [], []
z_list = []
cursor.execute(sql)
for item in cursor:
    spd = float(item[1])
    num = int(item[2])
    tti = float(item[3])
    x_list.append(num)
    y_list.append(spd)
    z = tti / num
    if z > 0:
        z_list.append(z)

z_list.sort()
h_list = []
mean = np.mean(z_list)
dist = 0
for z in z_list:
    dist += z - mean
    h_list.append(dist)
pos = h_list.index(min(h_list))
print z_list[pos]

x_list = [i for i in range(len(z_list))]
# plt.plot(x_list, h_list)
plt.scatter(x_list, z_list)
plt.show()
