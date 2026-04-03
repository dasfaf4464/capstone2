"""
분류 테스트 라우트 (DB 저장 없음)

엔드포인트
----------
POST /api/classify/images
    - 이미지 파일 여러 장 + 대분류 목록 → Gemini 분류 결과 JSON 반환
"""

import json

import numpy as np
import cv2
from flask import Blueprint, jsonify, render_template, request

from ..ai.gemini_classifier import classify_images

classify_bp = Blueprint("classify", __name__, url_prefix="/api/classify")


@classify_bp.route("/test", methods=["GET"])
def classify_test_ui():
    return render_template("classify_test.html")


@classify_bp.route("/images", methods=["POST"])
def classify_uploaded_images():
    """
    직접 업로드한 이미지 파일들을 대분류로 분류.

    multipart/form-data
      - images      : 이미지 파일 (여러 장, key="images")
      - categories  : JSON 배열 문자열  e.g. '["스포츠","풍경","음식"]'
    """
    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "이미지 파일이 없습니다. key='images'로 전송하세요."}), 400

    raw_cats = request.form.get("categories", "")
    try:
        categories = json.loads(raw_cats)
        if not isinstance(categories, list) or not categories:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "categories는 JSON 배열 문자열이어야 합니다. e.g. '[\"스포츠\",\"풍경\"]'"}), 400

    images: list[tuple[str, np.ndarray]] = []
    for f in files:
        file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
        bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if bgr is None:
            return jsonify({"error": f"이미지 디코딩 실패: {f.filename}"}), 400
        images.append((f.filename, bgr))

    try:
        results = classify_images(images, categories)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "categories": categories,
        "count":      len(results),
        "results":    results,
    }), 200

