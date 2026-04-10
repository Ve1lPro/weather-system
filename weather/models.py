from django.db import models

class City(models.Model):
    name = models.CharField(max_length=64, unique=True)
    location_id = models.CharField(max_length=32, unique=True)

    def __str__(self) -> str:
        return f"{self.name}({self.location_id})"


class WeatherRecord(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    obs_time = models.DateTimeField(db_index=True)  # 小时级时间点
    temp_c = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    precip_mm = models.FloatField(null=True, blank=True)
    wind_kph = models.FloatField(null=True, blank=True)
    pressure_hpa = models.FloatField(null=True, blank=True)

    source = models.CharField(max_length=32, default="qweather")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("city", "obs_time")
        ordering = ["-obs_time"]

    def __str__(self) -> str:
        return f"{self.city.name} {self.obs_time} {self.temp_c}°C"


class ForecastPoint(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    target_time = models.DateTimeField(db_index=True)
    yhat_temp_c = models.FloatField()
    model_name = models.CharField(max_length=64, default="rf_lag")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("city", "target_time", "model_name")
        ordering = ["-target_time"]


class AnomalyPoint(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    time = models.DateTimeField(db_index=True)
    metric = models.CharField(max_length=32)
    value = models.FloatField()
    score = models.FloatField()
    reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("city", "time", "metric")
        ordering = ["-time"]
