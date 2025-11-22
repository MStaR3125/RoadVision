from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import uuid
from pathlib import Path
from typing import Dict
from .processor import VideoProcessor
from . import config

app = FastAPI(title="Road Vision Enterprise")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (Frontend)
# We will serve the frontend from the root
static_dir = config.BASE_DIR / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Job Store (In-memory for simplicity, use Redis/DB for real enterprise)
jobs: Dict[str, Dict] = {}

# Ensure directories exist
os.makedirs(config.DATA_DIR / "uploads", exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)

processor = VideoProcessor()

def process_video_task(job_id: str, input_path: str, output_path: str):
    try:
        jobs[job_id]['status'] = 'processing'
        
        def update_progress(progress):
            jobs[job_id]['progress'] = progress
            
        processor.process_video(input_path, output_path, update_progress)
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 1.0
        jobs[job_id]['output_url'] = f"/api/download/{job_id}"
        
    except Exception as e:
        with open("job_error.log", "a") as f:
            f.write(f"JOB FAILED: {str(e)}\n")
            import traceback
            traceback.print_exc(file=f)
            
        print(f"JOB FAILED: {e}", flush=True)
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)

@app.get("/")
async def read_index():
    index_path = config.BASE_DIR / "frontend" / "index.html"
    return FileResponse(str(index_path))

@app.post("/api/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    
    input_filename = f"{job_id}_{file.filename}"
    input_path = config.DATA_DIR / "uploads" / input_filename
    output_filename = f"processed_{input_filename}"
    output_path = config.OUTPUT_DIR / output_filename
    
    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Initialize job
    jobs[job_id] = {
        'id': job_id,
        'status': 'queued',
        'progress': 0.0,
        'filename': file.filename
    }
    
    # Start background processing
    background_tasks.add_task(process_video_task, job_id, str(input_path), str(output_path))
    
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    if job_id not in jobs or jobs[job_id]['status'] != 'completed':
        raise HTTPException(status_code=404, detail="Result not ready")
        
    # Reconstruct path (in a real app, store this in DB)
    # We need to find the file in the output directory that matches the job ID
    # For simplicity, we'll assume the naming convention holds
    input_filename = f"{job_id}_{jobs[job_id]['filename']}"
    output_filename = f"processed_{input_filename}"
    output_path = config.OUTPUT_DIR / output_filename
    
    return FileResponse(output_path, media_type="video/mp4", filename=f"processed_{jobs[job_id]['filename']}")
