// 결과 페이지 전용 JavaScript

let currentTaskId = null
let analysisResult = null

// DOM 요소들
const loadingSection = document.getElementById("loadingSection")
const errorResult = document.getElementById("errorResult")
const resultCard = document.getElementById("resultCard")
const resultBadge = document.getElementById("resultBadge")
const resultText = document.getElementById("resultText")
const finalResult = document.getElementById("finalResult")
const phishingType = document.getElementById("phishingType")
const confidence = document.getElementById("confidence")
const warningMessage = document.getElementById("warningMessage")
const warningText = document.getElementById("warningText")
const errorMessage = document.getElementById("errorMessage")

// 페이지 초기화
function initializeResult() {
  // 피드백 폼 초기화 (새로운 분석을 위해)
  resetFeedbackForm()
  
  // Task ID 가져오기
  currentTaskId = getUrlParameter("taskId") || getFromStorage("currentTaskId")

  if (!currentTaskId) {
    showError("작업 ID를 찾을 수 없습니다.")
    return
  }

  // 결과 로드
  loadAnalysisResult()
}

// 분석 결과 로드
function loadAnalysisResult() {
  // 로컬 스토리지에서 결과 가져오기
  const analysisResultStr = localStorage.getItem("analysisResult")
  
  if (analysisResultStr) {
    try {
      analysisResult = JSON.parse(analysisResultStr)
      console.log('로드된 분석 결과:', analysisResult)
      
      // API 결과 유효성 검증
      if (analysisResult && analysisResult.success !== false) {
        console.log('분석 결과 표시 시작')
        displayResult(analysisResult)
      } else {
        console.warn('분석 결과가 유효하지 않음:', analysisResult)
        showError("분석이 실패했습니다. 다시 분석해주세요.")
      }
    } catch (error) {
      console.error('분석 결과 파싱 오류:', error)
      showError("분석 결과를 불러오는 중 오류가 발생했습니다.")
    }
  } else {
    console.log('저장된 분석 결과가 없음')
    // 실제 운영 환경에서는 목업 결과를 생성하지 않음
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      console.warn('개발 모드: Mock 결과 생성')
      generateMockResult()
    } else {
      showError("분석 결과를 찾을 수 없습니다. 먼저 음성 파일을 분석해주세요.")
    }
  }
}

// 목업 결과 생성 (개발용 - 실제 운영에서는 사용하지 않음)
function generateMockResult() {
  // 운영 환경에서는 목업 결과를 생성하지 않음
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    showError("분석 결과를 찾을 수 없습니다. 먼저 음성 파일을 분석해주세요.")
    return
  }
  
  console.warn('개발 모드: Mock 결과 생성')
  const isPhishing = Math.random() < 0.3 // 30% 확률로 피싱

  const mockResult = {
    success: true,
    verdict: isPhishing ? "phishing" : "normal",
    type: isPhishing ? getRandomPhishingType() : "정상 통화",
    confidence: isPhishing ? Math.round(75 + Math.random() * 20) : Math.round(85 + Math.random() * 15),
    warning: isPhishing ? getPhishingWarning() : getNormalMessage(),
    analysisStage: Math.random() < 0.3 ? "1차 ML" : "1차 ML + 2차 DL",
    completedAt: new Date().toISOString(),
    // 피드백을 위한 가짜 ID들 (실제 DB에 존재하지 않으므로 피드백 실패)
    rslt_id: "mock_" + Date.now(),
    ocrn_no: "mock_" + Date.now(),
    warning_message: isPhishing ? getPhishingWarning() : getNormalMessage(),
    is_phishing: isPhishing
  }

  displayResult(mockResult)
}

// 랜덤 피싱 유형 반환
function getRandomPhishingType() {
  const types = ["기관 사칭형", "대출 빙자형", "가족 사칭형", "투자 빙자형", "택배 빙자형"]
  return types[Math.floor(Math.random() * types.length)]
}

