// 분석 단계 정의
const analysisStepsData = [
  { id: 'stt', title: 'STT 변환', subtitle: 'VITO STT API' },
  { id: 'ml', title: '1차 ML 분석', subtitle: 'Machine Learning' },
  { id: 'dl', title: '2차 DL 분석', subtitle: 'Deep Learning' },
  { id: 'llm', title: 'LLM 메시지 생성', subtitle: 'GPT-4' }
]

class VoicePhishingDetector {
  constructor() {
    this.currentState = "upload"
    this.selectedFile = null
    this.websocket = null
    this.taskId = null
    this.currentStep = 0
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
    dropZone.addEventListener("click", (e) => {
      // 라벨 클릭 시 중복 방지 (라벨 자체에서도 파일 입력이 열림)
      if (e.target.tagName === 'LABEL') {
        return
      }
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

    // Feedback related events
    this.setupFeedbackListeners()

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
      
      // 이미 같은 파일이 선택되어 있으면 중복 처리 방지
      if (this.selectedFile && this.selectedFile.name === file.name && this.selectedFile.size === file.size) {
        console.log("동일한 파일이 이미 선택되어 있습니다.")
        return
      }
      
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
    const analyzeBtn = document.getElementById("analyze-btn")
    analyzeBtn.disabled = false
    analyzeBtn.classList.remove('processing')
    analyzeBtn.textContent = '분석 시작'
  }

  resetAnalyzeButton() {
    const analyzeBtn = document.getElementById("analyze-btn")
    analyzeBtn.disabled = false
    analyzeBtn.classList.remove('processing')
    analyzeBtn.textContent = '분석 시작'
  }

  async startAnalysis() {
    // 파일이 선택되지 않은 경우 체크
    if (!this.selectedFile) {
      alert("파일을 업로드해주세요.")
      return
    }

    // 중복 실행 방지
    const analyzeBtn = document.getElementById("analyze-btn")
    if (analyzeBtn.disabled || analyzeBtn.classList.contains('processing')) {
      return
    }

    // 버튼 비활성화로 중복 실행 방지
    analyzeBtn.disabled = true
    analyzeBtn.classList.add('processing')
    analyzeBtn.textContent = '분석 중...'

    // 분석 화면으로 전환 및 단계 UI 초기화
    this.updateAnalysisSteps(analysisStepsData)
    this.showScreen("analysis")

    // Task ID 생성 후 저장
    this.taskId = this.generateTaskId()
    localStorage.setItem('currentTaskId', this.taskId)

    // WebSocket 연결 시작
    this.connectWebSocket()

    try {
      // FormData 생성
      const formData = new FormData()
      formData.append('audio_file', this.selectedFile)
      formData.append('task_id', this.taskId)

      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value

      // 백엔드 분석 요청
      fetch('/analyze/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData
      }).catch(err => {
        console.error('분석 요청 오류:', err)
        this.handleAnalysisError('분석 요청 중 오류가 발생했습니다.')
      })

    } catch (error) {
      console.error('Analysis error:', error)
      this.handleAnalysisError('분석 시작 중 오류가 발생했습니다.')
      this.resetAnalyzeButton()
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

    // 모든 단계 완료 후 최종 완료 메시지 표시
    await this.delay(300)
    this.showAnalysisCompleted()
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
    // 피드백을 위해 현재 분석 결과 저장
    this.currentAnalysisResult = result
    
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
    document.getElementById("file-input").value = ""
    
    // 버튼 상태 완전히 초기화
    const analyzeBtn = document.getElementById("analyze-btn")
    analyzeBtn.disabled = true
    analyzeBtn.classList.remove('processing')
    analyzeBtn.textContent = '분석 시작'
    
    // 피드백 상태 완전히 초기화
    this.resetFeedbackState()
    
    this.showScreen("upload")
  }

  resetFeedbackState() {
    // 피드백 라디오 버튼 선택 해제 및 활성화
    const radioButtons = document.querySelectorAll('input[name="feedback-accuracy"]')
    radioButtons.forEach(radio => {
      radio.checked = false
      radio.disabled = false
    })
    
    // 피드백 코멘트 초기화 및 활성화
    const commentTextarea = document.getElementById('feedback-comment')
    if (commentTextarea) {
      commentTextarea.value = ''
      commentTextarea.disabled = false
    }
    
    // 피드백 제출 버튼 비활성화 및 원래 상태 복원
    const submitBtn = document.getElementById('submit-feedback-btn')
    if (submitBtn) {
      submitBtn.disabled = true
      submitBtn.innerHTML = `
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zm0 4.7l-8 5.334L4 8.7V6.297l8 5.333 8-5.333V8.7z"/>
        </svg>
        피드백 제출
      `
    }
    
    // 피드백 상태 메시지 숨김
    const statusDiv = document.getElementById('feedback-status')
    if (statusDiv) {
      statusDiv.classList.add('hidden')
      statusDiv.textContent = ''
      statusDiv.className = 'feedback-status hidden'
    }
    
    // 현재 분석 결과 초기화
    this.currentAnalysisResult = null
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

  showAnalysisCompleted() {
    // 모든 단계를 완료 상태로 표시
    document.querySelectorAll('.step-item').forEach(item => {
      if (!item.classList.contains('completed')) {
        item.classList.add('completed')
        item.querySelector('.step-status').textContent = '완료'
        item.querySelector('.step-spinner').classList.add('hidden')
        item.querySelector('.step-check').classList.remove('hidden')
      }
    })
    
    // 전체 진행률을 100%로 설정
    this.updateTotalProgress(100)
    
    // 최종 완료 메시지 표시
    this.updateStatusMessage("✅ 모든 분석이 완료되었습니다. 결과를 생성하는 중...")
    
    // 완료 효과 추가
    const overallProgress = document.querySelector('.overall-progress')
    if (overallProgress) {
      overallProgress.style.border = '2px solid #10b981'
      overallProgress.style.backgroundColor = '#ecfdf5'
    }
  }

  generateTaskId() {
    return 'task-' + Math.random().toString(36).substr(2, 9)
  }

  connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/analysis/${this.taskId}/`
    this.websocket = new WebSocket(wsUrl)

    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.handleWebSocketMessage(data)
    }

    this.websocket.onerror = () => {
      this.handleAnalysisError('서버와의 연결에 문제가 발생했습니다.')
    }
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'progress':
        this.handleProgressUpdate(data)
        break
      case 'complete':
        this.handleAnalysisComplete(data.result)
        break
      case 'error':
        this.handleAnalysisError(data.message)
        break
    }
  }

  handleProgressUpdate(data) {
    const { step, progress, message } = data
    this.currentStep = step
    this.updateAnalysisStep(step, progress === 100 ? 'completed' : 'processing', progress)
    this.updateStatusMessage(message)
    for (let i = 0; i < step; i++) {
      this.updateAnalysisStep(i, 'completed', 100)
    }
  }

  updateAnalysisStep(stepIndex, status, progress) {
    const stepInfo = analysisStepsData[stepIndex]
    if (!stepInfo) return
    const stepEl = document.getElementById(`step-${stepInfo.id}`)
    if (!stepEl) return

    const spinner = stepEl.querySelector('.step-spinner')
    const check = stepEl.querySelector('.step-check')
    const statusEl = stepEl.querySelector('.step-status')
    const bar = stepEl.querySelector('.progress-fill')
    const percent = stepEl.querySelector('.progress-percent')

    if (statusEl) {
      if (status === 'processing') statusEl.textContent = '진행 중'
      else if (status === 'completed') statusEl.textContent = '완료'
      else statusEl.textContent = '오류'
    }
    if (spinner) spinner.classList.toggle('hidden', status !== 'processing')
    if (check) check.classList.toggle('hidden', status !== 'completed')
    if (bar) bar.style.width = `${progress}%`
    if (percent) percent.textContent = `${Math.round(progress)}%`
    this.updateTotalProgress(progress)
  }

  handleAnalysisComplete(result) {
    if (this.websocket) {
      this.websocket.close()
    }
    analysisStepsData.forEach((_, idx) => this.updateAnalysisStep(idx, 'completed', 100))
    this.updateStatusMessage('분석이 완료되었습니다. 결과 페이지로 이동합니다...')
    localStorage.setItem('analysisResult', JSON.stringify(result))
    setTimeout(() => {
      this.displayResult(result)
      this.showScreen('result')
    }, 500)
  }

  handleAnalysisError(message) {
    this.updateStatusMessage(message)
    this.showScreen('error')
  }

  setupFeedbackListeners() {
    // 라디오 버튼 변경 시 제출 버튼 활성화
    const radioButtons = document.querySelectorAll('input[name="feedback-accuracy"]')
    const submitBtn = document.getElementById('submit-feedback-btn')
    
    if (radioButtons.length > 0 && submitBtn) {
      radioButtons.forEach(radio => {
        radio.addEventListener('change', () => {
          if (document.querySelector('input[name="feedback-accuracy"]:checked')) {
            submitBtn.disabled = false
          }
        })
      })
      
      // 피드백 제출 버튼 클릭
      submitBtn.addEventListener('click', this.submitFeedback.bind(this))
    }
  }

  async submitFeedback() {
    try {
      const submitBtn = document.getElementById('submit-feedback-btn')
      const statusDiv = document.getElementById('feedback-status')
      const accuracyRadio = document.querySelector('input[name="feedback-accuracy"]:checked')
      const commentTextarea = document.getElementById('feedback-comment')
      
      if (!accuracyRadio) {
        this.showFeedbackStatus('정확도를 선택해주세요.', 'error')
        return
      }
      
      // 버튼 비활성화 및 로딩 상태
      submitBtn.disabled = true
      submitBtn.innerHTML = `
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24" class="animate-spin">
          <path d="M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z"/>
        </svg>
        제출 중...
      `
      
      // 피드백 데이터 준비
      const feedbackData = {
        rslt_id: this.currentAnalysisResult?.rslt_id,
        ocrn_no: this.currentAnalysisResult?.ocrn_no,
        user_prediction: accuracyRadio.value === 'accurate' ? 'Y' : 'N',
        comment: commentTextarea.value.trim() || ''
      }
      
      // CSRF 토큰 가져오기
      const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value
      
      // 서버로 피드백 전송
      const response = await fetch('/submit_feedback/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(feedbackData)
      })
      
      const result = await response.json()
      
      if (result.success) {
        this.showFeedbackStatus('피드백이 성공적으로 제출되었습니다. 감사합니다!', 'success')
        
        // 폼 비활성화
        const radioButtons = document.querySelectorAll('input[name="feedback"]')
        radioButtons.forEach(radio => radio.disabled = true)
        commentTextarea.disabled = true
        
        // 버튼 완료 상태로 변경
        submitBtn.innerHTML = `
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          제출 완료
        `
      } else {
        this.showFeedbackStatus(result.error || '피드백 제출에 실패했습니다.', 'error')
        
        // 버튼 원래 상태로 복원
        submitBtn.disabled = false
        submitBtn.innerHTML = `
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
            <path d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zm0 4.7l-8 5.334L4 8.7V6.297l8 5.333 8-5.333V8.7z"/>
          </svg>
          피드백 제출
        `
      }
    } catch (error) {
      console.error('Feedback submission error:', error)
      this.showFeedbackStatus('네트워크 오류가 발생했습니다. 다시 시도해주세요.', 'error')
      
      // 버튼 원래 상태로 복원
      const submitBtn = document.getElementById('submit-feedback-btn')
      submitBtn.disabled = false
      submitBtn.innerHTML = `
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zm0 4.7l-8 5.334L4 8.7V6.297l8 5.333 8-5.333V8.7z"/>
        </svg>
        피드백 제출
      `
    }
  }

  showFeedbackStatus(message, type) {
    const statusDiv = document.getElementById('feedback-status')
    if (statusDiv) {
      statusDiv.textContent = message
      statusDiv.className = `feedback-status ${type}`
      statusDiv.classList.remove('hidden')
      
      // 3초 후 상태 메시지 숨김
      if (type === 'success') {
        setTimeout(() => {
          statusDiv.classList.add('hidden')
        }, 3000)
      }
    }
  }

  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }
}

// Initialize the application when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new VoicePhishingDetector()
})