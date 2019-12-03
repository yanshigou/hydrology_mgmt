from django.db import models


class StationInfo(models.Model):
    station_name = models.CharField(max_length=50, verbose_name="站名")
    station_code = models.CharField(max_length=20, verbose_name="站码")
    river = models.CharField(max_length=20, verbose_name="河流")
