/**
 * 브라우저 캐시 문제 해결을 위한 스크립트
 */

// 페이지 로드 시 브라우저 캐시 강제 새로고침
document.addEventListener('DOMContentLoaded', function() {
    console.log('캐시 수정 스크립트 로드됨');
    
    // 새로운 분석을 위한 피드백 폼 완전 초기화
    setTimeout(() => {
        resetAllFeedbackElements();
    }, 100);
    
    // 기존 submitFeedback 함수가 제대로 작동하지 않으면 강제로 대체
    if (typeof window.submitFeedback === 'function') {
        console.log('기존 submitFeedback 함수 발견 - 강제 교체');
    }
    
    // 최종 피드백 제출 함수 (모든 오류 해결)
    window.submitFeedback = async function() {
        console.log('최종 수정된 submitFeedback 함수 실행');
        
        try {
            // 라디오 버튼 요소들 찾기 (여러 가능한 name 속성 시도)
            let feedbackRadio = document.querySelector('input[name="feedback"]:checked') ||
                               document.querySelector('input[name="feedback-accuracy"]:checked');
            
            const commentElement = document.getElementById('feedbackComment') || 
                                 document.getElementById('feedback-comment');
            const submitBtn = document.getElementById('submitFeedbackBtn') || 
                            document.getElementById('submit-feedback-btn');
            
            console.log('피드백 요소들:', {
                feedbackRadio: feedbackRadio,
                commentElement: commentElement,
                submitBtn: submitBtn
            });
            
            if (!feedbackRadio) {
                alert('분석 결과에 대한 의견을 선택해주세요.');
                return;
            }
            
            // URL에서 taskId 가져오기
            const urlParams = new URLSearchParams(window.location.search);
            const taskId = urlParams.get('taskId');
            
            // 로컬 스토리지에서 분석 결과 가져오기
            const analysisResultStr = localStorage.getItem('analysisResult');
            let analysisResult = {};
            
            if (analysisResultStr) {
                try {
                    analysisResult = JSON.parse(analysisResultStr);
                } catch (e) {
                    console.error('분석 결과 파싱 오류:', e);
                }
            }
            
            console.log('분석 결과 데이터:', analysisResult);
            
            // ID 정보 추출
            const rslt_id = analysisResult.rslt_id || taskId || 'unknown';
            const ocrn_no = analysisResult.ocrn_no || taskId || 'unknown';
            
            const feedbackData = {
                rslt_id: rslt_id,
                ocrn_no: ocrn_no,
                user_prediction: feedbackRadio.value,
                comment: commentElement ? commentElement.value.trim() : ''
            };
            
            console.log('전송할 피드백 데이터:', feedbackData);
            
            // 제출 버튼 상태 변경
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 제출 중...';
            }
            
            // CSRF 토큰 가져오기
            function getCsrfToken() {
                const csrfMeta = document.querySelector('meta[name="csrf-token"]');
                if (csrfMeta) {
                    return csrfMeta.getAttribute('content');
                }
                const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
                if (csrfInput) {
                    return csrfInput.value;
                }
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {
                    const [name, value] = cookie.trim().split('=');
                    if (name === 'csrftoken') {
                        return value;
                    }
                }
                return '';
            }
            
            const csrfToken = getCsrfToken();
            console.log('CSRF 토큰:', csrfToken ? '있음' : '없음');
            
            // 서버에 피드백 전송
            const response = await fetch('/submit_feedback/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(feedbackData)
            });
            
            console.log('피드백 응답 상태:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: 서버 오류가 발생했습니다.`);
            }
            
            const result = await response.json();
            console.log('피드백 응답 결과:', result);
            
            if (result.success) {
                alert('피드백이 성공적으로 제출되었습니다. 감사합니다!');
                
                // 폼 비활성화
                const allRadios = document.querySelectorAll('input[name="feedback"], input[name="feedback-accuracy"]');
                allRadios.forEach(radio => radio.disabled = true);
                
                if (commentElement) {
                    commentElement.disabled = true;
                }
                
                // 버튼 완료 상태로 변경
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-check"></i> 제출 완료';
                    submitBtn.style.backgroundColor = '#10b981';
                }
            } else {
                throw new Error(result.error || '피드백 제출에 실패했습니다.');
            }
            
        } catch (error) {
            console.error('피드백 제출 오류:', error);
            alert('피드백 제출 중 오류가 발생했습니다: ' + error.message);
            
            // 제출 버튼 복원
            const submitBtn = document.getElementById('submitFeedbackBtn') || 
                            document.getElementById('submit-feedback-btn');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 피드백 제출';
            }
        }
    };
    
    // 피드백 폼 완전 초기화 함수
    window.resetAllFeedbackElements = function() {
        console.log('모든 피드백 요소 초기화 시작');
        
        // 라디오 버튼 초기화
        const radioButtons = document.querySelectorAll('input[name="feedback"], input[name="feedback-accuracy"]');
        radioButtons.forEach(radio => {
            radio.checked = false;
            radio.disabled = false;
        });
        
        // 텍스트 영역 초기화
        const textareas = ['feedbackComment', 'feedback-comment'];
        textareas.forEach(id => {
            const textarea = document.getElementById(id);
            if (textarea) {
                textarea.value = '';
                textarea.disabled = false;
            }
        });
        
        // 문자 카운터 초기화
        const charCount = document.getElementById('charCount');
        if (charCount) {
            charCount.textContent = '0';
            charCount.style.color = '#6b7280';
        }
        
        // 제출 버튼 초기화
        const submitBtns = ['submitFeedbackBtn', 'submit-feedback-btn'];
        submitBtns.forEach(id => {
            const submitBtn = document.getElementById(id);
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 피드백 제출';
                submitBtn.style.backgroundColor = '';
            }
        });
        
        // 피드백 섹션 숨기기
        const feedbackSection = document.getElementById('feedbackSection');
        if (feedbackSection) {
            feedbackSection.style.display = 'none';
        }
        
        // 피드백 버튼 다시 표시
        const feedbackBtn = document.getElementById('feedbackBtn');
        if (feedbackBtn) {
            feedbackBtn.style.display = 'inline-flex';
        }
        
        // 모든 성공/에러 메시지 제거
        const allMessages = document.querySelectorAll('.feedback-success, .feedback-error, #feedbackSuccess, #feedbackError');
        allMessages.forEach(msg => {
            if (msg.parentNode) {
                msg.remove();
            }
        });
        
        console.log('모든 피드백 요소 초기화 완료');
    };
    
    // 다시 분석 및 홈으로 버튼에 초기화 함수 연결
    const retryBtn = document.querySelector('button[onclick="retryAnalysis()"]');
    const homeBtn = document.querySelector('button[onclick="goHome()"]');
    
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            console.log('다시 분석 버튼 클릭 - 피드백 초기화');
            resetAllFeedbackElements();
        });
    }
    
    if (homeBtn) {
        homeBtn.addEventListener('click', () => {
            console.log('홈으로 버튼 클릭 - 피드백 초기화');
            resetAllFeedbackElements();
        });
    }
    
    console.log('캐시 수정 완료 - 최종 submitFeedback 함수 준비됨');
});