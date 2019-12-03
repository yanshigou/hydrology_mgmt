# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/5/10"
from users.models import HistoryRecord, Message
import math
import requests
import pynmea2
import json
import xlsxwriter
from devices.models import DevicesInfo
from django.template.context_processors import csrf
import base64


# 操作记录
def create_history_record(user, content, r_type=True):
    try:
        HistoryRecord.objects.create(username_id=user, operation_content=content, r_type=r_type)
        return True
    except Exception as e:
        print(e)
        return False


# 消息提醒
def make_message(username, content, m_type):
    Message.objects.create(username_id=username, content=content, m_type=m_type)
    return True


# 启用状态
def device_is_active(imei_id):
    device_info = DevicesInfo.objects.filter(id=imei_id).values()
    if device_info:
        is_active = device_info[0]['is_active']
    else:
        is_active = False
    return is_active


# 坐标转换

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 偏心率平方


def bd09_to_gcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02)
    百度——>谷歌、高德
    :param bd_lat:百度坐标纬度
    :param bd_lon:百度坐标经度
    :return:转换后的坐标列表形式
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return [gg_lng, gg_lat]


def gcj02_to_bd09(lng, lat):
    """
    火星坐标系(GCJ-02)转百度坐标系(BD-09)
    谷歌、高德——>百度
    :param lng:火星坐标经度
    :param lat:火星坐标纬度
    :return:
    """
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return [bd_lng, bd_lat]


def wgs84_to_gcj02(lng, lat):
    """
    WGS84转GCJ02(火星坐标系)
    :param lng:WGS84坐标系的经度
    :param lat:WGS84坐标系的纬度
    :return:
    """
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [mglng, mglat]


def gcj02_to_wgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


def bd09_to_wgs84(bd_lon, bd_lat):
    lon, lat = bd09_to_gcj02(bd_lon, bd_lat)
    return gcj02_to_wgs84(lon, lat)


def wgs84_to_bd09(lon, lat):
    lon, lat = wgs84_to_gcj02(lon, lat)
    return gcj02_to_bd09(lon, lat)


def _transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


# 批量GPS转高德
def gps_amap(locations):
    api = "http://restapi.amap.com/v3/assistant/coordinate/convert?locations={}" \
          "&coordsys=gps&key=5cda232d2d1f782a634096167304eb59"
    gps = ""
    for l in locations:
        gps += str(l[0]) + ',' + str(l[1]) + '|'
    url = api.format(gps)
    res = requests.get(url)
    return res


# 批量百度转高德
def baidu_amap(locations):
    api = "http://restapi.amap.com/v3/assistant/coordinate/convert?locations={}" \
          "&coordsys=baidu&key=5cda232d2d1f782a634096167304eb59"
    gps = ""
    for l in locations:
        gps += str(l[0]) + ',' + str(l[1]) + '|'
    url = api.format(gps)
    res = requests.get(url)
    return res


# 单个GPS转高德
def gps_map(location):
    api = "http://restapi.amap.com/v3/assistant/coordinate/convert?locations={}" \
          "&coordsys=gps&key=5cda232d2d1f782a634096167304eb59"
    gps = str(location[0]) + ',' + str(location[1])
    url = api.format(gps)
    res = requests.get(url)
    return res


def gps_conversion(longitude, latitude):
    # print(longitude.split('.'))
    longitude1 = float(longitude.split('.')[0][:3])
    longitude2 = float((float(longitude[3:]) / 60))
    longitude = longitude1 + longitude2
    # print(longitude1)
    # print(longitude2)
    # print(longitude)

    latitude1 = float(latitude.split('.')[0][:2])
    latitude2 = float((float(latitude[2:]) / 60))
    latitude = latitude1 + latitude2
    # print(latitude1)
    # print(latitude2)
    # print(latitude)
    return wgs84_to_gcj02(longitude, latitude)


def check_one_net_data(value):
    msg = pynmea2.parse(value)
    return msg


def one_net_register(imei):
    data = {
        "sn": imei,
        "title": imei
    }
    res = requests.post('http://api.heclouds.com/register_de?register_code=GBzk1E9e6vd0soTE', data=json.dumps(data))
    res_data = res.json()
    errno = res_data.get('errno')
    print(res_data)
    if errno == 0:
        dev_id = res_data['data']['device_id']
        print(dev_id)
    else:
        dev_id = 0
    return imei, dev_id


# 导出Excel
def export_excel(location_infos, sheet_info, filename):
    print('utils excel')

    title = ['设备序列号', '采集时间', '经度', '纬度', '方向', '速度 m/s', '海拔/米', '测量精度', '当前电压(V)', '卫星数量']

    f = xlsxwriter.Workbook(filename)
    fsheet = f.add_worksheet(sheet_info)
    # 首行格式
    format1 = f.add_format({
        'bold': True, 'font_color': 'black', 'font_size': 13, 'align': 'center', 'font_name': '宋体'
    })
    # 内容格式
    format2 = f.add_format({'font_color': 'black', 'font_size': 12, 'align': 'center', 'font_name': '宋体'})
    format3 = f.add_format({'font_color': 'blue', 'font_size': 12, 'align': 'center', 'font_name': '宋体'})

    # 设置A-K列 宽 20
    fsheet.set_column("A:J", 20)
    # 写入首行
    for t in range(len(title)):
        fsheet.write(0, t, title[t], format1)
    # 写入数据
    for i in range(len(location_infos)):
        wt_data = location_infos[i]
        for x in range(len(wt_data)):
            fsheet.write(i + 1, x, wt_data[x], format2)
    f.close()


def get_csrf(request):
    # 生成 csrf 数据，发送给前端
    x = csrf(request)
    csrf_token = x['csrf_token']
    return csrf_token


IS_DEBUG_JPUSH = True
jpushurl = "https://api.jpush.cn/v3/push"
jpush_appkey = "e1b7e3c9f81b8b8ba1878f5a"
jpush_master_secret = "89964f45f3007a8b696df6b5"


def jpush_function_extra(username, kind, summary, content):
    """
    :param username: 别名
    :param kind: 定义类型（1-预警速度, 2-重置密码）
    :param summary: 通知标题
    :param content: 通知内容
    :return:
    """
    base64_auth_string = base64.b64encode((jpush_appkey + ":" + jpush_master_secret).encode("utf-8"))
    # print(base64_auth_string)
    # print(str(base64_auth_string, 'utf-8'))
    headers = {'content-type': 'application/json', "Authorization": "Basic " + str(base64_auth_string, 'utf-8')}
    msg = {
        "platform": "all",
        "audience":
            {"alias": [username]}
        ,
        "notification": {
            "ios": {
                "alert": summary,
                "sound": "default",
                # "badge": "+1",
                "content-available": True,
                "extras": {
                    "kind": kind,
                    "content": content
                }
            },
            "android": {
                "alert": summary,
                # "title": "智守护",
                "builder_id": 1,
                "extras": {
                    "kind": kind,
                    "content": content
                }
            }
        },
        "options": {
            "apns_production": IS_DEBUG_JPUSH,
            "apns_collapse_id": "cmx"
        }
    }
    return requests.post(jpushurl, data=json.dumps(msg), headers=headers)
