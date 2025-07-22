// 업로드 페이지 전용 JavaScript

let selectedFile = null
let uploadProgress = 0

// DOM 요소들
const fileDropArea = document.getElementById("fileDropArea")
const fileInput = document.getElementById("fileInput")
const selectedFileDiv = document.getElementById("selectedFile")
const fileName = document.getElementById("fileName")
const fileSize = document.getElementById("fileSize")
const statusMessage = document.getElementById("statusMessage")
const statusText = document.getElementById("statusText")
const uploadProgressDiv = document.getElementById("uploadProgress")
const progressFill = document.getElementById("progressFill")
const progressText = document.getElementById("progressText")
const uploadBtn = document.getElementById("uploadBtn")
const analyzeBtn = document.getElementById("analyzeBtn")

// 드래그 앤 드롭 이벤트 핸들러
function handleDragOver(e) {
  e.preventDefault()
  fileDropArea.classList.add("drag-over")
}

function handleDragEnter(e) {
  e.preventDefault()
  fileDropArea.classList.add("drag-over")
}

function handleDragLeave(e) {
  e.preventDefault()
  fileDropArea.classList.remove("drag-over")
}

function handleDrop(e) {
  e.preventDefault()
  fileDropArea.classList.remove("drag-over")

  const files = e.dataTransfer.files
  if (files.length > 0) {
    handleFileSelection(files[0])
  }
}

// 파일 선택 이벤트 핸들러
function handleFileSelect(e) {
  const file = e.target.files[0]
  if (file) {
    handleFileSelection(file)
  }
}

// 파일 선택 처리
function handleFileSelection(file) {
  // 파일 형식 검증
  const validAudioFormats = ["audio/amr", "audio/mpeg", "audio/wav"]
  if (!validAudioFormats.includes(file.type)) {
    showStatusMessage(statusMessage, "지원하지 않는 파일 형식입니다. AMR, MP3, WAV 파일만 업로드 가능합니다.", "error")
    selectedFile = null
    updateButtonStates()
    return
  }

  // 파일 크기 검증 (최대 50MB)
  if (file.size > 50 * 1024 * 1024) {
    showStatusMessage(statusMessage, "파일 크기는 50MB 이하여야 합니다", "error")
    selectedFile = null
    updateButtonStates()
    return
  }

  // 파일 정보 표시
  selectedFile = file
  fileName.textContent = file.name
  fileSize.textContent = formatFileSize(file.size)
  selectedFileDiv.style.display = "block"
  hideStatusMessage(statusMessage)
  updateButtonStates()
}

// 버튼 상태 업데이트
function updateButtonStates() {
  const hasFile = selectedFile !== null
  uploadBtn.disabled = !hasFile
  analyzeBtn.disabled = !hasFile
}

// 업로드 시작
function startUpload() {
  if (!selectedFile) {
    showStatusMessage(statusMessage, "파일을 선택해주세요.", "error")
    return
  }

  // 업로드 시뮬레이션
  uploadProgressDiv.style.display = "block"
  uploadBtn.disabled = true
  analyzeBtn.disabled = true

  simulateUpload()
}

// 업로드 시뮬레이션
function simulateUpload() {
  uploadProgress = 0
  const interval = setInterval(() => {
    uploadProgress += Math.random() * 15
    if (uploadProgress >= 100) {
      uploadProgress = 100
      clearInterval(interval)
      onUploadComplete()
    }

    progressFill.style.width = `${uploadProgress}%`
    progressText.textContent = `업로드 중... ${Math.round(uploadProgress)}%`
  }, 200)
}

// 업로드 완료
function onUploadComplete() {
  progressText.textContent = "업로드 완료!"
  showStatusMessage(statusMessage, "파일이 성공적으로 업로드되었습니다.", "success")

  // 파일 정보 저장
  const fileInfo = {
    name: selectedFile.name,
    size: selectedFile.size,
    type: selectedFile.type,
    uploadTime: new Date().toISOString(),
  }
  saveToStorage("uploadedFile", fileInfo)

  // 버튼 상태 업데이트
  uploadBtn.disabled = true
  analyzeBtn.disabled = false
  analyzeBtn.textContent = "분석 시작"
}

// 분석 시작
function startAnalysis() {
  if (!selectedFile) {
    showStatusMessage(statusMessage, "먼저 파일을 업로드해주세요.", "error")
    return
  }

  // Task ID 생성 및 저장
  const taskId = generateTaskId()
  saveToStorage("currentTaskId", taskId)

  // 분석 페이지로 이동
  window.location.href = `/analysis/?taskId=${taskId}`
}

// 페이지 로드 시 초기화
document.addEventListener("DOMContentLoaded", () => {
  updateButtonStates()

  // 이전 업로드 정보가 있으면 복원
  const uploadedFile = getFromStorage("uploadedFile")
  if (uploadedFile) {
    // 업로드된 파일 정보 표시 (실제 파일 객체는 없음)
    fileName.textContent = uploadedFile.name
    fileSize.textContent = formatFileSize(uploadedFile.size)
    selectedFileDiv.style.display = "block"

    // 가상의 파일 객체 생성
    selectedFile = {
      name: uploadedFile.name,
      size: uploadedFile.size,
      type: uploadedFile.type,
    }

    updateButtonStates()
    showStatusMessage(statusMessage, "이전에 업로드된 파일이 있습니다.", "info")
  }
})

// 지원하는 오디오 파일 형식 검증
function isValidAudioFile(file) {
  const validAudioFormats = ["audio/amr", "audio/mpeg", "audio/wav"]
  return validAudioFormats.includes(file.type)
}

// 상태 메시지 표시
function showStatusMessage(element, message, type) {
  element.style.display = "block"
  statusText.textContent = message
  statusMessage.classList.remove("success", "error", "info")
  statusMessage.classList.add(type)
}

// 상태 메시지 숨김
function hideStatusMessage(element) {
  element.style.display = "none"
}

// 파일 크기 포맷팅
function formatFileSize(bytes) {
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"]
  if (bytes === 0) return "0 Byte"
  const i = Number.parseInt(Math.floor(Math.log(bytes) / Math.log(1024)))
  return Math.round(bytes / Math.pow(1024, i)) + " " + sizes[i]
}

// 로컬 스토리지에 데이터 저장
function saveToStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

// 로컬 스토리지에서 데이터 불러오기
function getFromStorage(key) {
  const value = localStorage.getItem(key)
  return value ? JSON.parse(value) : null
}

// Task ID 생성
function generateTaskId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5)
}