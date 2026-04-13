from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from weather.models import City, WeatherRecord

METRIC_MAP = {
    "temp": ("temp_c", "温度(°C)"),
    "humidity": ("humidity", "湿度(%)"),
    "precip": ("precip_mm", "降水(mm)"),
    "wind": ("wind_kph", "风速(kph)"),
    "pressure": ("pressure_hpa", "气压(hPa)"),
}


def dashboard(request):
    return render(request, "weather/dashboard.html", {"default_city": settings.DEFAULT_CITY_NAME})


def api_cities(request):
    cities = list(City.objects.values("id", "name", "location_id").order_by("name"))
    return JsonResponse({"cities": cities})


def api_series(request):
    """
    GET /api/series?cities=重庆,北京&metric=temp&limit=240
    返回多个城市在同一指标下的时间序列
    """
    cities_param = (request.GET.get("cities") or settings.DEFAULT_CITY_NAME).strip()
    metric_key = (request.GET.get("metric") or "temp").strip()
    limit = int(request.GET.get("limit", "240"))

    if metric_key not in METRIC_MAP:
        return JsonResponse({"error": "invalid metric"}, status=400)

    field, label = METRIC_MAP[metric_key]
    city_names = [c.strip() for c in cities_param.split(",") if c.strip()]
    if not city_names:
        return JsonResponse({"error": "no cities"}, status=400)

    city_qs = list(City.objects.filter(name__in=city_names))
    found_names = {c.name for c in city_qs}
    missing = [n for n in city_names if n not in found_names]
    if missing:
        return JsonResponse({"error": f"city not found: {missing}"}, status=404)

    # 保持用户选择的顺序
    name_to_city = {c.name: c for c in city_qs}
    ordered = [name_to_city[n] for n in city_names if n in name_to_city]

    series = []
    for city in ordered:
        recs = list(
            WeatherRecord.objects.filter(city=city)
            .order_by("-obs_time")[:limit]
            .values("obs_time", field)
        )
        recs = list(reversed(recs))
        series.append({
            "city": city.name,
            "label": label,
            "metric": metric_key,
            "data": [[r["obs_time"].isoformat(), r[field]] for r in recs],
        })

    return JsonResponse({"metric": metric_key, "label": label, "series": series})


def api_corr(request):
    """
    GET /api/corr?city=重庆&limit=240
    返回该城市的相关性矩阵（temp/humidity/precip/wind/pressure）
    """
    city_name = request.GET.get("city") or settings.DEFAULT_CITY_NAME
    limit = int(request.GET.get("limit", "240"))

    city = City.objects.filter(name=city_name).first()
    if not city:
        return JsonResponse({"error": "city not found"}, status=404)

    rows = list(
        WeatherRecord.objects.filter(city=city)
        .order_by("-obs_time")[:limit]
        .values("obs_time", "temp_c", "humidity", "precip_mm", "wind_kph", "pressure_hpa")
    )
    rows = list(reversed(rows))
    if len(rows) < 20:
        return JsonResponse({"error": "not enough data"}, status=400)

    import pandas as pd
    df = pd.DataFrame(rows).dropna()
    if len(df) < 20:
        return JsonResponse({"error": "not enough valid data"}, status=400)

    cols = [
        ("temp_c", "温度"),
        ("humidity", "湿度"),
        ("precip_mm", "降水"),
        ("wind_kph", "风速"),
        ("pressure_hpa", "气压"),
    ]
    used = [c[0] for c in cols if c[0] in df.columns]
    labels = [name for key, name in cols if key in used]
    corr = df[used].corr().round(3)

    heat = []
    for i in range(len(used)):
        for j in range(len(used)):
            heat.append([i, j, float(corr.iloc[j, i])])

    return JsonResponse({
        "city": city.name,
        "labels": labels,
        "matrix": heat,
    })


