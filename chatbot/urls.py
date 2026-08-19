from django.urls import path
from .views import chat_api_view, improve_campaign_view, funding_prediction_view, analytics_dashboard_view

urlpatterns = [
    path("chat/", chat_api_view, name="chat_api"),
    path("improve-campaign/", improve_campaign_view, name="improve_campaign"),
    path("funding-prediction/", funding_prediction_view, name="funding_prediction"),
    path("dashboard/", analytics_dashboard_view, name="analytics_dashboard"),
]