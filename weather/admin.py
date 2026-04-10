from django.contrib import admin
from .models import City, WeatherRecord, ForecastPoint, AnomalyPoint


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location_id")
    search_fields = ("name", "location_id")


@admin.register(WeatherRecord)
class WeatherRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id", "city", "obs_time", "temp_c", "humidity",
        "precip_mm", "wind_kph", "pressure_hpa", "source"
    )
    list_filter = ("city", "source")
    search_fields = ("city__name",)
    ordering = ("-obs_time",)


@admin.register(ForecastPoint)
class ForecastPointAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "target_time", "yhat_temp_c", "model_name", "created_at")
    list_filter = ("city", "model_name")
    search_fields = ("city__name",)
    ordering = ("-target_time",)


@admin.register(AnomalyPoint)
class AnomalyPointAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "time", "metric", "value", "score", "reason")
    list_filter = ("city", "metric")
    search_fields = ("city__name", "reason")
    ordering = ("-time",)