"""
Vertex AI Multimodal Embeddings 유틸리티
vision_test/test_vertex.py 에서 이식
"""

import os
import cv2
import numpy as np
from dotenv import load_dotenv

from .preprocessing import extract_frames_ffmpeg, preprocess_frame_bgr

load_dotenv()

GCP_PROJECT  = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")


def extract_frames(
    video_path: str,
    max_frames: int = 100,
    use_ffmpeg: bool = True,
    preprocess: bool = True,
):
    """
    균등 간격으로 max_frames 장 추출. (frame_idx, timestamp_sec, bgr_array) 반환.

    use_ffmpeg=True  : ffmpeg 파이프라인으로 추출 + 전처리 (기본)
    use_ffmpeg=False : OpenCV fallback (전처리 별도 적용 가능)
    preprocess       : use_ffmpeg=False 일 때 ffmpeg 후처리 적용 여부
    """
    if use_ffmpeg:
        return extract_frames_ffmpeg(video_path, max_frames=max_frames)

    # --- OpenCV fallback ---
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    total   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps     = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step    = max(1, total // max_frames)
    indices = list(range(0, total, step))[:max_frames]

    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            if preprocess:
                frame = preprocess_frame_bgr(frame)
            frames.append((idx, idx / fps, frame))

    cap.release()
    return frames


def load_model():
    """Vertex AI MultiModalEmbeddingModel 로드."""
    import vertexai
    from vertexai.vision_models import MultiModalEmbeddingModel
    from google.oauth2 import service_account

    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not key_path or not os.path.exists(key_path):
        raise RuntimeError(
            f"서비스 계정 키 파일을 찾을 수 없습니다: '{key_path}'\n"
            ".env의 GOOGLE_APPLICATION_CREDENTIALS 경로를 확인하세요."
        )

    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION, credentials=credentials)
    return MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")


def cosine_similarity(a, b) -> float:
    a, b = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 1e-8 else 0.0


def get_text_embedding(model, query: str) -> list:
    emb = model.get_embeddings(contextual_text=query)
    return emb.text_embedding


def get_image_embedding(model, frame_bgr) -> list:
    from vertexai.vision_models import Image as VImage
    ok, buf = cv2.imencode('.jpg', frame_bgr)
    if not ok:
        raise RuntimeError("imencode 실패")
    img = VImage(image_bytes=buf.tobytes())
    emb = model.get_embeddings(image=img)
    return emb.image_embedding
