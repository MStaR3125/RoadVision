document.addEventListener('DOMContentLoaded', () => {
    const uploadOverlay = document.getElementById('uploadOverlay');
    const fileInput = document.getElementById('fileInput');
    const videoStream = document.getElementById('videoStream');
    const systemStatus = document.getElementById('systemStatus');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Metrics elements
    const offsetValue = document.getElementById('offsetValue');
    const offsetBar = document.getElementById('offsetBar');
    const curvatureValue = document.getElementById('curvatureValue');
    const fpsValue = document.getElementById('fpsValue');
    const signsList = document.getElementById('signsList');

    // Upload Handling
    uploadOverlay.addEventListener('click', () => fileInput.click());

    uploadOverlay.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadOverlay.style.borderColor = 'var(--accent-cyan)';
    });

    uploadOverlay.addEventListener('dragleave', () => {
        uploadOverlay.style.borderColor = 'transparent';
    });

    uploadOverlay.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) handleUpload(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleUpload(e.target.files[0]);
    });

    function handleUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        systemStatus.textContent = 'Uploading...';

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    startStream();
                }
            })
            .catch(err => {
                console.error(err);
                systemStatus.textContent = 'Error Uploading';
            });
    }

    function startStream() {
        uploadOverlay.style.display = 'none';
        loadingOverlay.style.display = 'flex';

        // Wait a moment for backend to initialize
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
            videoStream.style.display = 'block';

            // Force reload of image source to restart stream
            videoStream.src = `/video_feed?t=${new Date().getTime()}`;

            videoStream.onerror = () => {
                systemStatus.textContent = 'Stream Connection Failed';
                systemStatus.style.color = 'var(--accent-magenta)';
                systemStatus.style.borderColor = 'rgba(255, 0, 85, 0.2)';
                systemStatus.style.background = 'rgba(255, 0, 85, 0.1)';
            };

            systemStatus.textContent = 'Processing Live';
            systemStatus.style.color = 'var(--accent-green)';
            systemStatus.style.borderColor = 'rgba(0, 255, 157, 0.2)';
            systemStatus.style.background = 'rgba(0, 255, 157, 0.1)';

            // Start polling metrics
            setInterval(updateMetrics, 500);
        }, 1000);
    }

    function updateMetrics() {
        fetch('/status')
            .then(res => res.json())
            .then(data => {
                // Update text values
                offsetValue.textContent = data.offset.toFixed(2);
                curvatureValue.textContent = Math.round(data.curvature);
                fpsValue.textContent = data.fps.toFixed(1);

                // Update visual bar for offset (0 is center/50%)
                // Range assumed -1m to 1m for full bar width
                const percentage = 50 + (data.offset * 25);
                offsetBar.style.width = `${Math.max(0, Math.min(100, percentage))}%`;

                // Update signs
                if (data.signs && data.signs.length > 0) {
                    signsList.innerHTML = data.signs.map(sign =>
                        `<span class="sign-badge">${sign}</span>`
                    ).join('');
                } else {
                    signsList.innerHTML = '<span class="placeholder">No signs detected</span>';
                }
            });
    }
});
