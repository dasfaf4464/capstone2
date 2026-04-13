"""
[ video 라우터 ]
영상 업로드 / 분석 요청 / 상태 조회 API 담당함
AI 파이프라인은 ai/pipeline.py 에서 백그라운드 스레드로 돌아감

- POST /api/video/upload          → 영상 업로드
- GET  /api/video/status/<uuid>   → 분석 진행 상태 조회
- POST /api/video/request         → AI 분석 요청
"""

from flask import Blueprint, request, jsonify, current_app, session
import os
import uuid
from werkzeug.utils import secure_filename
from ..storage.alchemy_models.temp_video import save_temp_video
from ..ai.pipeline import register_job, run_job, get_job

video_bp = Blueprint('video', __name__, url_prefix='/api/video')


@video_bp.route('/upload', methods=['POST'])
def upload_video():
    # 로그인 확인
    if 'user_uuid' not in session:
        return jsonify({"result": "fail", "msg": "로그인이 필요한 서비스입니다."}), 401

    # form-data 에서 video_file 키로 파일 꺼냄
    video_file = request.files.get('video_file')
    if not video_file or video_file.filename == '':
        return jsonify({"result": "fail", "msg": "영상 파일이 없습니다."}), 400

    # 파일명 보안 처리 후 uuid 기반으로 새 파일명 생성 (충돌 방지)
    ext = os.path.splitext(secure_filename(video_file.filename))[1]
    video_uuid = str(uuid.uuid4())
    filename = f"{video_uuid}{ext}"

    # TEMP_FOLDER 에 저장 (분석 완료 전 임시 보관용)
    upload_folder = current_app.config.get('TEMP_FOLDER', current_app.config['UPLOAD_FOLDER'])
    video_path = os.path.join(upload_folder, filename)
    video_file.save(video_path)

    try:
        user_uuid = session.get('user_uuid')

        # DB에 임시 영상 기록 저장
        save_temp_video(video_path=video_path, user_uuid=user_uuid)

        # 분석 job 등록 (메모리에 올려둠 → 이후 request API 에서 찾아씀)
        register_job(video_uuid, video_path)

        return jsonify({
            "result": "success",
            "msg": "업로드 완료",
            "video_data": {
                "video_uuid": video_uuid,
                "video_name": filename
            }
        }), 202

    except Exception as e:
        return jsonify({"result": "fail", "msg": "DB 저장 실패", "details": str(e)}), 500


@video_bp.route('/status/<video_uuid>', methods=['GET'])
def get_status(video_uuid):
    # 메모리에서 job 상태 조회
    # status 값 의미: 0=대기, 1=전처리중, 2=AI분석중, 3=완료, -1=오류
    job = get_job(video_uuid)
    if not job:
        return jsonify({"result": "fail", "msg": "존재하지 않는 video_uuid입니다."}), 404

    return jsonify({
        "result":   "success",
        "video_uuid": video_uuid,
        "status":   job['status'],
        "message":  job['message'],
        "progress": job['progress'],  # 현재까지 처리된 프레임 수
        "total":    job['total'],     # 전체 프레임 수
        "results":  job.get('results', []),  # 분석 완료 시 top5 프레임 목록
    }), 200


@video_bp.route('/request', methods=['POST'])
def request_analysis():
    # 로그인 확인
    if 'user_uuid' not in session:
        return jsonify({"result": "fail", "msg": "로그인이 필요한 서비스입니다."}), 401

    # 요청 body 에서 video_uuid, query 꺼냄
    data = request.json or {}
    video_uuid = data.get('video_uuid')
    query_text = data.get('query', '자동 분석')

    if not video_uuid:
        return jsonify({"result": "fail", "msg": "video_uuid가 필요합니다."}), 400

    result_folder = current_app.config['RESULT_FOLDER']

    try:
        # 백그라운드 스레드로 AI 분석 파이프라인 실행
        # 분석 결과는 /status/<video_uuid> 로 폴링해서 확인해야 함
        run_job(
            job_id=video_uuid,
            query=query_text,
            max_frames=50,
            result_folder=result_folder
        )

        return jsonify({
            "result": "success",
            "msg": "AI 영상 분석 요청 완료",
            "request_data": {
                "video_uuid": video_uuid,
                "query": query_text
            }
        }), 202

    except Exception as e:
        return jsonify({"result": "fail", "msg": "분석 요청 실패", "details": str(e)}), 500