def api_eval(request):
    """
    GET /api/eval?city=重庆&limit=720
    简单回测评估：输出 MAE / RMSE（温度）
    """
    import pandas as pd
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.ensemble import RandomForestRegressor

    city_name = request.GET.get("city") or settings.DEFAULT_CITY_NAME
    limit = int(request.GET.get("limit", "720"))

    city = City.objects.filter(name=city_name).first()
    if not city:
        return JsonResponse({"error": "city not found"}, status=404)

    rows = list(
        WeatherRecord.objects.filter(city=city)
        .order_by("obs_time")
        .values("obs_time", "temp_c")
    )
    if len(rows) < 80:
        return JsonResponse({"error": "not enough data"}, status=400)

    df = pd.DataFrame(rows).dropna().tail(limit).reset_index(drop=True)
    if len(df) < 80:
        return JsonResponse({"error": "not enough valid data"}, status=400)

    lags = [1, 2, 3, 6, 12, 24]
    for l in lags:
        df[f"lag{l}"] = df["temp_c"].shift(l)

    dt = pd.to_datetime(df["obs_time"])
    df["hour"] = dt.dt.hour
    df["dow"] = dt.dt.dayofweek

    df = df.dropna().reset_index(drop=True)
    if len(df) < 60:
        return JsonResponse({"error": "not enough feature rows"}, status=400)

    feature_cols = [f"lag{l}" for l in lags] + ["hour", "dow"]
    X = df[feature_cols].values
    y = df["temp_c"].values

    n = len(df)
    split = int(n * 0.8)
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]

    model = RandomForestRegressor(
        n_estimators=400,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(mean_squared_error(y_test, y_pred) ** 0.5)

    return JsonResponse({
        "city": city.name,
        "metric": "temp",
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
    })

def api_rank(request):
    """
    天气排行接口
    返回当前各城市最近一条记录中的：
    最高温、最低温、最高湿度
    """
    rows = []
    for city in City.objects.all():
        latest = (
            WeatherRecord.objects.filter(city=city)
            .order_by("-obs_time")
            .values("city__name", "obs_time", "temp_c", "humidity")
            .first()
        )
        if latest:
            rows.append({
                "city": latest["city__name"],
                "obs_time": latest["obs_time"].isoformat() if latest["obs_time"] else "",
                "temp_c": latest["temp_c"],
                "humidity": latest["humidity"],
            })

    if not rows:
        return JsonResponse({"error": "no data"}, status=400)

    valid_temp = [r for r in rows if r["temp_c"] is not None]
    valid_humidity = [r for r in rows if r["humidity"] is not None]

    highest_temp = max(valid_temp, key=lambda x: x["temp_c"]) if valid_temp else None
    lowest_temp = min(valid_temp, key=lambda x: x["temp_c"]) if valid_temp else None
    highest_humidity = max(valid_humidity, key=lambda x: x["humidity"]) if valid_humidity else None

    return JsonResponse({
        "highest_temp": highest_temp,
        "lowest_temp": lowest_temp,
        "highest_humidity": highest_humidity,
    })


def api_table(request):
    """
    原始天气数据表格接口
    GET /api/table?city=重庆&limit=10
    """
    city_name = request.GET.get("city") or settings.DEFAULT_CITY_NAME
    limit = int(request.GET.get("limit", "10"))

    city = City.objects.filter(name=city_name).first()
    if not city:
        return JsonResponse({"error": "city not found"}, status=404)

    rows = list(
        WeatherRecord.objects.filter(city=city)
        .order_by("-obs_time")[:limit]
        .values("obs_time", "temp_c", "humidity", "precip_mm", "wind_kph", "pressure_hpa")
    )

    data = []
    for r in rows:
        data.append({
            "obs_time": r["obs_time"].strftime("%Y-%m-%d %H:%M:%S") if r["obs_time"] else "",
            "temp_c": r["temp_c"],
            "humidity": r["humidity"],
            "precip_mm": r["precip_mm"],
            "wind_kph": r["wind_kph"],
            "pressure_hpa": r["pressure_hpa"],
        })

    return JsonResponse({
        "city": city.name,
        "rows": data,
    })

def _calc_temp_trend(values):
    clean = [float(v) for v in values if v is not None]
    if len(clean) < 3:
        return {"label": "数据不足", "delta": None}

    half = max(1, len(clean) // 2)
    early_avg = sum(clean[:half]) / len(clean[:half])
    late_avg = sum(clean[half:]) / len(clean[half:])
    delta = round(late_avg - early_avg, 2)

    if delta >= 1:
        label = "上升"
    elif delta <= -1:
        label = "下降"
    else:
        label = "平稳"
    return {"label": label, "delta": delta}


def api_summary(request):
    """
    城市概览接口
    GET /api/summary?city=重庆&limit=240
    返回数据量、均温、历史极值、趋势判断等摘要信息
    """
    city_name = request.GET.get("city") or settings.DEFAULT_CITY_NAME
    limit = int(request.GET.get("limit", "240"))

    city = City.objects.filter(name=city_name).first()
    if not city:
        return JsonResponse({"error": "city not found"}, status=404)

    latest = (
        WeatherRecord.objects.filter(city=city)
        .order_by("-obs_time")
        .values("obs_time", "temp_c", "humidity")
        .first()
    )
    if not latest:
        return JsonResponse({"error": "no data"}, status=400)

    recent_rows = list(
        WeatherRecord.objects.filter(city=city)
        .order_by("-obs_time")[:limit]
        .values("obs_time", "temp_c", "humidity")
    )
    recent_rows = list(reversed(recent_rows))

    total_records = WeatherRecord.objects.filter(city=city).count()
    valid_temps = [r["temp_c"] for r in recent_rows if r["temp_c"] is not None]
    valid_humidity = [r["humidity"] for r in recent_rows if r["humidity"] is not None]

    avg_temp = round(sum(valid_temps) / len(valid_temps), 2) if valid_temps else None
    max_temp = round(max(valid_temps), 2) if valid_temps else None
    min_temp = round(min(valid_temps), 2) if valid_temps else None
    avg_humidity = round(sum(valid_humidity) / len(valid_humidity), 2) if valid_humidity else None

    trend = _calc_temp_trend(valid_temps[-6:])

    return JsonResponse({
        "city": city.name,
        "total_records": total_records,
        "latest_time": latest["obs_time"].isoformat() if latest["obs_time"] else "",
        "latest_temp": latest["temp_c"],
        "avg_temp": avg_temp,
        "max_temp": max_temp,
        "min_temp": min_temp,
        "avg_humidity": avg_humidity,
        "trend_label": trend["label"],
        "trend_delta": trend["delta"],
    })
