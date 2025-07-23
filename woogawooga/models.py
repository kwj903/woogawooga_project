from django.db import models
from django.utils import timezone


class AnalysisResult(models.Model):
    """분석 결과 저장 모델"""
    
    # 파일 정보
    file_name = models.CharField(max_length=255, verbose_name="파일명")
    file_size = models.IntegerField(verbose_name="파일 크기")
    file_type = models.CharField(max_length=50, verbose_name="파일 타입")
    
    # 분석 결과
    is_phishing = models.BooleanField(verbose_name="보이스피싱 여부")
    confidence = models.FloatField(verbose_name="신뢰도")
    phishing_type = models.CharField(max_length=50, null=True, blank=True, verbose_name="피싱 유형")
    
    # 상세 결과
    stt_text = models.TextField(null=True, blank=True, verbose_name="STT 변환 텍스트")
    risk_factors = models.JSONField(default=list, verbose_name="위험 요소")
    explanation = models.TextField(null=True, blank=True, verbose_name="분석 설명")
    warning_message = models.TextField(null=True, blank=True, verbose_name="경고 메시지")
    
    # 메타 정보
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    processing_time = models.FloatField(null=True, blank=True, verbose_name="처리 시간(초)")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP 주소")
    
    class Meta:
        db_table = 'voice_phishing_results'
        ordering = ['-created_at']
        verbose_name = "분석 결과"
        verbose_name_plural = "분석 결과들"
    
    def __str__(self):
        return f"{self.file_name} - {'피싱' if self.is_phishing else '정상'} ({self.confidence:.2f})"


class SystemLog(models.Model):
    """시스템 로그 모델"""
    
    LOG_LEVELS = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),  
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS, verbose_name="로그 레벨")
    message = models.TextField(verbose_name="메시지")
    file_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="관련 파일")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP 주소")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    
    class Meta:
        db_table = 'system_logs'
        ordering = ['-created_at']
        verbose_name = "시스템 로그"
        verbose_name_plural = "시스템 로그들"
    
    def __str__(self):
        return f"[{self.level}] {self.message[:50]}..."
