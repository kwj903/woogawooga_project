from django.urls import path
from . import views

app_name = 'woogawooga'

urlpatterns = [
    # 메인 페이지
    path('', views.index, name='index'),
    
    
    # 분석 API
    path('analyze/', views.analyze, name='analyze'),
    
    # 피드백 API
    path('submit_feedback/', views.submit_feedback, name='submit_feedback'),
    
    # 분석 이력 API
    path('history/', views.get_analysis_history, name='analysis_history'),
    
    # 통계 페이지
    path('statistics/', views.statistics, name='statistics'),
]