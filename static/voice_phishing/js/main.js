class VoicePhishingDetector {
  constructor() {
    this.currentState = "upload"
    this.selectedFile = null
    this.init()
  }

  init() {
    this.setupEventListeners()
    this.showScreen("upload")
  }

  setupEventListeners() {
    // File upload events
    const dropZone = document.getElementById("drop-zone")
    const fileInput = document.getElementById("file-input")
    const analyzeBtn = document.getElementById("analyze-btn")

    // 터치 이벤트 지원 추가
    const isTouchDevice = "ontouchstart" in window || navigator.maxTouchPoints > 0

    // Drag and drop events (데스크톱)
    if (!isTouchDevice) {
      dropZone.addEventListener("dragenter", this.handleDrag.bind(this))
      dropZone.addEventListener("dragover", this.handleDrag.bind(this))
      dropZone.addEventListener("dragleave", this.handleDragLeave.bind(this))
      dropZone.addEventListener("drop", this.handleDrop.bind(this))
    }

    // 터치 디바이스에서는 드래그 앤 드롭 대신 클릭으로 파일 선택
    dropZone.addEventListener("click", () => {
      fileInput.click()
    })

    // File input change - 실제 로컬 파일 선택 처리
    fileInput.addEventListener("change", this.handleFileSelect.bind(this))

    // 분석시작 버튼
    analyzeBtn.addEventListener("click", this.startAnalysis.bind(this))

    // Error screen buttons
    document.getElementById("retry-btn").addEventListener("click", this.retryAnalysis.bind(this))
    document.getElementById("new-file-btn").addEventListener("click", this.resetToUpload.bind(this))

    // Result screen button
    document.getElementById("reanalyze-btn").addEventListener("click", this.resetToUpload.bind(this))

    // 모바일에서 화면 회전 시 레이아웃 재조정
    window.addEventListener("orientationchange", () => {
      setTimeout(() => {
        this.adjustLayoutForOrientation()
      }, 100)
    })

    // 모바일에서 키보드 표시/숨김 시 레이아웃 조정
    if (isTouchDevice) {
      window.addEventListener("resize", this.handleMobileResize.bind(this))
    }
  }

  adjustLayoutForOrientation() {
    // 화면 회전 시 필요한 레이아웃 조정
    const container = document.querySelector(".container")
    if (container) {
      container.style.minHeight = window.innerHeight + "px"
    }
  }

  handleMobileResize() {
    // 모바일에서 키보드로 인한 화면 크기 변경 처리
    const vh = window.innerHeight * 0.01
    document.documentElement.style.setProperty("--vh", `${vh}px`)
  }

  handleDrag(e) {
    e.preventDefault()
    e.stopPropagation()
    document.getElementById("drop-zone").classList.add("drag-active")
  }

  handleDragLeave(e) {
    e.preventDefault()
    e.stopPropagation()
    document.getElementById("drop-zone").classList.remove("drag-active")
  }

  handleDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    document.getElementById("drop-zone").classList.remove("drag-active")

    const files = e.dataTransfer.files
    if (files.length > 0) {
      this.handleFile(files[0])
    }
  }

  handleFileSelect(e) {
    const file = e.target.files[0]
    if (file) {
      console.log("파일 선택됨:", file.name, "크기:", file.size, "타입:", file.type)
      this.handleFile(file)
    } else {
      console.log("파일 선택이 취소되었습니다.")
    }
  }

  handleFile(file) {
    if (this.isValidAudioFile(file)) {
      this.selectedFile = file
      this.showSelectedFile(file.name, file.size)
      this.enableAnalyzeButton()
    } else {
      // 파일을 선택하지 않고 에러 메시지 표시
      this.selectedFile = null
      document.getElementById("file-selected").classList.add("hidden")
      document.getElementById("analyze-btn").disabled = true
      alert("지원 형식을 확인하여 파일을 업로드해주세요.")
      // 파일 입력 초기화
      document.getElementById("file-input").value = ""
    }
  }

  isValidAudioFile(file) {
    const validTypes = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/amr", "audio/x-wav", "audio/mp4", "audio/m4a"]
    const validExtensions = [".mp3", ".wav", ".amr", ".m4a"]

    // 파일 확장자 체크
    const fileName = file.name.toLowerCase()
    const hasValidExtension = validExtensions.some((ext) => fileName.endsWith(ext))

    // MIME 타입 체크
    const hasValidType = validTypes.includes(file.type)

    return hasValidExtension || hasValidType
  }

  showSelectedFile(filename, filesize) {
    document.getElementById("selected-filename").textContent = filename
    document.getElementById("selected-filesize").textContent = (filesize / 1024 / 1024).toFixed(2)
    document.getElementById("file-selected").classList.remove("hidden")
  }

  enableAnalyzeButton() {
    document.getElementById("analyze-btn").disabled = false
  }

  async startAnalysis() {
    // 파일이 선택되지 않은 경우 체크
    if (!this.selectedFile) {
      alert("파일을 업로드해주세요.")
      return
    }

    this.showScreen("analysis")

    try {
      // FormData 생성
      const formData = new FormData()
      formData.append("audio_file", this.selectedFile)

      // CSRF 토큰 추가
      const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value
      formData.append("csrfmiddlewaretoken", csrfToken)

      // 분석 진행 시뮬레이션
      await this.simulateAnalysisProgress()

      // Django API 호출
      const response = await fetch("/analyze/", {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": csrfToken,
        },
      })

      const result = await response.json()

      if (result.success) {
        this.displayResult(result)
        this.showScreen("result")
      } else {
        this.showError(result.error)
      }
    } catch (error) {
      console.error("Analysis error:", error)
      this.showError("네트워크 오류가 발생했습니다. 다시 시도해주세요.")
    }
  }

  async simulateAnalysisProgress() {
    const steps = [
      {
        id: 'stt',
        title: 'STT 변환',
        subtitle: 'VITO STT API',
        message: 'VITO API로 음성을 텍스트로 변환',
        progress: 25,
        duration: 3000
      },
      {
        id: 'ml',
        title: '1차 머신러닝 분석',
        subtitle: 'Random Forest Classifier',
        message: '머신러닝 모델로 1차 분석을 진행하고 있습니다...',
        progress: 50,
        duration: 2000
      },
      {
        id: 'dl',
        title: '2차 DL 분석',
        subtitle: 'BERT-based Transformer',
        message: '딥러닝 모델로 정밀 분석을 수행하고 있습니다...',
        progress: 75,
        duration: 2500
      },
      {
        id: 'llm',
        title: 'LLM 기반 메시지 생성',
        subtitle: 'GPT-4o',
        message: '머신러닝 모델로 1차 분석을 진행하고 있습니다...',
        progress: 100,
        duration: 2000
      }
    ]

    // 분석 진행 상황 표시를 위한 HTML 업데이트
    this.updateAnalysisSteps(steps)

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i]
      
      // 현재 단계 활성화
      this.setCurrentStep(step.id, step.message)
      
      // 진행률 업데이트
      await this.animateProgress(step.progress, step.duration)
      
      // 단계 완료 표시
      this.markStepCompleted(step.id)
      
      if (i < steps.length - 1) {
        await this.delay(500) // 단계 간 간격
      }
    }
  }

  updateAnalysisSteps(steps) {
    // 분석 화면의 card-content 찾기
    const analysisScreen = document.getElementById('analysis-screen')
    const analysisContainer = analysisScreen.querySelector('.card-content')
    
    // 기존 분석 단계 UI 제거하고 새로 생성
    const existingSteps = document.getElementById('analysis-steps')
    if (existingSteps) {
      existingSteps.remove()
    }
    
    const stepsHTML = `
        <div id="analysis-steps" class="analysis-steps">
          ${steps.map(step => `
            <div class="step-item" id="step-${step.id}">
              <div class="step-icon">
                <div class="step-circle">
                  <svg class="step-check hidden" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                  </svg>
                  <div class="step-spinner hidden">
                    <div class="spinner"></div>
                  </div>
                </div>
              </div>
              <div class="step-content">
                <div class="step-title">${step.title}</div>
                <div class="step-subtitle">${step.subtitle}</div>
                <div class="step-detail hidden">
                  ${step.title === 'STT 변환' ? step.message : '진행 중...'}
                </div>
              </div>
              <div class="step-status">진행 대기</div>
            </div>
          `).join('')}
          
          <div class="overall-progress">
            <div class="progress-label">
              <span>전체 진행률</span>
              <span id="overall-percentage">0%</span>
            </div>
            <div class="progress-bar">
              <div id="overall-progress-fill" class="progress-fill" style="width: 0%"></div>
            </div>
          </div>
          
          <div class="current-status">
            <div class="status-message">
              <p id="current-status-text">분석을 시작합니다...</p>
            </div>
          </div>
        </div>
      `
      
    // 기존 진행률 표시 요소 제거
    const existingProgress = analysisContainer.querySelector('.progress-container')
    const existingStatus = analysisContainer.querySelector('.status-message')
    
    if (existingProgress) existingProgress.remove()
    if (existingStatus) existingStatus.remove()
    
    analysisContainer.insertAdjacentHTML('beforeend', stepsHTML)
  }

  setCurrentStep(stepId, message) {
    // 모든 단계를 대기 상태로 리셋
    document.querySelectorAll('.step-item').forEach(item => {
      item.classList.remove('active', 'completed')
      item.querySelector('.step-status').textContent = '진행 대기'
      item.querySelector('.step-spinner').classList.add('hidden')
      item.querySelector('.step-check').classList.add('hidden')
      item.querySelector('.step-detail').classList.add('hidden')
    })
    
    // 현재 단계 활성화
    const currentStep = document.getElementById(`step-${stepId}`)
    if (currentStep) {
      currentStep.classList.add('active')
      currentStep.querySelector('.step-status').textContent = '진행 중'
      currentStep.querySelector('.step-spinner').classList.remove('hidden')
      currentStep.querySelector('.step-detail').classList.remove('hidden')
    }
    
    // 상태 메시지 업데이트
    this.updateStatusMessage(message)
  }

  markStepCompleted(stepId) {
    const step = document.getElementById(`step-${stepId}`)
    if (step) {
      step.classList.remove('active')
      step.classList.add('completed')
      step.querySelector('.step-status').textContent = '완료'
      step.querySelector('.step-spinner').classList.add('hidden')
      step.querySelector('.step-check').classList.remove('hidden')
    }
  }

  async animateProgress(targetProgress, duration) {
    const startTime = Date.now()
    
    // 이전 진행률을 0으로 리셋하여 항상 0부터 시작
    let startProgress = 0
    if (targetProgress === 25) {
      startProgress = 0
    } else if (targetProgress === 50) {
      startProgress = 25
    } else if (targetProgress === 75) {
      startProgress = 50
    } else if (targetProgress === 100) {
      startProgress = 75
    }
    
    return new Promise(resolve => {
      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / duration, 1)
        const currentProgress = startProgress + (targetProgress - startProgress) * progress
        
        this.updateTotalProgress(currentProgress)
        
        if (progress < 1) {
          requestAnimationFrame(animate)
        } else {
          resolve()
        }
      }
      animate()
    })
  }

  updateTotalProgress(progress) {
    const totalProgressEl = document.getElementById("total-progress")
    const overallProgressEl = document.getElementById("overall-progress-fill")
    const progressPercentageEl = document.getElementById("progress-percentage")
    const overallPercentageEl = document.getElementById("overall-percentage")
    
    if (totalProgressEl) {
      totalProgressEl.style.width = `${progress}%`
    }
    if (overallProgressEl) {
      overallProgressEl.style.width = `${progress}%`
    }
    if (progressPercentageEl) {
      progressPercentageEl.textContent = `${Math.round(progress)}%`
    }
    if (overallPercentageEl) {
      overallPercentageEl.textContent = `${Math.round(progress)}%`
    }
  }

  updateStatusMessage(message) {
    const statusTextEl = document.getElementById("status-text")
    const currentStatusTextEl = document.getElementById("current-status-text")
    
    if (statusTextEl) {
      statusTextEl.textContent = message
    }
    if (currentStatusTextEl) {
      currentStatusTextEl.textContent = message
    }
  }

  displayResult(result) {
    const finalResult = document.getElementById("final-result")
    const phishingTypeDiv = document.getElementById("phishing-type")
    const phishingTypeValue = document.getElementById("phishing-type-value")
    const warningMessage = document.getElementById("warning-message")

    // 최종 결과 표시
    if (result.is_phishing) {
      finalResult.textContent = "보이스피싱"
      finalResult.className = "result-value phishing"
    } else {
      finalResult.textContent = "정상"
      finalResult.className = "result-value normal"
    }

    // 피싱 유형 표시
    if (result.is_phishing && result.type) {
      phishingTypeDiv.classList.remove("hidden")
      phishingTypeValue.textContent = result.type
    } else {
      phishingTypeDiv.classList.add("hidden")
    }

    // 경고 메시지 표시
    if (result.is_phishing) {
      warningMessage.innerHTML = `
                <div class="alert alert-error">
                    <div class="alert-header">
                        <svg class="alert-icon" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
                        </svg>
                    </div>
                    <p>"${result.warning_message || "이 통화는 보이스피싱이 의심됩니다."}"</p>
                </div>
            `
    } else {
      warningMessage.innerHTML = `
                <div class="alert alert-success">
                    <div class="alert-header">
                        <svg class="alert-icon" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <p>"보이스피싱 의심률이 적은 대화입니다."</p>
                </div>
            `
    }
  }

  showError(errorMessage) {
    document.getElementById("error-message").textContent = errorMessage
    this.showScreen("error")
  }

  retryAnalysis() {
    this.showScreen("upload")
  }

  resetToUpload() {
    this.selectedFile = null
    document.getElementById("file-selected").classList.add("hidden")
    document.getElementById("analyze-btn").disabled = true
    document.getElementById("file-input").value = ""
    this.showScreen("upload")
  }

  showScreen(screenName) {
    // Hide all screens
    const screens = ["upload-screen", "analysis-screen", "error-screen", "result-screen"]
    screens.forEach((screen) => {
      document.getElementById(screen).classList.add("hidden")
    })

    // Show target screen
    document.getElementById(`${screenName}-screen`).classList.remove("hidden")

    // Update breadcrumb
    const breadcrumbTexts = {
      upload: "업로드",
      analysis: "분석중",
      error: "오류",
      result: "결과",
    }
    document.getElementById("breadcrumb-text").textContent = breadcrumbTexts[screenName]

    this.currentState = screenName
  }

  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }
}

// Initialize the application when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new VoicePhishingDetector()
})