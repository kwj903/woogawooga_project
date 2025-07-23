from django.urls import path
from . import views

app_name = 'voice_phishing'

urlpatterns = [
    # 메인 페이지
    path('', views.index, name='index'),
    
    # 분석 API
    path('analyze/', views.analyze, name='analyze'),
    
    # 통계 페이지
    path('statistics/', views.statistics, name='statistics'),
]