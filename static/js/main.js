// DOM 요소들
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const uploadArea = document.getElementById('uploadArea');
const resetBtn = document.getElementById('resetBtn');
const queryInput = document.getElementById('queryInput');
const sendBtn = document.getElementById('sendBtn');
const reportBtn = document.getElementById('reportBtn');
const chatMessages = document.getElementById('chatMessages');
const documentList = document.getElementById('documentList');

let currentFile = null;
let uploadedDocuments = [];

// 이벤트 리스너 등록
uploadBtn.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', uploadFile);
resetBtn.addEventListener('click', manualResetSession);
sendBtn.addEventListener('click', sendMessage);
reportBtn.addEventListener('click', generateReport);

// Enter 키로 메시지 전송
queryInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 제안 카드 클릭 이벤트
document.addEventListener('click', function(e) {
    if (e.target.closest('.suggestion-card')) {
        const prompt = e.target.closest('.suggestion-card').dataset.prompt;
        if (prompt) {
            queryInput.value = prompt;
            sendMessage();
        }
    }
});

// 드래그 앤 드롭 기능 강화
setupDragAndDrop();

function setupDragAndDrop() {
    // 전체 업로드 영역에 드래그 앤 드롭 설정
    const dragEvents = ['dragenter', 'dragover', 'dragleave', 'drop'];
    
    dragEvents.forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // 드래그 진입/종료 효과
    uploadArea.addEventListener('dragenter', handleDragEnter);
    uploadArea.addEventListener('dragover', handleDragEnter);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    function handleDragEnter(e) {
        uploadArea.classList.add('dragover');
    }

    function handleDragLeave(e) {
        // 실제로 영역을 벗어났는지 확인
        if (!uploadArea.contains(e.relatedTarget)) {
            uploadArea.classList.remove('dragover');
        }
    }

    function handleDrop(e) {
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        
        if (files.length > 0) {
            const file = files[0];
            fileInput.files = files;
            handleFileSelection(file);
        }
    }
}

// 파일 선택 처리
function handleFileSelection(file) {
    // 파일 유효성 검사
    if (!validateFile(file)) {
        return;
    }
    
    // 미리보기 업데이트
    updateUploadPreview(file);
    
    // 자동 업로드 (선택적)
    // uploadFile();
}

// 파일 유효성 검사
function validateFile(file) {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (file.size > maxSize) {
        showNotification('파일 크기가 너무 큽니다. (16MB 제한)', 'error');
        return false;
    }
    
    if (!allowedExtensions.includes(fileExtension)) {
        showNotification(`지원하지 않는 파일 형식입니다. 지원 형식: ${allowedExtensions.join(', ')}`, 'error');
        return false;
    }
    
    return true;
}

// 업로드 미리보기 업데이트
function updateUploadPreview(file) {
    const uploadText = uploadArea.querySelector('.upload-text');
    const originalHTML = uploadText.innerHTML;
    
    uploadText.innerHTML = `
        <p><strong>선택된 파일: ${file.name}</strong></p>
        <p class="upload-subtitle">크기: ${formatFileSize(file.size)}</p>
        <p class="upload-subtitle">업로드하려면 '파일 선택' 버튼을 클릭하세요</p>
    `;
    
    // 3초 후 원래 텍스트로 복원 (업로드하지 않은 경우)
    setTimeout(() => {
        if (!currentFile || currentFile !== file.name) {
            uploadText.innerHTML = originalHTML;
        }
    }, 3000);
}

// 파일 크기 포맷팅
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 수동 세션 리셋 함수
async function manualResetSession() {
    try {
        resetBtn.disabled = true;
        resetBtn.textContent = '리셋 중...';
        
        showNotification('세션을 리셋하고 기존 데이터를 삭제합니다...', 'info');
        
        await restartSession();
        
        // UI 초기화
        currentFile = null;
        uploadedDocuments = [];
        updateDocumentList();
        clearChatMessages();
        showWelcomeMessage();
        
        // 채팅은 항상 활성화 상태로 유지
        queryInput.disabled = false;
        sendBtn.disabled = false;
        reportBtn.disabled = false;
        queryInput.placeholder = '어떤걸 물어보시겠어요?';
        fileInput.value = '';
        
        showNotification('새 세션이 시작되었습니다. 파일 업로드 없이도 대화하거나 새 파일을 업로드할 수 있습니다.', 'success');
        
    } catch (error) {
        console.error('Manual reset error:', error);
        showNotification(`세션 리셋 오류: ${error.message}`, 'error');
    } finally {
        resetBtn.disabled = false;
        resetBtn.textContent = '새로운 대화 시작하기';
    }
}

