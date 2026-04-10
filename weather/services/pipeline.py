from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_aware
from weather.models import WeatherRecord, ForecastPoint, AnomalyPoint, City
from .ml import train_and_predict_temp, detect_anomalies_simple

def _aware(dt):
    if dt is None:
        return None
    return dt if is_aware(dt) else make_aware(dt)

def ingest_hourly_24h(city: City, payload: dict) -> int:
    hourly = payload.get("hourly", [])
    count = 0
    for h in hourly:
        # v7/weather/24h 字段：fxTime, temp, humidity, precip, windSpeed, pressure
        dt = _aware(parse_datetime(h.get("fxTime") or h.get("obsTime") or ""))
        if not dt:
            continue

        def f(x):
            return float(x) if x is not None and x != "" else None

        obj, created = WeatherRecord.objects.update_or_create(
            city=city,
            obs_time=dt,
            defaults={
                "temp_c": f(h.get("temp")),
                "humidity": f(h.get("humidity")),
                "precip_mm": f(h.get("precip")),
                "wind_kph": f(h.get("windSpeed")),
                "pressure_hpa": f(h.get("pressure")),
            }
        )
        if created:
            count += 1
    return count

def run_analysis(city: City, horizon_hours: int = 12) -> dict:
    import pandas as pd

    qs = WeatherRecord.objects.filter(city=city).order_by("obs_time")[:24*30]  # 最多近30天
    rows = list(qs.values("obs_time", "temp_c", "humidity", "precip_mm", "wind_kph", "pressure_hpa"))
    if len(rows) < 48:
        return {"ok": False, "msg": "数据太少：至少收集48小时再分析/预测"}

    df = pd.DataFrame(rows).dropna(subset=["temp_c"]).sort_values("obs_time")
    if len(df) < 48:
        return {"ok": False, "msg": "有效温度数据不足"}

    # 预测（温度）
    pred_df = train_and_predict_temp(df, horizon_hours=horizon_hours, model_name="rf_lag")
    for _, r in pred_df.iterrows():
        ForecastPoint.objects.update_or_create(
            city=city,
            target_time=r["target_time"].to_pydatetime(),
            model_name=r["model_name"],
            defaults={"yhat_temp_c": float(r["yhat_temp_c"])}
        )

    # 异常检测（温度）
    anomalies = detect_anomalies_simple(df, metric="temp_c")
    for a in anomalies:
        AnomalyPoint.objects.update_or_create(
            city=city,
            time=a["time"].to_pydatetime(),
            metric="temp_c",
            defaults={
                "value": float(a["value"]),
                "score": float(a["score"]),
                "reason": a["reason"],
            }
        )

    return {"ok": True, "forecast_points": int(len(pred_df)), "anomalies": int(len(anomalies))}