// 피싱 경고 메시지 반환
function getPhishingWarning() {
  const warnings = [
    "공공기관을 사칭한 보이스피싱입니다. 즉시 통화를 종료하고 해당 기관에 직접 연락하여 확인하세요. 개인정보나 금융정보를 절대 제공하지 마세요.",
    "대출 관련 보이스피싱입니다. 정식 금융기관은 전화로 개인정보를 요구하지 않습니다. 통화를 종료하고 해당 금융기관에 직접 문의하세요.",
    "가족을 사칭한 보이스피싱입니다. 가족에게 직접 연락하여 확인하고, 급하다는 이유로 돈을 요구하는 경우 절대 응하지 마세요.",
    "투자 관련 보이스피싱입니다. 고수익을 보장하는 투자는 존재하지 않습니다. 통화를 종료하고 금융감독원에 신고하세요.",
    "택배 관련 보이스피싱입니다. 개인정보나 금융정보를 요구하는 경우 즉시 통화를 종료하고 해당 택배사에 직접 확인하세요.",
  ]
  return warnings[Math.floor(Math.random() * warnings.length)]
}

// 정상 메시지 반환
function getNormalMessage() {
  return "이 통화는 정상으로 판별되었습니다. 하지만 항상 개인정보 보호에 주의하시고, 의심스러운 요청이 있을 때는 직접 해당 기관에 확인하시기 바랍니다."
}

// 결과 표시
function displayResult(result) {
  // 로딩 섹션 숨기기
  loadingSection.style.display = "none"

  // 결과 카드 표시
  resultCard.style.display = "block"

  // API 응답 형식에 맞게 데이터 추출
  const isPhishing = result.is_phishing || (result.verdict === "phishing")
  const phishingTypeText = result.type || result.phishing_type || "정상통화"
  const confidenceValue = result.confidence || (result.confidence_level * 100) || 0
  const warningTextContent = result.warning_message || result.warning || "분석 완료"

  // 결과 배지 설정
  resultBadge.className = `result-badge ${isPhishing ? "phishing" : "normal"}`
  resultBadge.innerHTML = `
        <i class="fas ${isPhishing ? "fa-exclamation-triangle" : "fa-check-circle"}"></i>
        <span>${isPhishing ? "보이스피싱" : "정상"}</span>
    `

  // 상세 정보 설정
  finalResult.textContent = isPhishing ? "보이스피싱" : "정상"
  finalResult.className = `detail-value ${isPhishing ? "phishing" : "normal"}`

  phishingType.textContent = phishingTypeText
  confidence.textContent = `${Math.round(confidenceValue * 100)}%`

  // 경고 메시지 설정
  warningMessage.className = `warning-message ${isPhishing ? "phishing" : "normal"}`
  warningText.textContent = `"${warningTextContent}"`
  
  console.log('표시된 결과:', { isPhishing, phishingTypeText, confidenceValue, warningTextContent })
  
  // 피드백 버튼 표시
  showFeedbackButton()
}

// 오류 표시
function showError(message) {
  loadingSection.style.display = "none"
  errorResult.style.display = "block"
  errorMessage.textContent = message
}

// 페이지 로드 시 초기화
document.addEventListener("DOMContentLoaded", () => {
  initializeResult()
})

// getUrlParameter 함수 선언
function getUrlParameter(name) {
  name = name.replace(/[[\]]/g, "\\$&")
  const regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)")
  const results = regex.exec(window.location.href)
  if (!results) return null
  if (!results[2]) return ""
  return decodeURIComponent(results[2].replace(/\+/g, " "))
}

// getFromStorage 함수 선언
function getFromStorage(key) {
  return localStorage.getItem(key)
}

// 피드백 관련 함수들
let currentAnalysisData = null

// 피드백 버튼 표시
function showFeedbackButton() {
  const feedbackBtn = document.getElementById('feedbackBtn')
  if (feedbackBtn) {
    feedbackBtn.style.display = 'inline-flex'
  }
}

// 피드백 섹션 표시
function showFeedback() {
  const feedbackSection = document.getElementById('feedbackSection')
  if (feedbackSection) {
    feedbackSection.style.display = 'block'
    feedbackSection.scrollIntoView({ behavior: 'smooth' })
  }
  
  // 문자 카운터 초기화 (중복 이벤트 방지)
  const textarea = document.getElementById('feedbackComment')
  const charCount = document.getElementById('charCount')
  if (textarea && charCount) {
    // 기존 이벤트 리스너 제거 (중복 방지)
    textarea.removeEventListener('input', updateCharCount)
    // 새 이벤트 리스너 추가
    textarea.addEventListener('input', updateCharCount)
    // 초기 카운트 설정
    charCount.textContent = textarea.value.length
  }
}

