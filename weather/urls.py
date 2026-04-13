from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/cities", views.api_cities, name="api_cities"),
    path("api/series", views.api_series, name="api_series"),
    path("api/corr", views.api_corr, name="api_corr"),
    path("api/eval", views.api_eval, name="api_eval"),
    path("api/rank", views.api_rank, name="api_rank"),
    path("api/table", views.api_table, name="api_table"),
    path("api/summary", views.api_summary, name="api_summary"),
]