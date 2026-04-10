from django.apps import AppConfig
import os

class WeatherConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "weather"

    def ready(self):
        # 防止某些情况下重复启动调度器
        if os.environ.get("SCHEDULER_STARTED") == "1":
            return
        os.environ["SCHEDULER_STARTED"] = "1"

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from django.core.management import call_command
        except Exception as e:
            print("导入调度器失败：", e)
            return

        # 先启动时立刻抓一次数据
        try:
            call_command("fetch_weather", "--analyze", "--horizon", "12")
            print("启动时已执行 fetch_weather")
        except Exception as e:
            print("启动时抓取天气失败：", e)

        # 再启动定时任务
        try:
            scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
            scheduler.add_job(
                lambda: call_command("fetch_weather", "--analyze", "--horizon", "12"),
                trigger="interval",
                minutes=30,
                id="fetch_weather_job",
                replace_existing=True,
            )
            scheduler.start()
            print("✅ APScheduler 已启动，每30分钟执行一次 fetch_weather")
        except Exception as e:
            print("启动定时任务失败：", e)