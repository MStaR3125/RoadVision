const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const jobsList = document.getElementById('jobsList');
const resultVideo = document.getElementById('resultVideo');
const videoPlaceholder = document.getElementById('videoPlaceholder');

// State
let jobs = [];
let activeJobId = null;

// Drag & Drop
dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleUpload(e.target.files[0]);
});

async function handleUpload(file) {
    // Show progress UI
    document.querySelector('.dropzone-content').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'block';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Upload failed');

        const data = await res.json();
        addJob(data.job_id, file.name);

        // Reset UI
        setTimeout(() => {
            document.querySelector('.dropzone-content').style.display = 'flex';
            document.getElementById('uploadProgress').style.display = 'none';
        }, 1000);

    } catch (err) {
        console.error(err);
        alert('Upload failed');
        document.querySelector('.dropzone-content').style.display = 'flex';
        document.getElementById('uploadProgress').style.display = 'none';
    }
}

function addJob(id, filename) {
    const job = {
        id,
        filename,
        status: 'queued',
        progress: 0
    };
    jobs.unshift(job);
    renderJobs();
    pollJob(id);
}

function renderJobs() {
    if (jobs.length === 0) {
        jobsList.innerHTML = '<div class="empty-state">No jobs yet</div>';
        return;
    }

    jobsList.innerHTML = jobs.map(job => `
        <div class="job-item ${activeJobId === job.id ? 'active' : ''}" onclick="selectJob('${job.id}')">
            <div class="job-info">
                <h4>${job.filename}</h4>
                <div class="job-meta">ID: ${job.id.substring(0, 8)}</div>
            </div>
            <div class="job-status">
                <span class="status-badge status-${job.status}">
                    ${job.status === 'processing' ? Math.round(job.progress * 100) + '%' : job.status}
                </span>
            </div>
        </div>
    `).join('');
}

function selectJob(id) {
    activeJobId = id;
    renderJobs();

    const job = jobs.find(j => j.id === id);
    if (job && job.status === 'completed') {
        videoPlaceholder.style.display = 'none';
        resultVideo.style.display = 'block';
        resultVideo.src = `/api/download/${id}`;
        resultVideo.play();

        // Show overlay legend
        document.getElementById('legendOverlay').style.display = 'block';
    } else {
        videoPlaceholder.style.display = 'flex';
        resultVideo.style.display = 'none';
        resultVideo.pause();

        // Hide overlay legend
        document.getElementById('legendOverlay').style.display = 'none';
    }
}

async function pollJob(id) {
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/api/jobs/${id}`);
            const data = await res.json();

            // Update local state
            const jobIndex = jobs.findIndex(j => j.id === id);
            if (jobIndex !== -1) {
                jobs[jobIndex] = { ...jobs[jobIndex], ...data };
                renderJobs();
            }

            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(interval);
                if (data.status === 'completed' && !activeJobId) {
                    selectJob(id); // Auto-select first completed job
                }
            }
        } catch (err) {
            console.error('Polling error', err);
        }
    }, 1000);
}
