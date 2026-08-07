import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

app = FastAPI(
    title="AI Talking Head Service",
    description="REST API for generating lip-synced talking head avatars",
    version="1.0.0",
)

# In-memory job state store
jobs_db: Dict[str, dict] = {}

VOICE_GENDER = {
    "en-US-ChristopherNeural": "male",
    "en-US-GuyNeural": "male",
    "en-GB-RyanNeural": "male",
    "en-IN-PrabhatNeural": "male",
    "en-US-JennyNeural": "female",
    "en-GB-SoniaNeural": "female",
    "en-IN-NeerjaNeural": "female",
}


def get_voice_gender(voice: str):
    return VOICE_GENDER.get(voice, "neutral")

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    estimated_time_remaining: float
    created_at: str
    completed_at: Optional[str] = None
    output_url: Optional[str] = None


def dummy_rendering_task(job_id: str):
    # This is a placeholder task simulation
    jobs_db[job_id]["status"] = "rendering"
    jobs_db[job_id]["progress"] = 50.0


@app.get("/")
def read_root():
    return {"name": "AI Talking Head Service", "status": "healthy"}


@app.post("/api/v1/avatar/generate", status_code=202)
def generate_avatar(
    background_tasks: BackgroundTasks,
    face_image: UploadFile = File(...),
    audio: UploadFile = File(...),
    voice: str = Form("en-US-ChristopherNeural"),
    model: str = Form("latentsync"),
    enhancer: bool = Form(True),
):

    job_id = f"job_{uuid.uuid4().hex[:12]}"

    gender = get_voice_gender(voice)
    # Store initial state
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "estimated_time_remaining": 30.0,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None,
        "output_url": None,
    "voice": voice,
    "gender": gender,
    }

    # Trigger background work simulation
    background_tasks.add_task(dummy_rendering_task, job_id)

    return {
        "job_id": job_id,
        "status": "queued",
        "created_at": jobs_db[job_id]["created_at"],
        "message": "Avatar rendering job successfully queued.",
    }


@app.get("/api/v1/avatar/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs_db[job_id]
