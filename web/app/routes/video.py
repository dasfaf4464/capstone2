from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename

# AI 파이프라인 함수 불러오기
from ..ai.pipeline import register_job, run_job, get_job

video_bp    = Blueprint('video',    __name__, url_prefix='/api/video')
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@video_bp.route('/upload', methods=['POST'])
def upload_video():
    video_file = request.files.get('video')
    
    # 예외 처리: 파일이 아예 없거나, 이름이 비어있는 경우 차단
    if not video_file or video_file.filename == '':
        return jsonify({"error": "영상 파일이 없습니다."}), 400

    # secure_filename 적용
    ext      = os.path.splitext(secure_filename(video_file.filename))[1]
    video_id = str(uuid.uuid4())
    filename = f"{video_id}{ext}"

    upload_folder = current_app.config['UPLOAD_FOLDER']
    video_path = os.path.join(upload_folder, filename)
    video_file.save(video_path)

    register_job(video_id, video_path)

    return jsonify({
        "message":  "업로드 완료",
        "video_id": video_id,
        "status":   0,  # 0: 대기
    }), 202


@video_bp.route('/status/<video_id>', methods=['GET'])
def get_video_status(video_id):
    job = get_job(video_id)
    if not job:
        return jsonify({"error": "존재하지 않는 video_id입니다."}), 404

    return jsonify({
        "video_id":      video_id,
        "status":        job['status'],
        "message":       job['message'],
        "progress":      job['progress'],
        "total":         job['total'],
        "thumbnail_url": job.get('thumbnail_url'),
        "results":       job.get('results', []),
    }), 200

@analysis_bp.route('/request', methods=['POST'])
def request_analysis():
    data       = request.json or {}
    video_id   = data.get('video_id')
    query      = data.get('query', '').strip()
    max_frames = int(data.get('max_frames', 50))

    if not video_id or not query:
        return jsonify({"error": "video_id와 query가 필요합니다."}), 400

    job = get_job(video_id)
    if not job:
        return jsonify({"error": "존재하지 않는 video_id입니다."}), 404

    result_folder = current_app.config['RESULT_FOLDER']

    run_job(
        job_id=video_id,
        query=query,
        max_frames=max_frames,
        result_folder=result_folder,
    )

    return jsonify({
        "message":  "AI 분석 파이프라인 가동 시작",
        "video_id": video_id,
        "query":    query,
        "status":   2,  # 2: AI 분석 중
    }), 202
