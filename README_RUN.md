# 运行说明（PyCharm/命令行通用）

## 1. 安装依赖
pip install -r requirements.txt

## 2. 配置环境变量
复制 .env.example 为 .env，并填写：
- QWEATHER_API_KEY
- DEFAULT_LOCATION_ID（和风后台可查城市 LocationID）

## 3. 初始化数据库
python manage.py makemigrations
python manage.py migrate

## 4. 采集 + 分析/预测/异常
python manage.py fetch_weather --analyze --horizon 12

## 5. 启动
python manage.py runserver
打开：http://127.0.0.1:8000/
