from django.urls import path
from .views import DataView, AiView, ProvinceView, PredictView


urlpatterns = [
    path('data/', DataView.as_view(), name='items'),
    path('ai/', AiView.as_view(), name='items'),
    path('province/', ProvinceView.as_view(), name='items'),
    path('predict/', PredictView.as_view(), name='items'),
]