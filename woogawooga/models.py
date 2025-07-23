from django.db import models
from django.utils import timezone
import uuid


class ProcessdFile(models.Model):
    """처리된 파일 정보 모델"""
    
    ocrn_no = models.CharField(max_length=50, primary_key=True, verbose_name="발생번호")
    ocrn_hm = models.DateTimeField(verbose_name="발생시분")
    trsc_file_nm = models.CharField(max_length=300, null=True, blank=True, verbose_name="전사파일명")
    transcript = models.TextField(verbose_name="전사내용")
    prcs_cont_1 = models.JSONField(verbose_name="1차 전처리내용")
    prcs_cont_2 = models.JSONField(null=True, blank=True, verbose_name="2차 전처리내용")
    vldtn_yn = models.CharField(max_length=1, verbose_name="유효성 여부")
    stats_file_path = models.CharField(max_length=200, verbose_name="통계파일경로")
    file_path = models.CharField(max_length=200, verbose_name="파일경로")
    
    class Meta:
        db_table = 'ProcessdFile'
        verbose_name = "처리된 파일"
        verbose_name_plural = "처리된 파일들"
    
    def __str__(self):
        return f"{self.ocrn_no} - {self.trsc_file_nm}"


class ModelRegistry(models.Model):
    """모델 레지스트리"""
    
    mdl_id = models.CharField(max_length=20, primary_key=True, verbose_name="모델ID")
    mdl_nm = models.CharField(max_length=100, verbose_name="모델명")
    use_yn = models.CharField(max_length=1, verbose_name="사용여부")
    
    class Meta:
        db_table = 'ModelRegistry'
        verbose_name = "모델 레지스트리"
        verbose_name_plural = "모델 레지스트리들"
    
    def __str__(self):
        return f"{self.mdl_id} - {self.mdl_nm}"


class InferenceResult(models.Model):
    """추론 결과 모델"""
    
    ML_RESULT_CHOICES = [
        ('0', '정상'),
        ('1', '피싱'),
        ('보류', '보류'),
    ]
    
    rslt_id = models.CharField(max_length=50, verbose_name="결과ID")
    ocrn_no = models.ForeignKey(ProcessdFile, on_delete=models.CASCADE, verbose_name="발생번호")
    mdl_id = models.CharField(max_length=20, verbose_name="모델ID")
    file_id = models.CharField(max_length=20, verbose_name="파일ID")
    prdt_scr = models.DecimalField(max_digits=4, decimal_places=3, verbose_name="예측점수")
    ml_rslt_cd = models.CharField(max_length=10, choices=ML_RESULT_CHOICES, verbose_name="ML결과코드")
    dl_jdgm_yn = models.CharField(max_length=1, null=True, blank=True, verbose_name="DL판단여부")
    phsh_tp_nm = models.CharField(max_length=100, verbose_name="피싱유형명")
    warn_cn = models.TextField(verbose_name="경고내용")
    prdt_dt = models.DateTimeField(verbose_name="예측일시")
    
    class Meta:
        db_table = 'InferenceResult'
        verbose_name = "추론 결과"
        verbose_name_plural = "추론 결과들"
        unique_together = [['rslt_id', 'ocrn_no']]
    
    def __str__(self):
        return f"{self.rslt_id} - {self.get_ml_rslt_cd_display()}"


class Feedback(models.Model):
    """피드백 모델"""
    
    prp_no = models.CharField(max_length=20, verbose_name="제안번호")
    rslt_id = models.CharField(max_length=50, verbose_name="결과ID")
    ocrn_no = models.CharField(max_length=50, verbose_name="발생번호")
    prdt_rslt_yn = models.CharField(max_length=1, verbose_name="예측결과여부")
    wropn_cn = models.TextField(null=True, blank=True, verbose_name="의견내용")
    opnn_reg_ymd = models.DateTimeField(null=True, blank=True, verbose_name="의견등록일시")
    
    class Meta:
        db_table = 'feedback'
        verbose_name = "피드백"
        verbose_name_plural = "피드백들"
        unique_together = [['prp_no', 'rslt_id', 'ocrn_no']]
    
    def __str__(self):
        return f"{self.prp_no} - {self.rslt_id}"


class VoicePhishingSystemLog(models.Model):
    """새로운 시스템 로그 모델"""
    
    log_nm = models.CharField(max_length=300, verbose_name="로그명")
    ocrn_no = models.ForeignKey(ProcessdFile, on_delete=models.CASCADE, verbose_name="발생번호")
    err_no = models.CharField(max_length=20, null=True, blank=True, verbose_name="에러번호")
    log_reg_dt = models.DateTimeField(verbose_name="로그등록일시")
    log_ocrn_pstn = models.CharField(max_length=200, verbose_name="로그발생위치")
    err_rsn = models.TextField(null=True, blank=True, verbose_name="에러사유")
    err_cd_nm = models.CharField(max_length=300, null=True, blank=True, verbose_name="에러코드명")
    
    class Meta:
        db_table = 'SystemLog'
        verbose_name = "시스템 로그"
        verbose_name_plural = "시스템 로그들"
        unique_together = [['log_nm', 'ocrn_no']]
    
    def __str__(self):
        return f"{self.log_nm} - {self.log_ocrn_pstn}"


class SystemLog(models.Model):
    """기존 시스템 로그 모델 (호환성 유지)"""
    
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
        verbose_name = "기존 시스템 로그"
        verbose_name_plural = "기존 시스템 로그들"
    
    def __str__(self):
        return f"[{self.level}] {self.message[:50]}..."


# 기존 모델들 (호환성을 위해 유지)
class AnalysisResult(models.Model):
    """분석 결과 저장 모델 (기존 UI 호환용)"""
    
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
