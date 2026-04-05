let currentImageData = []; 
let currentLayout = 'layout-1'; 

function changeLayout(layoutType, clickedButton) {
    currentLayout = layoutType; 

    const sidebarButtons = document.querySelectorAll('.sidebar-item');
    sidebarButtons.forEach(button => {
        button.classList.remove('active');
    });
    clickedButton.classList.add('active');

    const detailView = document.getElementById('detail-view');
    const galleryView = document.getElementById('gallery-view');
    
    if (detailView.style.display === 'block') {
        detailView.style.display = 'none';
        galleryView.style.display = 'block';
        document.getElementById('page-header').innerText = '아카이브';
    }

    renderGallery(); 
}

function closeDetail() {
    document.getElementById('detail-view').style.display = 'none';
    document.getElementById('gallery-view').style.display = 'block';
    document.getElementById('page-header').innerText = '아카이브';
}

async function fetchImageArchive() {
    try {
        const response = await fetch(`/api/archive/list`, { method: 'GET' });

        if (response.ok) {
            const data = await response.json();
            currentImageData = data.items || []; 
            renderGallery(); 
        } else {
            alert("이미지 목록을 불러오는데 실패했습니다.");
        }
    } catch (error) {
        console.error(error);
    }
}

function renderGallery() {
    const gallery = document.getElementById('photo-gallery');
    gallery.innerHTML = ''; 
    gallery.className = currentLayout; 

    if (!currentImageData || currentImageData.length === 0) {
        gallery.innerHTML = '<p style="text-align:center; padding:20px;">저장된 사진이 없습니다.</p>';
        return;
    }

    if (currentLayout === 'layout-3') {
        currentImageData.forEach(item => {
            const photoDiv = document.createElement('div');
            photoDiv.className = 'photo-item';
            photoDiv.innerText = item.frame_id || '사진';

            photoDiv.onclick = function() { openDetail(this, item); };
            gallery.appendChild(photoDiv);
        });
    } else {
        const categorizedData = {};
        
        currentImageData.forEach(item => {
            const tags = (item.refined_tags && item.refined_tags.length > 0) 
                         ? item.refined_tags : ['미분류'];
            
            tags.forEach(tag => {
                if (!categorizedData[tag]) categorizedData[tag] = [];
                categorizedData[tag].push(item);
            });
        });

        for (const category in categorizedData) {
            const categoryTitle = document.createElement('h3');
            categoryTitle.innerText = category;
            categoryTitle.style.width = '100%';
            categoryTitle.style.marginTop = '20px';
            categoryTitle.style.marginBottom = '10px';
            categoryTitle.style.borderBottom = '2px solid #eee';
            gallery.appendChild(categoryTitle);

            const categoryContainer = document.createElement('div');
            categoryContainer.style.display = 'flex';
            categoryContainer.style.flexWrap = 'wrap';
            categoryContainer.style.gap = '10px';

            categorizedData[category].forEach(item => {
                const photoDiv = document.createElement('div');
                photoDiv.className = 'photo-item';
                photoDiv.innerText = item.frame_id || '사진';

                photoDiv.onclick = function() { openDetail(this, item); };
                categoryContainer.appendChild(photoDiv);
            });

            gallery.appendChild(categoryContainer);
        }
    }
}

function openDetail(photoElement, itemData = null) {
    document.getElementById('gallery-view').style.display = 'none';
    document.getElementById('detail-view').style.display = 'block';
    document.getElementById('page-header').innerText = '아카이브 (이미지 상세)';

    const downloadBtn = document.getElementById('btn-download');
    const photoDisplay = document.getElementById('selected-photo-display');

    if (itemData) {
        const tags = itemData.refined_tags ? itemData.refined_tags.join(', ') : "미분류";
        
        document.getElementById('info-name').innerText = itemData.frame_id || "파일명 없음";
        document.getElementById('info-category').innerText = tags;
        document.getElementById('info-accuracy').innerText = "정보 없음";
        document.getElementById('info-date').innerText = itemData.timestamp ? itemData.timestamp + "초" : "시간 정보 없음";
        document.getElementById('info-prompt').innerText = "프롬프트 없음";

        if (itemData.frame_id) {
            photoDisplay.innerHTML = `
                <img src="/api/archive/download/${itemData.frame_id}.jpg" 
                     alt="${itemData.frame_id}" 
                     style="max-width: 100%; max-height: 100%; object-fit: contain;">
            `;
        } else {
            photoDisplay.innerText = "이미지를 불러올 수 없습니다.";
        }
        
        downloadBtn.onclick = () => downloadImage(itemData.frame_id + '.jpg');
    } else {
        const photoName = photoElement.innerText;
        document.getElementById('info-name').innerText = photoName + ".jpg";
        document.getElementById('info-category').innerText = "인물";
        document.getElementById('info-accuracy').innerText = "95%";
        document.getElementById('info-date').innerText = "시간 정보 없음";
        document.getElementById('info-prompt').innerText = "프롬프트 없음";
        
        photoDisplay.innerText = photoName;
        downloadBtn.onclick = () => downloadImage('dummy_frame_id.jpg');
    }
}

async function downloadImage(frameId) {
    try {
        const response = await fetch(`/api/archive/download/${frameId}`, {
            method: 'GET',
        });

        if (response.ok) {
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = frameId; 
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } else {
            alert(`이미지 다운로드 실패 (상태 코드: ${response.status})`);
        }
    } catch (error) {
        console.error(error);
        alert("서버 연결 실패");
    }
}

window.addEventListener('DOMContentLoaded', () => {
    fetchImageArchive(); 
});