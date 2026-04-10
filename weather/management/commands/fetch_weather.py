from django.core.management.base import BaseCommand
from django.conf import settings
from weather.models import City
from weather.services.qweather_client import QWeatherClient
from weather.services.pipeline import ingest_hourly_24h, run_analysis

class Command(BaseCommand):
    help = "拉取和风天气24h小时数据入库，可选进行分析/预测/异常检测"

    def add_arguments(self, parser):
        parser.add_argument("--city", type=str, default=settings.DEFAULT_CITY_NAME)
        parser.add_argument("--location", type=str, default=settings.DEFAULT_LOCATION_ID)
        parser.add_argument("--analyze", action="store_true")
        parser.add_argument("--horizon", type=int, default=12)

    def handle(self, *args, **opts):
        city_name = opts["city"]
        location_id = opts["location"]

        if not location_id:
            raise RuntimeError("DEFAULT_LOCATION_ID 未配置（或命令行未提供 --location）")

        city, _ = City.objects.get_or_create(name=city_name, defaults={"location_id": location_id})
        if city.location_id != location_id:
            city.location_id = location_id
            city.save()

        client = QWeatherClient(settings.QWEATHER_API_HOST, settings.QWEATHER_API_KEY)
        payload = client.hourly_24h(location_id=city.location_id)

        n = ingest_hourly_24h(city, payload)
        self.stdout.write(self.style.SUCCESS(f"入库完成：新增 {n} 条（城市：{city.name}）"))

        if opts["analyze"]:
            res = run_analysis(city, horizon_hours=opts["horizon"])
            self.stdout.write(self.style.SUCCESS(f"分析完成：{res}"))
