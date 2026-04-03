"""
Gemini Vision 기반 사진 대분류 분류기 (테스트용)
- DB 저장 없이 분류 결과 JSON 반환
"""

import json
import os

import cv2
import numpy as np
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _bgr_to_pil(bgr: np.ndarray) -> Image.Image:
    """OpenCV BGR 배열 → PIL RGB 이미지."""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def _build_prompt(categories: list[str]) -> str:
    cats = ", ".join(categories)
    return f"""아래 이미지들을 각각 주어진 대분류 중 하나로 분류하고, 각 이미지에 대한 간단한 설명을 한국어로 작성해.

대분류 목록: [{cats}]

반드시 아래 JSON 배열 형식으로만 응답해. 코드블록이나 다른 텍스트는 포함하지 마.
[
  {{
    "filename": "이미지 파일명 또는 순서 (image_1, image_2, ...)",
    "category": "해당 대분류",
    "description": "사진에 대한 간단한 설명"
  }}
]"""


def classify_images(
    images: list[tuple[str, np.ndarray]],
    categories: list[str],
    api_key: str | None = None,
) -> list[dict]:
    """
    이미지 목록을 대분류 목록으로 분류.

    Parameters
    ----------
    images     : (파일명, BGR ndarray) 튜플 리스트
    categories : 대분류 목록  e.g. ["스포츠", "풍경", "음식"]
    api_key    : Gemini API 키 (None이면 환경변수 GEMINI_API_KEY 사용)

    Returns
    -------
    [{"filename": ..., "category": ..., "description": ...}, ...]
    """
    from google import genai

    key = api_key or GEMINI_API_KEY
    if not key:
        raise RuntimeError(".env에 GEMINI_API_KEY가 설정되지 않았습니다.")
    if not GEMINI_MODEL:
        raise RuntimeError(".env에 GEMINI_MODEL이 설정되지 않았습니다.")

    client = genai.Client(api_key=key)

    # 프롬프트 + 이미지 파트 구성
    # 파일명을 이미지 앞에 텍스트로 삽입해 LLM이 매핑 가능하게 함
    parts: list = [_build_prompt(categories)]
    for filename, bgr in images:
        parts.append(f"\n[{filename}]")
        parts.append(_bgr_to_pil(bgr))

    response = client.models.generate_content(model=GEMINI_MODEL, contents=parts)
    raw = response.text.strip()

    # 혹시 코드블록으로 감싸진 경우 제거
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        )

    return json.loads(raw)