// 세션 재시작 함수
async function restartSession() {
    try {
        const response = await fetch('/restart_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        if (result.success) {
            console.log('세션 재시작 완료:', result.message);
            currentFile = null;
        } else {
            console.error('세션 재시작 실패:', result.message);
        }
    } catch (error) {
        console.error('세션 재시작 오류:', error);
    }
}

// 파일 업로드 함수
async function uploadFile() {
    const file = fileInput.files[0];
    if (!file) {
        showNotification('파일을 선택해주세요.', 'error');
        return;
    }

    if (!validateFile(file)) {
        return;
    }

    // 기존 파일이 있는 경우 새 세션 시작
    if (currentFile) {
        showNotification('기존 데이터를 삭제하고 새 파일을 업로드합니다...', 'info');
        await restartSession();
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        uploadBtn.disabled = true;
        uploadBtn.textContent = '업로드 중...';
        uploadBtn.classList.add('loading');
        
        showNotification(`${file.name} 파일을 업로드하고 있습니다...`, 'info');
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        
        if (result.success) {
            currentFile = result.file_path;
            
            // 업로드된 문서 목록에 추가
            addDocumentToList({
                name: file.name,
                size: formatFileSize(file.size),
                chunks: result.chunks_count,
                uploadTime: new Date().toLocaleString()
            });
            
            showNotification(`${result.message}`, 'success');
            enableChat();
            clearWelcomeMessage();
            
            fileInput.value = '';
        } else {
            showNotification(`업로드 실패: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification(`업로드 오류: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '파일 선택';
        uploadBtn.classList.remove('loading');
    }
}

// 문서 목록에 추가
function addDocumentToList(document) {
    uploadedDocuments.push(document);
    updateDocumentList();
}

// 문서 목록 업데이트
function updateDocumentList() {
    if (uploadedDocuments.length === 0) {
        documentList.innerHTML = '<p style="text-align: center; color: #656d76; font-size: 14px; padding: 20px;">업로드된 문서가 없습니다</p>';
        return;
    }
    
    documentList.innerHTML = uploadedDocuments.map((doc, index) => `
        <div class="document-item" data-index="${index}">
            <span class="document-icon"></span>
            <div class="document-info">
                <span class="document-name">${doc.name}</span>
                <span class="document-size">${doc.size} • ${doc.chunks || 0}개 청크</span>
            </div>
            <div class="document-actions">
                <button class="document-action" onclick="removeDocument(${index})" title="삭제">🗑️</button>
            </div>
        </div>
    `).join('');
}

// 문서 삭제
function removeDocument(index) {
    if (confirm('이 문서를 삭제하시겠습니까?')) {
        uploadedDocuments.splice(index, 1);
        updateDocumentList();
        
        if (uploadedDocuments.length === 0) {
            currentFile = null;
            // 문서가 없어도 채팅은 계속 사용 가능
            queryInput.disabled = false;
            sendBtn.disabled = false;
            reportBtn.disabled = false;
            queryInput.placeholder = '어떤걸 물어보시겠어요?';
            showWelcomeMessage();
        }
    }
}

// 메시지 전송 함수
async function sendMessage() {
    const query = queryInput.value.trim();
    if (!query) return;

    // 환영 메시지 제거
    clearWelcomeMessage();
    
    // 사용자 메시지 표시
    addMessageToChat('user', query);
    queryInput.value = '';

    try {
        sendBtn.disabled = true;
        sendBtn.classList.add('loading');
        
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                file_path: currentFile
            })
        });

        const result = await response.json();
        
        if (result.success) {
            addMessageToChat('ai', result.response);
        } else {
            addMessageToChat('ai', `오류: ${result.message}`);
        }
    } catch (error) {
        addMessageToChat('ai', `요청 오류: ${error.message}`);
    } finally {
        sendBtn.disabled = false;
        sendBtn.classList.remove('loading');
    }
}

