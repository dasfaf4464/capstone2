let dropZone, fileInput, fileNameDisplay, submitBtn;

document.addEventListener('DOMContentLoaded', () => {
    dropZone = document.getElementById('drop-zone');
    fileInput = document.getElementById('file-input');
    fileNameDisplay = document.getElementById('file-name');
    submitBtn = document.querySelector('.submit-btn');

    // 박스 클릭 시 파일탐색기 열기
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // 탐색기에서 파일 선택 시
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    // 드래그 
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault(); 
        dropZone.classList.add('dragover'); 
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover'); 
    });

    // 드롭 시
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        handleFiles(files);
        fileInput.files = files; 
    });

    if (submitBtn) {
        submitBtn.addEventListener('click', async () => {
            if (fileInput.files.length === 0) {
                alert("먼저 동영상을 업로드해주세요.");
                return;
            }

            const file = fileInput.files[0];
            submitBtn.disabled = true;
            submitBtn.textContent = "동영상 업로드 중...";
            const uuid = await uploadVideo(file);
            if (uuid) {
                submitBtn.textContent = "영상 분석 처리 중...";
                await requestAnalysis(uuid);
            }
            submitBtn.disabled = false;
            submitBtn.textContent = "출력 버튼";
        });
    }
});

// API

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        
        if (file.type.startsWith('video/')) {
            fileNameDisplay.textContent = `선택된 파일: ${file.name}`;
        } else {
            alert("동영상 파일만 업로드 가능합니다.");
            fileNameDisplay.textContent = "";
            fileInput.value = "";
        }
    }
}

// 영상 업로드
async function uploadVideo(file) {
    const formData = new FormData();
    formData.append('video', file); 

    try {
        const response = await fetch('/api/video/upload', {
            method: 'POST', 
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            console.log("업로드 성공:", result);
            return result.video_uuid; 
        } else {
            console.error("업로드 실패 상태:", response.status);
            alert("오류로 업로드에 실패했습니다.");
            return null;
        }
    } catch (error) {
        console.error("네트워크 에러:", error);
        alert("서버와 연결할 수 없습니다.");
        return null;
    }
}

// 영상 처리 요청
async function requestAnalysis(uuid) {
    try {
        const response = await fetch('/api/video/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_uuid: uuid
            })
        });

        if (response.ok) {
            const result = await response.json();
            console.log("영상 분석 결과:", result);
            alert("영상 분석이 완료되었습니다!");
            return result;
        } else {
            console.error("요청 실패 상태:", response.status);
            alert("영상 분석 요청에 실패했습니다.");
        }
    } catch (error) {
        console.error("요청 에러:", error);
        alert("서버와 연결할 수 없습니다.");
    }
}