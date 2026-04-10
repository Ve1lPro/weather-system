from django.core.management.base import BaseCommand
from weather.models import City
from weather.services.pipeline import run_analysis

class Command(BaseCommand):
    help = "对所有城市重跑分析/预测/异常（温度）"

    def add_arguments(self, parser):
        parser.add_argument("--horizon", type=int, default=12)

    def handle(self, *args, **opts):
        for city in City.objects.all():
            res = run_analysis(city, horizon_hours=opts["horizon"])
            self.stdout.write(self.style.SUCCESS(f"{city.name}: {res}"))
