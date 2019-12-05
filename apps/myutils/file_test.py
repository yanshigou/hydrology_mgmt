# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/12/4"
import matplotlib as mpl
import matplotlib.pyplot as plt

y_data = list()
x_data = list()
f = open("G:\dzt\hydrology_mgmt\media\SectionFile\\2019\\12\大断面.txt")

for i in f:

    line = i.split()
    if len(line) < 2:
        continue
    x = float(line[0])
    y = float(line[1])
    x_data.append(x)
    y_data.append(y)
f.close()

# 设置matplotlib正常显示中文和负号
mpl.rcParams['font.sans-serif'] = ['SimHei']  # 用黑体显示中文
mpl.rcParams['axes.unicode_minus'] = False  # 正常显示负号

max_x = max(x_data)
min_x = min(x_data)
max_y = max(y_data)
min_y = min(y_data)

markLine = 10  # 水位高程

plt.plot(x_data, y_data, color='brown')  # 先画折线图
# plt.fill(x_data, y_data, color="g", alpha=0.3)
plt.plot(([min_x, max_y], [max_x, max_y]), color='#1E90FF')

plt.fill_between(x_data, y_data, markLine, color='#1E90FF')  # 再画水面，填充颜色
plt.text(max_x / 2 - 120, markLine + 1, "水位值(m):" + str(markLine))  # 设置text位置

plt.fill_between(x_data, min_y, y_data, color='brown')  # 填充折线区域

plt.xlim(min_x, max_x)  # 构造x轴长度
plt.ylim(min_y, max_y+10)  # 构造y轴高度
# 显示横轴标签
plt.xlabel("起点距(m)")
# 显示纵轴标签
plt.ylabel("河底高程(m)")
# 显示图标题
plt.title("水文大断面")
plt.savefig('G:\dzt\hydrology_mgmt\media\SectionImage\daduanmian.png')
plt.show()
