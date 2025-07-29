// 분석 페이지 전용 JavaScript

let currentTaskId = null
let websocket = null
let currentStep = 0
let isAnalysisComplete = false

// DOM 요소들
const taskIdElement = document.getElementById("taskId")
const analysisSteps = document.getElementById("analysisSteps")
const currentStatus = document.getElementById("currentStatus")
const errorSection = document.getElementById("errorSection")

// 분석 단계 정보
const steps = [
  { key: "stt", name: "STT 변환", icon: "fas fa-microphone" },
  { key: "ml", name: "1차 ML 분석", icon: "fas fa-brain" },
  { key: "dl", name: "2차 DL 분석", icon: "fas fa-robot" },
  { key: "llm", name: "LLM 메시지 생성", icon: "fas fa-comments" }
]

// URL에서 파라미터 가져오기
function getUrlParameter(name) {
  name = name.replace(/[[\]]/g, "\\$&")
  const regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)")
  const results = regex.exec(window.location.href)
  if (!results) return null
  if (!results[2]) return ""
  return decodeURIComponent(results[2].replace(/\+/g, " "))
}

// 로컬 스토리지에서 데이터 가져오기
function getFromStorage(key) {
  return localStorage.getItem(key)
}

// 로컬 스토리지에 데이터 저장하기
function saveToStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

// Task ID 생성하기
function generateTaskId() {
  return Math.random().toString(36).substr(2, 9)
}

// 페이지 초기화
function initializeAnalysis() {
  // URL에서 Task ID 가져오기
  currentTaskId = getUrlParameter("taskId") || getFromStorage("currentTaskId") || generateTaskId()

  if (taskIdElement) {
    taskIdElement.textContent = currentTaskId
  }

  // WebSocket 연결 시작
  connectWebSocket()
}

// WebSocket 연결
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/analysis/${currentTaskId}/`
  
  websocket = new WebSocket(wsUrl)
  
  websocket.onopen = function(event) {
    console.log('WebSocket 연결 성공')
    currentStatus.textContent = "분석을 준비하고 있습니다..."
  }
  
  websocket.onmessage = function(event) {
    const data = JSON.parse(event.data)
    handleWebSocketMessage(data)
  }
  
  websocket.onclose = function(event) {
    console.log('WebSocket 연결 종료')
    if (!isAnalysisComplete) {
      // 예상치 못한 연결 종료인 경우 재연결 시도
      setTimeout(() => {
        if (!isAnalysisComplete) {
          connectWebSocket()
        }
      }, 3000)
    }
  }
  
  websocket.onerror = function(error) {
    console.error('WebSocket 오류:', error)
    handleAnalysisError('서버와의 연결에 문제가 발생했습니다.')
  }
}

// WebSocket 메시지 처리
function handleWebSocketMessage(data) {
  console.log('WebSocket 메시지 수신:', data)
  
  switch (data.type) {
    case 'progress':
      handleProgressUpdate(data)
      break
    case 'complete':
      handleAnalysisComplete(data.result)
      break
    case 'error':
      handleAnalysisError(data.message)
      break
    default:
      console.log('알 수 없는 메시지 타입:', data.type)
  }
}

// 진행률 업데이트 처리
function handleProgressUpdate(data) {
  const { step, progress, message, step_name } = data
  
  // 현재 단계 업데이트
  currentStep = step
  
  // 단계 상태 업데이트
  updateAnalysisStep(step, progress === 100 ? "completed" : "processing", progress)
  
  // 상태 메시지 업데이트
  currentStatus.textContent = message
  
  // 이전 단계들을 완료 상태로 설정
  for (let i = 0; i < step; i++) {
    updateAnalysisStep(i, "completed", 100)
  }
}

// 분석 단계 업데이트
function updateAnalysisStep(stepIndex, status, progress) {
  const stepElement = analysisSteps.children[stepIndex]
  if (!stepElement) return

  const iconElement = stepElement.querySelector(".step-icon i")
  const progressBar = stepElement.querySelector(".progress-fill")
  const progressPercent = stepElement.querySelector(".progress-percent")

  // 아이콘 업데이트
  iconElement.className = getStepIconClass(status)

  // 진행률 업데이트
  if (progressBar && progressPercent) {
    progressBar.style.width = `${progress}%`
    progressPercent.textContent = `${Math.round(progress)}%`
  }
}

// 단계별 아이콘 클래스 반환
function getStepIconClass(status) {
  switch (status) {
    case "processing":
      return "fas fa-spinner step-processing"
    case "completed":
      return "fas fa-check-circle step-completed"
    case "error":
      return "fas fa-exclamation-triangle step-error"
    default:
      return "fas fa-circle step-pending"
  }
}


// 분석 완료 처리
function handleAnalysisComplete(result) {
  isAnalysisComplete = true
  
  // WebSocket 연결 종료
  if (websocket) {
    websocket.close()
  }
  
  // 모든 단계를 완료 상태로 설정
  for (let i = 0; i < steps.length; i++) {
    updateAnalysisStep(i, "completed", 100)
  }
  
  currentStatus.textContent = "분석이 완료되었습니다. 결과 페이지로 이동합니다..."
  
  // 결과를 localStorage에 저장
  saveToStorage("analysisResult", result)
  
  // 2초 후 결과 페이지로 이동
  setTimeout(() => {
    window.location.href = `/result/?taskId=${currentTaskId}`
  }, 2000)
}


// 분석 재시도
function retryAnalysis() {
  // 오류 섹션 숨기기
  errorSection.style.display = "none"

  // 모든 단계 초기화
  for (let i = 0; i < steps.length; i++) {
    updateAnalysisStep(i, "pending", 0)
  }
  
  // 상태 초기화
  isAnalysisComplete = false
  currentStep = 0

  // WebSocket 재연결
  connectWebSocket()
}

// 오류 처리
function handleAnalysisError(message) {
  currentStatus.textContent = message
  errorSection.style.display = "block"

  // 현재 단계를 오류 상태로 변경
  if (currentStep < steps.length) {
    updateAnalysisStep(currentStep, "error", 0)
  }
}

// 페이지 로드 시 초기화
document.addEventListener("DOMContentLoaded", () => {
  initializeAnalysis()
})