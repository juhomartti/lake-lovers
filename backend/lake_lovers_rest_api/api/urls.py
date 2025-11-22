from django.urls import path
from .views import DataView, AiView, ProvinceView


urlpatterns = [
    path('data/', DataView.as_view(), name='items'),
    path('ai/', AiView.as_view(), name='items'),
    path('province/', ProvinceView.as_view(), name='items'),
]