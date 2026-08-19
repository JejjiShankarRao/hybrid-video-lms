import uuid
from datetime import datetime, timezone
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

# The repository has no provider-specific avatar catalog. These are the
# service-level gender categories used to select and validate avatars.
MALE_AVATAR = "male"
FEMALE_AVATAR = "female"
SUPPORTED_AVATARS = {MALE_AVATAR, FEMALE_AVATAR}
DEFAULT_AVATAR = MALE_AVATAR

def get_voice_gender(voice: str):
    return VOICE_GENDER.get(voice, "neutral")


def get_avatar_for_voice(voice: str, avatar: Optional[str] = None):
    gender = get_voice_gender(voice)
    resolved_gender = DEFAULT_AVATAR if gender == "neutral" else gender

    if avatar is None:
        return resolved_gender

    normalized_avatar = avatar.strip().lower()
    if normalized_avatar not in SUPPORTED_AVATARS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported avatar '{avatar}'. Supported avatars: "
                + ", ".join(sorted(SUPPORTED_AVATARS))
            ),
        )

    if normalized_avatar != resolved_gender:
        if resolved_gender == "male":
            raise HTTPException(
                status_code=400,
                detail="male voice + female avatar is not supported; use a male avatar",
            )
        if resolved_gender == "female":
            raise HTTPException(
                status_code=400,
                detail="female voice + male avatar is not supported; use a female avatar",
            )

    return normalized_avatar


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    estimated_time_remaining: float
    created_at: str
    voice: Optional[str] = None
    gender: Optional[str] = None
    avatar: Optional[str] = None
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
    avatar: Optional[str] = Form(None),
    model: str = Form("latentsync"),
    enhancer: bool = Form(True),
):
    if voice not in VOICE_GENDER:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported voice '{voice}'. Supported voices: "
                + ", ".join(sorted(VOICE_GENDER))
            ),
        )

    gender = get_voice_gender(voice)
    selected_avatar = get_avatar_for_voice(voice, avatar)
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "estimated_time_remaining": 30.0,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "completed_at": None,
        "output_url": None,
        "voice": voice,
        "gender": gender,
        "avatar": selected_avatar,
    }
    background_tasks.add_task(dummy_rendering_task, job_id)

    return {
        "job_id": job_id,
        "status": "queued",
        "created_at": jobs_db[job_id]["created_at"],
        "voice": voice,
        "gender": gender,
        "avatar": selected_avatar,
        "message": "Avatar rendering job successfully queued.",
    }


@app.get("/api/v1/avatar/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs_db[job_id]