// 문자 카운터 업데이트 함수 (분리)
function updateCharCount() {
  const charCount = document.getElementById('charCount')
  if (charCount) {
    charCount.textContent = this.value.length
    
    // 글자수 제한 시각적 표시
    if (this.value.length > 950) {
      charCount.style.color = '#ef4444' // 빨간색
    } else if (this.value.length > 800) {
      charCount.style.color = '#f59e0b' // 주황색
    } else {
      charCount.style.color = '#6b7280' // 기본 회색
    }
  }
}

// 피드백 섹션 숨기기
function hideFeedback() {
  const feedbackSection = document.getElementById('feedbackSection')
  if (feedbackSection) {
    feedbackSection.style.display = 'none'
  }
  
  // 폼 초기화
  resetFeedbackForm()
}

// 피드백 폼 완전 초기화
function resetFeedbackForm() {
  console.log('피드백 폼 완전 초기화 시작')
  
  // 모든 라디오 버튼 초기화 (더 광범위하게)
  const radioButtons = document.querySelectorAll('input[type="radio"]')
  radioButtons.forEach(radio => {
    radio.checked = false
    radio.disabled = false
  })
  
  // 모든 체크박스 초기화
  const checkBoxes = document.querySelectorAll('input[type="checkbox"]')
  checkBoxes.forEach(checkbox => {
    checkbox.checked = false
    checkbox.disabled = false
  })
  
  // 모든 텍스트 영역 초기화
  const textareas = document.querySelectorAll('textarea')
  textareas.forEach(textarea => {
    textarea.value = ''
    textarea.disabled = false
  })
  
  // 모든 텍스트 입력 필드 초기화
  const textInputs = document.querySelectorAll('input[type="text"]')
  textInputs.forEach(input => {
    input.value = ''
    input.disabled = false
  })
  
  // 문자 카운터 초기화
  const charCount = document.getElementById('charCount')
  if (charCount) {
    charCount.textContent = '0'
    charCount.style.color = '#6b7280' // 기본 회색으로 초기화
  }
  
  // 피드백 섹션 숨기기
  const feedbackSection = document.querySelector('.feedback-section')
  if (feedbackSection) {
    feedbackSection.style.display = 'none'
  }
  
  // 피드백 성공 메시지 숨기기
  const successMessage = document.querySelector('.feedback-success')
  if (successMessage) {
    successMessage.style.display = 'none'
  }
  
  // 피드백 버튼 다시 보이기
  const feedbackBtn = document.getElementById('feedbackBtn')
  if (feedbackBtn) {
    feedbackBtn.style.display = 'inline-block'
  }
  
  // 로컬스토리지에서 피드백 관련 데이터 제거 (더 광범위하게)
  const feedbackKeys = [
    'feedbackData', 'feedbackSubmitted', 'userFeedback', 
    'feedback_data', 'feedback_submitted', 'user_feedback',
    'currentFeedback', 'lastFeedback', 'feedbackState'
  ]
  
  feedbackKeys.forEach(key => {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  })
  
  console.log('피드백 폼 완전 초기화 완료')
  
  // 제출 버튼 초기화 (모든 가능한 ID 대상)
  const submitBtns = ['submitFeedbackBtn', 'submit-feedback-btn']
  submitBtns.forEach(id => {
    const submitBtn = document.getElementById(id)
    if (submitBtn) {
      submitBtn.disabled = false
      submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 피드백 제출'
      submitBtn.style.backgroundColor = ''
    }
  })
  
  // 피드백 섹션 숨기기
  const feedbackSection = document.getElementById('feedbackSection')
  if (feedbackSection) {
    feedbackSection.style.display = 'none'
  }
  
  // 피드백 버튼 다시 표시
  const feedbackBtn = document.getElementById('feedbackBtn')
  if (feedbackBtn) {
    feedbackBtn.style.display = 'inline-flex'
  }
  
  // 모든 성공/에러 메시지 제거
  const messages = ['feedbackSuccess', 'feedbackError']
  messages.forEach(id => {
    const msg = document.getElementById(id)
    if (msg) {
      msg.remove()
    }
  })
  
  // 기존 메시지들도 제거
  const existingMessages = document.querySelectorAll('.feedback-success, .feedback-error')
  existingMessages.forEach(msg => msg.remove())
  
  console.log('피드백 폼 완전 초기화 완료')
}

