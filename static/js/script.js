// 공통 JavaScript 함수들

// 모바일 메뉴 토글
function toggleMobileMenu() {
  const mobileMenu = document.getElementById("mobileMenu")
  mobileMenu.classList.toggle("show")
}

// 페이지 이동 함수들
function goHome() {
  window.location.href = "/"
}

function goToUpload() {
  window.location.href = "/upload/"
}

function retryAnalysis() {
  window.location.href = "/upload/"
}

// URL 파라미터 가져오기
function getUrlParameter(name) {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get(name)
}

// 로컬 스토리지 헬퍼
function saveToStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

function getFromStorage(key) {
  const item = localStorage.getItem(key)
  return item ? JSON.parse(item) : null
}

// 상태 메시지 표시
function showStatusMessage(element, message, type = "info") {
  element.style.display = "flex"
  element.className = `status-message ${type}`
  element.querySelector("#statusText").textContent = message
}

function hideStatusMessage(element) {
  element.style.display = "none"
}

// 진행률 업데이트
function updateProgress(progressElement, fillElement, textElement, percent, text = "") {
  progressElement.style.display = "block"
  fillElement.style.width = `${percent}%`
  textElement.textContent = text || `${percent}%`
}

// 파일 크기 포맷팅
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

// 파일 확장자 검증
function isValidAudioFile(file) {
  const allowedTypes = ["audio/amr", "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"]
  const allowedExtensions = [".amr", ".mp3", ".wav"]
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf("."))

  return allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension)
}

// 랜덤 Task ID 생성
function generateTaskId() {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 8)
  return `TASK-${timestamp}-${random}`
}

// 페이지 로드 시 공통 초기화
document.addEventListener("DOMContentLoaded", () => {
  // 현재 페이지에 따른 네비게이션 활성화
  const currentPage = window.location.pathname.split("/").pop() || "index.html"
  const navLinks = document.querySelectorAll(".nav-link, .mobile-nav-link")

  navLinks.forEach((link) => {
    const href = link.getAttribute("href")
    if (href === currentPage) {
      link.classList.add("active")
    } else {
      link.classList.remove("active")
    }
  })
})