# amap2local
将高德地图路网通过路径规划API复制到本地缓存，
并且做道路美化

1. loadAMapAPI.py

>读取API模块，下载道路

2. useLoad.py

>使用loadAMapAPI并保存到原始文件（已废弃）

3. saveMap.py

>将上述保存的原始文件重新组织成路网文件（废弃）

4. refineMap.py

>将上述路网文件中重复的道路去重

5. plotMap.py
>画图

6. /road/...
>数据文件放在此文件夹

 raw.txt 原始从高德down下来的数据，道路可能分段

 merge.txt 合并成完整的两条对向道路

 center.txt 道路中心线

 par.txt 通过中心线生成两条平行线

 参见test_all.py
 首先使用loadAMapAPI的main函数 存为raw.txt

 refineMap的merge函数 存为经纬度格式的merge.txt

 trans函数存为xy格式的merge_xy.txt

 center.py的center函数，初步提取中心线center.txt

 center0,center1两个函数，处理中心线

 par.py中 par函数生成平行线
 par0,par1等函数将路口间的线擦除