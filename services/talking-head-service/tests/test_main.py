from fastapi.testclient import TestClient
from src.main import (
    DEFAULT_AVATAR,
    FEMALE_AVATAR,
    MALE_AVATAR,
    VOICE_GENDER,
    app,
    get_avatar_for_voice,
)

client = TestClient(app)


def make_uploads():
    return [
        ("face_image", ("face.png", b"fake image bytes", "image/png")),
        ("audio", ("audio.wav", b"fake audio bytes", "audio/wav")),
    ]


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "AI Talking Head Service", "status": "healthy"}


def post_generation(voice, avatar=None):
    data = {"voice": voice}
    if avatar is not None:
        data["avatar"] = avatar
    return client.post("/api/v1/avatar/generate", files=make_uploads(), data=data)


def test_male_voices_select_male_avatar():
    for voice in (
        "en-US-ChristopherNeural",
        "en-US-GuyNeural",
        "en-GB-RyanNeural",
        "en-IN-PrabhatNeural",
    ):
        response = post_generation(voice)
        assert response.status_code == 202
        body = response.json()
        assert body["gender"] == "male"
        assert body["avatar"] == MALE_AVATAR


def test_female_voices_select_female_avatar():
    for voice in (
        "en-US-JennyNeural",
        "en-GB-SoniaNeural",
        "en-IN-NeerjaNeural",
    ):
        response = post_generation(voice)
        assert response.status_code == 202
        body = response.json()
        assert body["gender"] == "female"
        assert body["avatar"] == FEMALE_AVATAR


def test_male_voice_matches_male_avatar():
    response = client.post(
        "/api/v1/avatar/generate",
        files=make_uploads(),
        data={"voice": "en-US-ChristopherNeural", "avatar": MALE_AVATAR},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["voice"] == "en-US-ChristopherNeural"
    assert body["gender"] == "male"
    assert body["avatar"] == MALE_AVATAR


def test_default_avatar_matches_male_voice_when_avatar_missing():
    response = post_generation("en-US-ChristopherNeural")
    assert response.status_code == 202
    assert response.json()["avatar"] == MALE_AVATAR

    job_response = client.get(f"/api/v1/avatar/jobs/{response.json()['job_id']}")
    assert job_response.status_code == 200
    assert job_response.json()["avatar"] == MALE_AVATAR


def test_female_voice_matches_female_avatar():
    response = client.post(
        "/api/v1/avatar/generate",
        files=make_uploads(),
        data={"voice": "en-US-JennyNeural", "avatar": FEMALE_AVATAR},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["voice"] == "en-US-JennyNeural"
    assert body["gender"] == "female"
    assert body["avatar"] == FEMALE_AVATAR


def test_default_avatar_matches_female_voice_when_avatar_missing():
    response = client.post(
        "/api/v1/avatar/generate",
        files=make_uploads(),
        data={"voice": "en-US-JennyNeural"},
    )
    assert response.status_code == 202
    assert response.json()["avatar"] == FEMALE_AVATAR


def test_unsupported_voice_returns_400():
    response = client.post(
        "/api/v1/avatar/generate",
        files=make_uploads(),
        data={"voice": "en-US-UnknownNeural"},
    )
    assert response.status_code == 400
    assert "Unsupported voice" in response.json()["detail"]


def test_unsupported_avatar_returns_400():
    response = client.post(
        "/api/v1/avatar/generate",
        files=make_uploads(),
        data={"voice": "en-US-ChristopherNeural", "avatar": "robot"},
    )
    assert response.status_code == 400
    assert "Unsupported avatar" in response.json()["detail"]


def test_male_voice_rejects_female_avatar():
    response = client.post(
        "/api/v1/avatar/generate",
        files=make_uploads(),
        data={"voice": "en-US-ChristopherNeural", "avatar": FEMALE_AVATAR},
    )
    assert response.status_code == 400
    assert "male voice" in response.json()["detail"].lower()
    assert "female avatar" in response.json()["detail"].lower()


def test_female_voice_rejects_male_avatar():
    response = client.post(
        "/api/v1/avatar/generate",
        files=make_uploads(),
        data={"voice": "en-US-JennyNeural", "avatar": MALE_AVATAR},
    )
    assert response.status_code == 400
    assert "female voice" in response.json()["detail"].lower()
    assert "male avatar" in response.json()["detail"].lower()


def test_unknown_gender_falls_back_to_default_avatar():
    assert get_avatar_for_voice("unknown-voice") == DEFAULT_AVATAR
    assert get_avatar_for_voice("unknown-voice", DEFAULT_AVATAR) == DEFAULT_AVATAR


def test_voice_gender_mapping_contains_all_supported_voices():
    assert set(VOICE_GENDER) == {
        "en-US-ChristopherNeural",
        "en-US-GuyNeural",
        "en-GB-RyanNeural",
        "en-IN-PrabhatNeural",
        "en-US-JennyNeural",
        "en-GB-SoniaNeural",
        "en-IN-NeerjaNeural",
    }
