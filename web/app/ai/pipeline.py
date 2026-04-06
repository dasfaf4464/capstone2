"""
AI 분석 파이프라인 — 백그라운드 job 관리
vision_test/app.py 의 _run_job 로직 이식
"""

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import cv2
import numpy as np
from pathlib import Path

from .embeddings import (
    extract_frames, load_model,
    get_text_embedding, get_image_embedding, cosine_similarity,
)

# 분석 job 상태 저장 (in-memory)
# status: 0:대기, 1:전처리, 2:AI분석중, 3:완료
_jobs: dict = {}
_jobs_lock = threading.Lock()

# Vertex AI rate limit: 전체 job에 걸쳐 동시 요청 최대 3개로 제한
_RATE_SEMAPHORE = threading.Semaphore(3)


def get_job(job_id: str) -> dict | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None  # 복사본 반환으로 외부 변경 방지


def register_job(job_id: str, video_path: str):
    """upload 시점에 job 등록."""
    with _jobs_lock:
        _jobs[job_id] = {
            'status':     0,  # 0: 대기
            'message':    '업로드 완료, 분석 대기 중',
            'progress':   0,
            'total':      0,
            'results':    [],
            'video_path': video_path,
        }


def run_job(job_id: str, query: str, max_frames: int, result_folder: str):
    """백그라운드 스레드로 분석 파이프라인 실행."""
    job = _jobs.get(job_id)
    if not job:
        raise KeyError(f"job_id '{job_id}' 가 존재하지 않습니다.")

    thread = threading.Thread(
        target=_execute,
        args=(job_id, job['video_path'], query, max_frames, result_folder),
        daemon=True,
    )
    thread.start()


def _schedule_cleanup(job_id: str, result_folder: str, delay: int = 3600):
    """완료/오류 후 delay초 뒤 job 메모리 + top5 파일 자동 삭제."""
    def _cleanup():
        with _jobs_lock:
            job = _jobs.pop(job_id, None)
        if job:
            for r in job.get('results', []):
                fpath = Path(result_folder) / r['filename']
                fpath.unlink(missing_ok=True)
    threading.Timer(delay, _cleanup).start()


def _execute(job_id: str, video_path: str, query: str,
             max_frames: int, result_folder: str):
    def _update_job(**kwargs):
        with _jobs_lock:
            _jobs[job_id].update(kwargs)

    try:
        _update_job(status=1, message='프레임 추출 중...')  # 1: 전처리

        frames = extract_frames(video_path, max_frames=max_frames)
        _update_job(total=len(frames))

        _update_job(status=2, message='텍스트 임베딩 중...')  # 2: AI 분석 중
        model    = load_model()
        text_vec = get_text_embedding(model, query)

        def _embed_frame(item):
            i, frame_idx, ts, frame_bgr = item
            with _RATE_SEMAPHORE:  # 모듈 레벨 세마포어 — 전체 job에 걸쳐 동시 3개 제한
                img_vec = get_image_embedding(model, frame_bgr)
            score = cosine_similarity(text_vec, img_vec)
            with _jobs_lock:
                _jobs[job_id]['progress'] += 1
                progress = _jobs[job_id]['progress']
            _update_job(message=f'프레임 임베딩 중... ({progress}/{len(frames)})')
            return {
                'frame_idx': frame_idx,
                'timestamp': ts,
                'score':     score,
                'frame_bgr': frame_bgr,
            }

        indexed = [(i, fi, ts, bgr) for i, (fi, ts, bgr) in enumerate(frames)]
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(_embed_frame, item): item for item in indexed}
            for future in as_completed(futures):
                results.append(future.result())

        results.sort(key=lambda x: x['score'], reverse=True)

        scores = np.array([r['score'] for r in results])
        s_min, s_max = scores.min(), scores.max()

        os.makedirs(result_folder, exist_ok=True)
        top5 = []
        for rank, r in enumerate(results[:5], 1):
            fname = f"{job_id}_top{rank}.jpg"
            fpath = os.path.join(result_folder, fname)
            cv2.imwrite(fpath, r['frame_bgr'])

            norm = float((r['score'] - s_min) / (s_max - s_min + 1e-8))
            top5.append({
                'rank':       rank,
                'timestamp':  round(r['timestamp'], 2),
                'score':      round(r['score'], 4),
                'norm_score': round(norm, 4),
                'filename':   fname,
            })

        _update_job(status=3, results=top5, message='완료')  # 3: 완료
        _schedule_cleanup(job_id, result_folder)

    except Exception as e:
        _update_job(status=-1, message=str(e))  # -1: 오류
        _schedule_cleanup(job_id, result_folder)
