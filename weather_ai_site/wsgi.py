"""
WSGI config for weather_ai_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see:
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# 指定 Django settings 模块
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weather_ai_site.settings")

# WSGI 应用对象（runserver / 部署时都会用到）
application = get_wsgi_application()