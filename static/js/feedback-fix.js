/**
 * 피드백 제출 문제 해결을 위한 강제 수정 스크립트
 * 이 스크립트는 result.html에서 로드되어 올바른 URL로 피드백을 제출합니다.
 */

// 페이지 로드 후 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('피드백 수정 스크립트 로드됨');
    
    // 기존 피드백 제출 함수들을 모두 덮어쓰기
    window.submitFeedback = async function() {
        console.log('수정된 submitFeedback 함수 실행');
        
        try {
            // 폼 데이터 수집
            const feedbackValue = document.querySelector('input[name="feedback"]:checked')
            const commentText = document.getElementById('feedbackComment').value.trim()
            
            if (!feedbackValue) {
                alert('분석 결과에 대한 의견을 선택해주세요.')
                return
            }
            
            // 분석 결과에서 필요한 정보 추출
            const urlParams = new URLSearchParams(window.location.search)
            const taskId = urlParams.get('taskId')
            
            // 로컬 스토리지에서 분석 결과 가져오기
            const analysisResultStr = localStorage.getItem('analysisResult')
            const analysisResult = analysisResultStr ? JSON.parse(analysisResultStr) : {}
            
            console.log('분석 결과 데이터:', analysisResult)
            
            // 실제 분석 결과에서 rslt_id와 ocrn_no 가져오기
            let rslt_id = analysisResult.rslt_id || taskId
            let ocrn_no = analysisResult.ocrn_no || taskId
            
            console.log('사용할 ID:', { rslt_id, ocrn_no })
            
            if (!rslt_id || !ocrn_no) {
                alert('분석 결과 정보를 찾을 수 없습니다. 페이지를 새로고침하고 다시 분석해주세요.')
                return
            }
            
            const feedbackData = {
                rslt_id: rslt_id,
                ocrn_no: ocrn_no,
                user_prediction: feedbackValue.value,
                comment: commentText
            }
            
            console.log('전송할 피드백 데이터:', feedbackData)
            
            // 제출 버튼 비활성화
            const submitBtn = document.getElementById('submitFeedbackBtn')
            if (submitBtn) {
                submitBtn.disabled = true
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 제출 중...'
            }
            
            // CSRF 토큰 가져오기
            function getCsrfToken() {
                const csrfMeta = document.querySelector('meta[name="csrf-token"]')
                if (csrfMeta) {
                    return csrfMeta.getAttribute('content')
                }
                const cookies = document.cookie.split(';')
                for (let cookie of cookies) {
                    const [name, value] = cookie.trim().split('=')
                    if (name === 'csrftoken') {
                        return value
                    }
                }
                return ''
            }
            
            const csrfToken = getCsrfToken()
            console.log('CSRF 토큰:', csrfToken ? '있음' : '없음')
            
            // 서버에 피드백 전송 (올바른 URL 사용)
            const response = await fetch('/submit_feedback/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(feedbackData)
            })
            
            console.log('피드백 응답 상태:', response.status)
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: 서버 오류가 발생했습니다.`)
            }
            
            const result = await response.json()
            console.log('피드백 응답 결과:', result)
            
            if (result.success) {
                // 성공 메시지 표시
                alert('피드백이 성공적으로 제출되었습니다. 감사합니다!')
                
                // 폼 비활성화
                const radioButtons = document.querySelectorAll('input[name="feedback"]')
                radioButtons.forEach(radio => radio.disabled = true)
                const textarea = document.getElementById('feedbackComment')
                if (textarea) textarea.disabled = true
                
                // 버튼 완료 상태로 변경
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-check"></i> 제출 완료'
                    submitBtn.style.backgroundColor = '#10b981'
                }
            } else {
                throw new Error(result.error || '피드백 제출에 실패했습니다.')
            }
            
        } catch (error) {
            console.error('피드백 제출 오류:', error)
            alert('피드백 제출 중 오류가 발생했습니다: ' + error.message)
            
            // 제출 버튼 복원
            const submitBtn = document.getElementById('submitFeedbackBtn')
            if (submitBtn) {
                submitBtn.disabled = false
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 피드백 제출'
            }
        }
    }
    
    console.log('피드백 수정 완료 - submitFeedback 함수가 덮어써졌습니다.')
});