// 피드백 제출
async function submitFeedback() {
  try {
    // 폼 데이터 수집
    const feedbackValue = document.querySelector('input[name="feedback"]:checked')
    const commentText = document.getElementById('feedbackComment').value.trim()
    
    if (!feedbackValue) {
      showFeedbackError('분석 결과에 대한 의견을 선택해주세요.')
      return
    }
    
    // 댓글 길이 검증
    if (commentText.length > 1000) {
      showFeedbackError('의견은 1000자 이하로 작성해주세요.')
      return
    }
    
    // 분석 결과에서 필요한 정보 추출
    const urlParams = new URLSearchParams(window.location.search)
    const taskId = urlParams.get('taskId') || currentTaskId
    
    // 로컬 스토리지에서 분석 결과 가져오기
    const analysisResultStr = localStorage.getItem('analysisResult')
    const analysisResult = analysisResultStr ? JSON.parse(analysisResultStr) : {}
    
    console.log('로컬스토리지 분석 결과:', analysisResult)
    console.log('사용 가능한 키:', Object.keys(analysisResult))
    console.log('URL taskId:', taskId)
    
    // 실제 분석 결과에서 rslt_id와 ocrn_no 가져오기 (다양한 형태 지원)
    let rslt_id = analysisResult.rslt_id || analysisResult.result_id || taskId
    let ocrn_no = analysisResult.ocrn_no || analysisResult.occurrence_no || analysisResult.task_id || taskId
    
    // 추가 데이터 검증 및 상세 로깅
    console.log('추출된 데이터:')
    console.log('  rslt_id 후보들:', {
      'analysisResult.rslt_id': analysisResult.rslt_id,
      'analysisResult.result_id': analysisResult.result_id,
      'taskId': taskId
    })
    console.log('  ocrn_no 후보들:', {
      'analysisResult.ocrn_no': analysisResult.ocrn_no,
      'analysisResult.occurrence_no': analysisResult.occurrence_no,
      'analysisResult.task_id': analysisResult.task_id,
      'taskId': taskId
    })
    
    if (!rslt_id || !ocrn_no) {
      console.warn('필요한 ID 정보 부족, URL에서 가져오기 시도')
      rslt_id = rslt_id || taskId
      ocrn_no = ocrn_no || taskId
    }
    
    // 데이터 유효성 최종 검증
    if (!rslt_id || !ocrn_no || rslt_id === 'undefined' || ocrn_no === 'undefined') {
      showFeedbackError('분석 결과 정보를 찾을 수 없습니다. 페이지를 새로고침하고 다시 분석해주세요.')
      return
    }
    
    // Mock 데이터 감지
    if (rslt_id.startsWith('mock_') || ocrn_no.startsWith('mock_')) {
      showFeedbackError('개발 모드에서는 피드백을 제출할 수 없습니다. 실제 음성 파일로 분석 후 시도해주세요.')
      return
    }
    
    console.log('최종 피드백 데이터:', { 
      rslt_id, 
      ocrn_no, 
      user_prediction: feedbackValue.value, 
      comment: commentText,
      available_data: Object.keys(analysisResult)
    })
    
    const feedbackData = {
      rslt_id: rslt_id,
      ocrn_no: ocrn_no,
      user_prediction: feedbackValue.value,
      comment: commentText
    }
    
    // 제출 버튼 비활성화
    const submitBtn = document.getElementById('submitFeedbackBtn')
    const originalText = submitBtn.innerHTML
    submitBtn.disabled = true
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 제출 중...'
    
    // 서버에 피드백 전송
    const response = await fetch('/submit_feedback/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'X-CSRFToken': getCsrfToken()
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
      showFeedbackSuccess(result.message || '피드백이 성공적으로 제출되었습니다.')
      
      // 폼 숨기기
      setTimeout(() => {
        hideFeedback()
      }, 3000)
    } else {
      throw new Error(result.error || '피드백 제출에 실패했습니다.')
    }
    
  } catch (error) {
    console.error('피드백 제출 오류:', error)
    
    // 친화적인 오류 메시지 표시
    let userMessage = '피드백 제출 중 오류가 발생했습니다.'
    
    if (error.message.includes('HTTP 404')) {
      userMessage = '분석 결과를 찾을 수 없습니다. 페이지를 새로고침 후 다시 시도해주세요.'
    } else if (error.message.includes('HTTP 500')) {
      userMessage = '서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
    } else if (error.message.includes('네트워크') || error.name === 'TypeError') {
      userMessage = '네트워크 연결을 확인하고 다시 시도해주세요.'
    } else if (error.message.includes('UTF-8') || error.message.includes('인코딩')) {
      userMessage = '텍스트 입력에 문제가 있습니다. 특수문자를 제거하고 다시 시도해주세요.'
    } else if (error.message) {
      userMessage = error.message
    }
    
    showFeedbackError(userMessage)
  } finally {
    // 제출 버튼 복원
    const submitBtn = document.getElementById('submitFeedbackBtn')
    if (submitBtn) {
      submitBtn.disabled = false
      submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 피드백 제출'
    }
  }
}

