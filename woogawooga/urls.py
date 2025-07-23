from django.urls import path
from . import views

app_name = 'woogawooga'

urlpatterns = [
    # 메인 페이지
    path('', views.index, name='index'),
    
    # 업로드 페이지
    path('upload/', views.upload, name='upload'),
    
    # 분석 페이지
    path('analysis/', views.analysis, name='analysis'),
    path('analysis/<str:task_id>/', views.analysis_detail, name='analysis_detail'),
    
    # 결과 페이지
    path('result/', views.result, name='result'),
    path('result/<str:task_id>/', views.result_detail, name='result_detail'),
    
    # API 엔드포인트 (AJAX 호출용)
    path('api/upload/', views.api_upload, name='api_upload'),
    path('api/start-analysis/', views.api_start_analysis, name='api_start_analysis'),
    path('api/analysis-status/<str:task_id>/', views.api_analysis_status, name='api_analysis_status'),
    path('api/result/<str:task_id>/', views.api_result, name='api_result'),
]