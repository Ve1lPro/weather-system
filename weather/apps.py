from django.apps import AppConfig

class WeatherConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "weather"

    def ready(self):
        """可选：runserver 时启动定时拉取任务（Windows/PyCharm 下也能用）。
        如果你不想自动跑，把下面整个 ready() 内容注释掉即可。
        """
        import os
        # 避免 Django 自动重载时重复启动
        if os.environ.get("RUN_MAIN") != "true":
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from django.core.management import call_command
        except Exception:
            return

        scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        scheduler.add_job(
            lambda: call_command("fetch_weather", "--analyze", "--horizon", "12"),
            trigger="interval",
            minutes=30,
            id="fetch_weather_job",
            replace_existing=True,
        )
        scheduler.start()
