from django.urls import path
from . import views

app_name = 'woogawooga'

urlpatterns = [
    # 메인 페이지
    path('', views.index, name='index'),
    
    # 분석 및 결과 페이지
    path('analysis/', views.analysis, name='analysis'),
    path('result/', views.result, name='result'),
    
    # 분석 API
    path('analyze/', views.analyze, name='analyze'),
    
    # 피드백 API
    path('submit_feedback/', views.submit_feedback, name='submit_feedback'),
    
    # 프론트엔드 로깅 API
    path('log_frontend_event/', views.log_frontend_event, name='log_frontend_event'),
    
    # 분석 이력 API
    path('history/', views.get_analysis_history, name='analysis_history'),
    
    # 통계 페이지
    path('statistics/', views.statistics, name='statistics'),
]