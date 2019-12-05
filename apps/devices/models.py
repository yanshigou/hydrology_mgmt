from django.db import models
from station.models import StationInfo


class DevicesInfo(models.Model):
    device_id = models.CharField(max_length=20, verbose_name="仪器编号", unique=True)
    station = models.ForeignKey(StationInfo, verbose_name="测站点")
    name = models.CharField(max_length=50, verbose_name='仪器名称')
    device_type = models.CharField(max_length=20, verbose_name="仪器类型")
    install_method = models.CharField(max_length=10, verbose_name="安装方式")
    fs_direction = models.CharField(max_length=10, verbose_name="发射方向")
    start_point = models.CharField(max_length=20, verbose_name="起点")
    offset = models.CharField(max_length=20, verbose_name="偏移")
    # elevation = models.CharField(max_length=20, verbose_name="高程")
    device_status = models.BooleanField(default=True, verbose_name="仪器状态")
    longitude = models.CharField(max_length=30, verbose_name='经度')
    latitude = models.CharField(max_length=30, verbose_name='纬度')

    class Meta:
        verbose_name = 'ADCP设备信息表'
        verbose_name_plural = verbose_name
