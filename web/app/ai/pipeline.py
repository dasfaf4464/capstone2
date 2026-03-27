"""
AI 분석 파이프라인 — 백그라운드 job 관리
vision_test/app.py 의 _run_job 로직 이식
"""

import os
import time
import threading
import cv2
import numpy as np

from .embeddings import (
    extract_frames, load_model,
    get_text_embedding, get_image_embedding, cosine_similarity,
)

# 분석 job 상태 저장 (in-memory)
# status: 0:대기, 1:전처리, 2:AI분석중, 3:완료
_jobs: dict = {}


def get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)


def register_job(job_id: str, video_path: str):
    """upload 시점에 job 등록."""
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


def _execute(job_id: str, video_path: str, query: str,
             max_frames: int, result_folder: str):
    try:
        _jobs[job_id]['status']  = 1  # 1: 전처리
        _jobs[job_id]['message'] = '프레임 추출 중...'

        frames = extract_frames(video_path, max_frames=max_frames)
        _jobs[job_id]['total'] = len(frames)

        _jobs[job_id]['status']  = 2  # 2: AI 분석 중
        _jobs[job_id]['message'] = '텍스트 임베딩 중...'
        model    = load_model()
        text_vec = get_text_embedding(model, query)

        results = []
        for i, (frame_idx, ts, frame_bgr) in enumerate(frames):
            _jobs[job_id]['message']  = f'프레임 임베딩 중... ({i+1}/{len(frames)})'
            _jobs[job_id]['progress'] = i + 1

            img_vec = get_image_embedding(model, frame_bgr)
            score   = cosine_similarity(text_vec, img_vec)
            results.append({
                'frame_idx': frame_idx,
                'timestamp': ts,
                'score':     score,
                'frame_bgr': frame_bgr,
            })
            time.sleep(0.5)  # Vertex AI rate limit 방지

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
                # TODO: DB images 테이블에 image_path, image_query 저장
            })

        _jobs[job_id]['status']  = 3  # 3: 완료
        _jobs[job_id]['results'] = top5
        _jobs[job_id]['message'] = '완료'

    except Exception as e:
        _jobs[job_id]['status']  = -1  # -1: 오류
        _jobs[job_id]['message'] = str(e)
