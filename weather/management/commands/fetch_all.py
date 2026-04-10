from django.core.management.base import BaseCommand
from django.core.management import call_command
from weather.models import City

class Command(BaseCommand):
    help = "采集数据库中所有城市（遍历 City 表）"

    def add_arguments(self, parser):
        parser.add_argument("--analyze", action="store_true")
        parser.add_argument("--horizon", type=int, default=12)

    def handle(self, *args, **opts):
        cities = City.objects.all().order_by("name")
        if not cities.exists():
            self.stdout.write(self.style.WARNING("City 表为空，请先添加城市"))
            return

        for c in cities:
            self.stdout.write(self.style.WARNING(f"==> 采集：{c.name} {c.location_id}"))
            args = ["--city", c.name, "--location", c.location_id, "--horizon", str(opts["horizon"])]
            if opts["analyze"]:
                args.append("--analyze")
            call_command("fetch_weather", *args)

        self.stdout.write(self.style.SUCCESS("全部城市采集完成"))