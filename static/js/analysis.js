// 분석 페이지 전용 JavaScript

let currentTaskId = null
const analysisInterval = null
let currentStep = 0

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

  // 분석 시작
  startAnalysisSimulation()
}

// 분석 시뮬레이션 시작
function startAnalysisSimulation() {
  currentStep = 0
  updateAnalysisStep(0, "processing", 0)
  currentStatus.textContent = "STT 변환을 시작합니다..."

  // 단계별 진행 시뮬레이션
  simulateStep(0)
}

// 단계별 시뮬레이션
function simulateStep(stepIndex) {
  if (stepIndex >= steps.length) {
    // 모든 단계 완료
    completeAnalysis()
    return
  }

  const step = steps[stepIndex]
  let progress = 0

  updateAnalysisStep(stepIndex, "processing", 0)
  updateStatusMessage(stepIndex, "processing")

  const stepInterval = setInterval(() => {
    progress += Math.random() * 10

    if (progress >= 100) {
      progress = 100
      clearInterval(stepInterval)

      updateAnalysisStep(stepIndex, "completed", 100)

      // 1차 ML에서 피싱 판별 시뮬레이션 (30% 확률)
      if (stepIndex === 1 && Math.random() < 0.3) {
        // 1차에서 피싱 판별됨 - 바로 완료
        setTimeout(() => {
          completeAnalysisEarly("1차 ML에서 보이스피싱이 탐지되었습니다.")
        }, 1000)
        return
      }

      // 다음 단계로 진행
      setTimeout(() => {
        simulateStep(stepIndex + 1)
      }, 500)
    }

    updateAnalysisStep(stepIndex, "processing", Math.min(progress, 100))
  }, 300)
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

// 상태 메시지 업데이트
function updateStatusMessage(stepIndex, status) {
  const messages = {
    0: {
      processing: "VITO STT로 음성을 텍스트로 변환하고 있습니다...",
      completed: "STT 변환이 완료되었습니다.",
    },
    1: {
      processing: "1차 ML 모델로 보이스피싱 패턴을 분석하고 있습니다...",
      completed: "1차 ML 분석이 완료되었습니다.",
    },
    2: {
      processing: "2차 DL 모델로 정밀 검증을 진행하고 있습니다...",
      completed: "2차 DL 분석이 완료되었습니다.",
    },
  }

  const message = messages[stepIndex]?.[status] || "분석을 진행하고 있습니다..."
  currentStatus.textContent = message
}

// 조기 완료 (1차에서 피싱 탐지)
function completeAnalysisEarly(message) {
  currentStatus.textContent = message

  // 결과 생성 및 저장
  const result = {
    verdict: "phishing",
    type: "기관 사칭형",
    confidence: 87.5,
    warning: "공공기관을 사칭한 보이스피싱입니다. 즉시 통화를 종료하고 해당 기관에 직접 연락하여 확인하세요.",
    analysisStage: "1차 ML",
    completedAt: new Date().toISOString(),
  }

  saveToStorage("analysisResult", result)

  // 결과 페이지로 이동
  setTimeout(() => {
    window.location.href = `/result/?taskId=${currentTaskId}`
  }, 2000)
}

// 전체 분석 완료
function completeAnalysis() {
  currentStatus.textContent = "GPT-4o가 맞춤형 경고 메시지를 생성하고 있습니다..."

  // 최종 결과 생성 (80% 확률로 정상)
  const isPhishing = Math.random() < 0.2

  const result = {
    verdict: isPhishing ? "phishing" : "normal",
    type: isPhishing ? "투자 빙자형" : "정상 통화",
    confidence: isPhishing ? 92.3 : 96.7,
    warning: isPhishing
      ? "투자 관련 보이스피싱입니다. 고수익을 보장하는 투자는 존재하지 않습니다. 통화를 종료하고 금융감독원에 신고하세요."
      : "이 통화는 정상으로 판별되었습니다. 하지만 항상 개인정보 보호에 주의하시고, 의심스러운 요청이 있을 때는 직접 해당 기관에 확인하시기 바랍니다.",
    analysisStage: "1차 ML + 2차 DL",
    completedAt: new Date().toISOString(),
  }

  saveToStorage("analysisResult", result)

  // 결과 페이지로 이동
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

  // 분석 재시작
  startAnalysisSimulation()
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