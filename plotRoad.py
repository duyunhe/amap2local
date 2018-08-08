
# -*- coding: utf-8 -*-
# @Time    : 2018/8/1 16:21
# @Author  : 
# @简介    : 
# @File    : plotRoad.py

from geo import bl2xy
import matplotlib.pyplot as plt

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


fp = open("./road/road3.txt")
while True:
    line = fp.readline().strip('\n')
    if line == '':
        break
    if line[0] != '#':
        items = line.split(',', 1)
        road = items[1]
        line = fp.readline().strip('\n')
        seg = []
        crds = line.split(';')
        for crd in crds:
            l, b = map(float, crd.split(','))
            x, y = bl2xy(b, l)
            seg.append([x, y])
        x, y = zip(*seg)
        plt.plot(x, y)
        # plt.text(x[0], y[0], road)
plt.show()