// 피드백 에러 메시지 표시
function showFeedbackError(message) {
  // 기존 에러 메시지 제거
  const existingError = document.getElementById('feedbackError')
  if (existingError) {
    existingError.remove()
  }
  
  // 새 에러 메시지 생성
  const errorDiv = document.createElement('div')
  errorDiv.id = 'feedbackError'
  errorDiv.className = 'feedback-error'
  errorDiv.innerHTML = `
    <i class="fas fa-exclamation-triangle"></i>
    <span>${message}</span>
  `
  
  // 피드백 섹션에 추가
  const feedbackForm = document.querySelector('.feedback-form')
  if (feedbackForm) {
    feedbackForm.insertBefore(errorDiv, feedbackForm.firstChild)
    
    // 3초 후 자동 제거
    setTimeout(() => {
      if (errorDiv.parentNode) {
        errorDiv.remove()
      }
    }, 3000)
  } else {
    // 대체: alert 사용
    alert(message)
  }
}

// 피드백 성공 메시지 표시
function showFeedbackSuccess(message = '피드백이 성공적으로 제출되었습니다.') {
  // 기존 성공 메시지 제거
  const existingSuccess = document.getElementById('feedbackSuccess')
  if (existingSuccess) {
    existingSuccess.remove()
  }
  
  // 새 성공 메시지 생성
  const successDiv = document.createElement('div')
  successDiv.id = 'feedbackSuccess'
  successDiv.className = 'feedback-success'
  successDiv.style.cssText = `
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    margin: 16px 0;
    background-color: #10b981;
    color: white;
    border-radius: 6px;
    font-size: 14px;
    animation: slideIn 0.3s ease-out;
  `
  successDiv.innerHTML = `
    <i class="fas fa-check-circle"></i>
    <span>${message}</span>
  `
  
  // 피드백 섹션에 추가
  const feedbackForm = document.querySelector('.feedback-form')
  if (feedbackForm) {
    feedbackForm.insertBefore(successDiv, feedbackForm.firstChild)
    
    // 5초 후 자동 제거
    setTimeout(() => {
      if (successDiv.parentNode) {
        successDiv.remove()
      }
    }, 5000)
  } else {
    // 대체: alert 사용
    alert(message)
  }
}

// CSRF 토큰 가져오기
function getCsrfToken() {
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      return value
    }
  }
  
  // 메타 태그에서 찾기
  const csrfMeta = document.querySelector('meta[name="csrf-token"]')
  if (csrfMeta) {
    return csrfMeta.getAttribute('content')
  }
  
  return ''
}

// 다시 분석 버튼 클릭 시 완전 새로고침
function retryAnalysis() {
  console.log('다시 분석 버튼 클릭 - 완전 새로고침 시작')
  
  // 1. 모든 분석 관련 데이터 즉시 제거
  clearAllAnalysisData()
  
  // 2. 피드백 폼 완전 초기화
  resetFeedbackForm()
  
  // 3. DOM 요소 완전 초기화
  clearAllDOMElements()
  
  // 4. 메인 페이지로 이동 (캐시 무시)
  window.location.href = '/'
}

