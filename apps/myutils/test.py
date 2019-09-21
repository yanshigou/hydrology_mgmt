# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/9/5"
import requests
import json

url = 'http://192.168.31.54:8000/dataInfo/upload/'
data_dict = {
    "imei": "13370763530",
    "time": "2019-09-05 17:32:18",
    "up_time": "2019-09-05 17:32:18",
    "longitude": "106.52533",
    "latitude": "29.51934",
    "altitude": "1",
    "speed": "253",
    "direction": "1",
    "accuracy": "1",
    "power": "1",
    "satellites": "1",
    "real_satellites": "1"
}
headers = {"Content-Type": "application/json"}
res = requests.post(url, data=json.dumps(data_dict), headers=headers)
print(res)
print(res.json())
