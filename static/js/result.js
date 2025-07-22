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
  analysisResult = getFromStorage("analysisResult")

  if (analysisResult) {
    displayResult(analysisResult)
  } else {
    // 결과가 없으면 시뮬레이션으로 생성
    setTimeout(() => {
      generateMockResult()
    }, 2000)
  }
}

// 목업 결과 생성
function generateMockResult() {
  const isPhishing = Math.random() < 0.3 // 30% 확률로 피싱

  const mockResult = {
    verdict: isPhishing ? "phishing" : "normal",
    type: isPhishing ? getRandomPhishingType() : "정상 통화",
    confidence: isPhishing ? Math.round(75 + Math.random() * 20) : Math.round(85 + Math.random() * 15),
    warning: isPhishing ? getPhishingWarning() : getNormalMessage(),
    analysisStage: Math.random() < 0.3 ? "1차 ML" : "1차 ML + 2차 DL",
    completedAt: new Date().toISOString(),
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

  // 결과 배지 설정
  const isPhishing = result.verdict === "phishing"
  resultBadge.className = `result-badge ${isPhishing ? "phishing" : "normal"}`
  resultBadge.innerHTML = `
        <i class="fas ${isPhishing ? "fa-exclamation-triangle" : "fa-check-circle"}"></i>
        <span>${isPhishing ? "보이스피싱" : "정상"}</span>
    `

  // 상세 정보 설정
  finalResult.textContent = isPhishing ? "보이스피싱" : "정상"
  finalResult.className = `detail-value ${isPhishing ? "phishing" : "normal"}`

  phishingType.textContent = result.type
  confidence.textContent = `${result.confidence}%`

  // 경고 메시지 설정
  warningMessage.className = `warning-message ${isPhishing ? "phishing" : "normal"}`
  warningText.textContent = `"${result.warning}"`
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