// 홈으로 이동 시 완전 새로고침
function goHome() {
  console.log('홈으로 버튼 클릭 - 완전 새로고침 시작')
  
  // 1. 모든 분석 관련 데이터 즉시 제거
  clearAllAnalysisData()
  
  // 2. 피드백 폼 완전 초기화
  resetFeedbackForm()
  
  // 3. DOM 요소 완전 초기화
  clearAllDOMElements()
  
  // 4. 메인 페이지로 이동
  window.location.href = '/'
}

// 모든 분석 관련 데이터 완전 제거
function clearAllAnalysisData() {
  console.log('모든 분석 관련 데이터 완전 제거 시작')
  
  // 1. 로컬스토리지 완전 초기화 (더 광범위하게)
  const keysToRemove = [
    'analysisResult', 'currentTaskId', 'feedbackData', 'feedbackSubmitted', 
    'userFeedback', 'analysisData', 'uploadedFile', 'taskResult',
    'lastAnalysis', 'currentAnalysis', 'feedbackState', 'currentFeedback',
    'lastFeedback', 'user_feedback', 'feedback_data', 'feedback_submitted',
    'analysis_result', 'task_id', 'result_data', 'upload_data'
  ]
  
  keysToRemove.forEach(key => {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  })
  
  // 2. 전체 localStorage와 sessionStorage 완전 초기화 (극단적 방법)
  try {
    localStorage.clear()
    sessionStorage.clear()
    console.log('localStorage와 sessionStorage 완전 초기화')
  } catch (e) {
    console.error('스토리지 초기화 오류:', e)
  }
  
  // 3. 모든 쿠키 제거
  document.cookie.split(";").forEach(function(c) { 
    const eqPos = c.indexOf("=")
    const name = eqPos > -1 ? c.substr(0, eqPos).trim() : c.trim()
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=" + window.location.hostname
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/"
  })
  
  // 4. 전역 변수 초기화
  if (typeof analysisResult !== 'undefined') {
    analysisResult = null
  }
  if (typeof currentTaskId !== 'undefined') {
    currentTaskId = null
  }
  if (typeof currentAnalysisData !== 'undefined') {
    currentAnalysisData = null
  }
  
  // 5. 메모리 강제 정리
  if (window.gc) {
    window.gc()
  }
  
  console.log('모든 분석 관련 데이터 제거 완료')
}

// DOM 요소들 완전 초기화
function clearAllDOMElements() {
  console.log('DOM 요소 완전 초기화 시작')
  
  try {
    // 1. 모든 폼 요소 초기화
    const forms = document.querySelectorAll('form')
    forms.forEach(form => {
      form.reset()
    })
    
    // 2. 모든 입력 필드 초기화
    const inputs = document.querySelectorAll('input, textarea, select')
    inputs.forEach(input => {
      if (input.type === 'checkbox' || input.type === 'radio') {
        input.checked = false
      } else {
        input.value = ''
      }
      input.disabled = false
    })
    
    // 3. 피드백 관련 UI 요소 숨기기/초기화
    const feedbackElements = [
      '.feedback-section', '.feedback-success', '.feedback-error',
      '#feedbackSection', '#feedbackSuccess', '#feedbackError'
    ]
    
    feedbackElements.forEach(selector => {
      const elements = document.querySelectorAll(selector)
      elements.forEach(element => {
        element.style.display = 'none'
        if (element.classList) {
          element.classList.remove('show', 'active', 'visible')
        }
      })
    })
    
    // 4. 결과 관련 텍스트 초기화
    const textElements = [
      '#resultText', '#finalResult', '#phishingType', 
      '#confidence', '#warningText', '#feedbackComment'
    ]
    
    textElements.forEach(selector => {
      const element = document.querySelector(selector)
      if (element) {
        element.textContent = ''
        element.innerHTML = ''
      }
    })
    
    // 5. 모든 동적 메시지 제거
    const dynamicMessages = document.querySelectorAll(
      '.alert, .notification, .message, .toast, .popup'
    )
    dynamicMessages.forEach(msg => {
      msg.remove()
    })
    
    // 6. 이벤트 리스너 제거 (메모리 누수 방지)
    const elementsWithEvents = document.querySelectorAll('[onclick], [onchange], [oninput]')
    elementsWithEvents.forEach(element => {
      element.onclick = null
      element.onchange = null
      element.oninput = null
    })
    
    console.log('DOM 요소 완전 초기화 완료')
    
  } catch (error) {
    console.error('DOM 초기화 중 오류:', error)
  }
}