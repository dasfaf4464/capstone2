"""
ffmpeg 기반 이미지 전처리 유틸리티
- 프레임 추출 (균등 간격)
- 리사이즈
- 디노이즈 (hqdn3d)
- 밝기/대비 정규화 (eq)
"""

import os
import ffmpeg
import numpy as np


# Vertex AI multimodalembedding@001 권장 입력 크기
DEFAULT_SIZE = (512, 512)


def get_video_info(video_path: str) -> dict:
    """ffprobe로 영상 메타데이터 반환."""
    probe = ffmpeg.probe(video_path)
    vs = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    fps_raw = vs.get('r_frame_rate', '30/1')
    num, den = map(int, fps_raw.split('/'))
    fps = num / den if den else 30.0
    return {
        'width':       int(vs['width']),
        'height':      int(vs['height']),
        'fps':         fps,
        'total_frames': int(vs.get('nb_frames', 0)),
        'duration':    float(probe['format'].get('duration', 0)),
    }


def extract_frames_ffmpeg(
    video_path: str,
    max_frames: int = 100,
    size: tuple[int, int] = DEFAULT_SIZE,
    denoise: bool = True,
    normalize: bool = True,
) -> list[tuple[int, float, np.ndarray]]:
    """
    ffmpeg 파이프라인으로 프레임을 추출하고 전처리.

    Parameters
    ----------
    video_path  : 입력 영상 경로
    max_frames  : 최대 추출 프레임 수
    size        : (width, height) 리사이즈 목표 크기
    denoise     : hqdn3d 디노이즈 필터 적용 여부
    normalize   : eq 필터로 밝기/대비 정규화 여부

    Returns
    -------
    list of (frame_idx, timestamp_sec, bgr_ndarray)
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"영상 파일 없음: {video_path}")

    info = get_video_info(video_path)
    fps = info['fps']
    duration = info['duration']

    # 균등 간격 타임스탬프 계산
    if duration <= 0:
        raise RuntimeError("영상 duration을 읽을 수 없습니다.")

    timestamps = _build_timestamps(video_path, duration, max_frames)

    w, h = size
    frames = []

    for ts in timestamps:
        raw = _extract_single_frame(video_path, ts, w, h, denoise, normalize)
        if raw is None:
            continue
        frame_idx = int(ts * fps)
        # RGB → BGR (OpenCV 호환)
        bgr = raw[:, :, ::-1].copy()
        frames.append((frame_idx, ts, bgr))

    return frames


def preprocess_frame_bgr(
    frame_bgr: np.ndarray,
    size: tuple[int, int] = DEFAULT_SIZE,
    denoise: bool = True,
    normalize: bool = True,
) -> np.ndarray:
    """
    이미 추출된 BGR 프레임에 ffmpeg 전처리 적용.
    (OpenCV extract_frames 결과물에 후처리할 때 사용)

    Returns
    -------
    전처리된 BGR ndarray
    """
    import tempfile, cv2

    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cv2.imwrite(tmp_path, frame_bgr)
        w, h = size
        raw = _apply_filters_to_image(tmp_path, w, h, denoise, normalize)
    finally:
        os.unlink(tmp_path)

    if raw is None:
        # 필터 실패 시 OpenCV 리사이즈만 수행
        import cv2
        return cv2.resize(frame_bgr, size)

    # RGB → BGR
    return raw[:, :, ::-1].copy()


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _detect_scene_changes(video_path: str, threshold: float = 0.3) -> list[float]:
    """
    ffmpeg select 필터로 장면 전환 타임스탬프 목록 반환.
    threshold: 0.0~1.0, 높을수록 큰 변화만 감지
    """
    try:
        out, _ = (
            ffmpeg
            .input(video_path)
            .video
            .filter('select', f'gt(scene,{threshold})')
            .filter('showinfo')
            .output('pipe:', format='null', vsync='vfr')
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        # showinfo 출력에서 pts_time 파싱
        import re
        stderr_text = _.decode('utf-8', errors='ignore')
        timestamps = [
            float(m.group(1))
            for m in re.finditer(r'pts_time:([\d.]+)', stderr_text)
        ]
        return sorted(timestamps)
    except Exception:
        return []


def _build_timestamps(video_path: str, duration: float, max_frames: int) -> list[float]:
    """
    장면 전환 타임스탬프 + 균등 보완으로 max_frames 개 타임스탬프 구성.
    장면 전환 감지 실패 시 균등 분포로 폴백.
    """
    scene_ts = _detect_scene_changes(video_path)

    if not scene_ts:
        # 폴백: 균등 분포
        return np.linspace(0, duration, max_frames, endpoint=False).tolist()

    # 장면 전환이 max_frames 초과 시 균등 다운샘플
    if len(scene_ts) >= max_frames:
        indices = np.linspace(0, len(scene_ts) - 1, max_frames, dtype=int)
        return [scene_ts[i] for i in indices]

    # 부족분을 균등 분포로 보충
    n_fill = max_frames - len(scene_ts)
    fill_ts = np.linspace(0, duration, n_fill + 2, endpoint=True).tolist()[1:-1]

    scene_set = set(round(t, 3) for t in scene_ts)
    merged = list(scene_ts)
    for t in fill_ts:
        if round(t, 3) not in scene_set:
            merged.append(t)

    merged.sort()
    return merged[:max_frames]

def _build_filter_chain(stream, w: int, h: int, denoise: bool, normalize: bool):
    """ffmpeg 필터 체인 구성."""
    stream = stream.filter('scale', w, h)
    if denoise:
        stream = stream.filter('hqdn3d', luma_spatial=4)
    if normalize:
        # 대비 살짝 올리고 채도 유지
        stream = stream.filter('eq', contrast=1.2, brightness=0.02, saturation=1.1)
    return stream


def _extract_single_frame(
    video_path: str,
    timestamp: float,
    w: int,
    h: int,
    denoise: bool,
    normalize: bool,
) -> np.ndarray | None:
    """지정 타임스탬프의 단일 프레임을 RGB ndarray로 반환."""
    try:
        stream = ffmpeg.input(video_path, ss=timestamp)
        stream = _build_filter_chain(stream.video, w, h, denoise, normalize)
        out, _ = (
            stream
            .output('pipe:', vframes=1, format='rawvideo', pix_fmt='rgb24')
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        if not out:
            return None
        return np.frombuffer(out, np.uint8).reshape(h, w, 3)
    except ffmpeg.Error:
        return None


def _apply_filters_to_image(
    image_path: str,
    w: int,
    h: int,
    denoise: bool,
    normalize: bool,
) -> np.ndarray | None:
    """이미지 파일에 ffmpeg 필터 적용 후 RGB ndarray 반환."""
    try:
        stream = ffmpeg.input(image_path)
        stream = _build_filter_chain(stream.video, w, h, denoise, normalize)
        out, _ = (
            stream
            .output('pipe:', vframes=1, format='rawvideo', pix_fmt='rgb24')
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        if not out:
            return None
        return np.frombuffer(out, np.uint8).reshape(h, w, 3)
    except ffmpeg.Error:
        return None