// 보고서 생성 함수
async function generateReport() {
    const query = queryInput.value.trim() || '업로드된 문서를 바탕으로 1분 스피치를 작성해주세요.';

    try {
        reportBtn.disabled = true;
        reportBtn.textContent = '생성 중...';
        reportBtn.classList.add('loading');
        
        addMessageToChat('system', '1분 스피치를 생성하고 있습니다. 잠시만 기다려주세요...');
        
        const response = await fetch('/generate_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                format: 'docx'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        
        if (result.success) {
            addMessageToChat('ai', '1분 스피치가 성공적으로 생성되었습니다!');
            
            if (result.content && result.content.length > 50) {
                const preview = result.content.substring(0, 200) + (result.content.length > 200 ? '...' : '');
                addMessageToChat('ai', `미리보기:\n${preview}`);
            }
            
            // 다운로드 버튼 추가
            addDownloadButton(result.download_url, result.filename || '1분_스피치.docx');
            
        } else {
            addMessageToChat('ai', `1분 스피치 생성 실패: ${result.message}`);
        }
    } catch (error) {
        console.error('Report generation error:', error);
        addMessageToChat('ai', `1분 스피치 생성 오류: ${error.message}`);
    } finally {
        reportBtn.disabled = false;
        reportBtn.textContent = '1분 스피치 생성';
        reportBtn.classList.remove('loading');
    }
}

// 다운로드 버튼 추가
function addDownloadButton(downloadUrl, filename) {
    const downloadDiv = document.createElement('div');
    downloadDiv.style.marginTop = '15px';
    downloadDiv.style.padding = '15px';
    downloadDiv.style.background = 'linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%)';
    downloadDiv.style.borderRadius = '12px';
    downloadDiv.style.border = '1px solid #28a745';
    downloadDiv.style.textAlign = 'center';
    
    const downloadLink = document.createElement('a');
    downloadLink.href = downloadUrl;
    downloadLink.textContent = `${filename} 다운로드`;
    downloadLink.className = 'btn btn-success';
    downloadLink.style.textDecoration = 'none';
    downloadLink.style.color = 'white';
    downloadLink.style.background = '#28a745';
    downloadLink.style.padding = '10px 20px';
    downloadLink.style.borderRadius = '8px';
    downloadLink.style.display = 'inline-block';
    downloadLink.style.fontWeight = '500';
    downloadLink.style.transition = 'all 0.3s ease';
    
    downloadLink.addEventListener('mouseenter', () => {
        downloadLink.style.background = '#218838';
        downloadLink.style.transform = 'translateY(-1px)';
    });
    
    downloadLink.addEventListener('mouseleave', () => {
        downloadLink.style.background = '#28a745';
        downloadLink.style.transform = 'translateY(0)';
    });
    
    downloadDiv.appendChild(downloadLink);
    
    const lastMessage = chatMessages.lastElementChild;
    if (lastMessage) {
        lastMessage.appendChild(downloadDiv);
    }
}

// 채팅에 메시지 추가
function addMessageToChat(sender, message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = message.replace(/\n/g, '<br>');
    } else if (sender === 'system') {
        messageDiv.innerHTML = message.replace(/\n/g, '<br>');
    } else {
        messageDiv.innerHTML = message.replace(/\n/g, '<br>');
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 알림 표시
function showNotification(message, type = 'info') {
    addMessageToChat('system', message);
}

// 채팅 활성화
function enableChat() {
    queryInput.disabled = false;
    sendBtn.disabled = false;
    reportBtn.disabled = false;
    queryInput.placeholder = '어떤걸 물어보시겠어요?';
}

// 환영 메시지 표시
function showWelcomeMessage() {
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'block';
    }
}

// 환영 메시지 제거
function clearWelcomeMessage() {
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
}

// 채팅 메시지 초기화
function clearChatMessages() {
    chatMessages.innerHTML = '';
}

// 페이지 종료 시 세션 정리
window.addEventListener('beforeunload', function(event) {
    if (currentFile) {
        fetch('/cleanup_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }).catch(console.error);
    }
});

// 초기 상태 설정
document.addEventListener('DOMContentLoaded', function() {
    // 파일 업로드 없이도 채팅 가능하도록 활성화
    queryInput.disabled = false;
    sendBtn.disabled = false;
    reportBtn.disabled = false;
    queryInput.placeholder = '어떤걸 물어보시겠어요?';
    
    updateDocumentList();
    showWelcomeMessage();
    
    // 초기 시스템 메시지
    setTimeout(() => {
        addMessageToChat('system', '1MinSpeech에 오신 것을 환영합니다! 파일 업로드 없이도 자유롭게 대화하거나, 왼쪽에서 문서를 업로드하여 문서 기반 대화를 시작할 수 있습니다.');
    }, 500);
});