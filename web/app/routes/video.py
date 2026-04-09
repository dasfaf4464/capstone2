from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy import text
from ..storage.core.pg import pg_alchemy as db
from ..ai.pipeline import register_job, run_job # AI 파이프라인 함수들

# '/api/video'로 시작하는 요청을 처리
video_bp = Blueprint('video', __name__, url_prefix='/api/video')

# 영상 업로드 API (/api/video/upload)
@video_bp.route('/upload', methods=['POST'])
def upload_video():
    # 프론트엔드에서 보낸 폼 데이터 중 'video_file'이라는 이름의 파일을 가져옴
    video_file = request.files.get('video_file')
    
    # 파일이 정상적으로 올라오지 않았다면 에러를 반환
    if not video_file or video_file.filename == '':
        return jsonify({"result": "fail", "msg": "영상 파일이 없습니다."}), 400

    # 해킹 방지를 위해 파일명을 안전하게 바꾸고(secure_filename), 확장자(.mp4 등)만 분리
    ext = os.path.splitext(secure_filename(video_file.filename))[1]
    
    # 영상마다 절대 안 겹치는 고유한 랜덤 ID(uuid)를 만듦
    video_uuid = str(uuid.uuid4())
    
    # 저장할 파일 이름을 "랜덤ID.확장자" 형태로 만듦
    filename = f"{video_uuid}{ext}"

    # 환경 설정(__init__.py)에 정의된 업로드 폴더 경로를 가져옴
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # 실제 파일이 저장될 전체 경로를 조합 (예: /media/uploads/1234-abcd.mp4)
    video_path = os.path.join(upload_folder, filename)
    
    # 서버의 물리적인 하드디스크(도커 볼륨)에 파일을 저장
    video_file.save(video_path)

    try:
        # 업로드된 영상 정보를 DB의 temp_video 테이블에 기록
        query = text("""
            INSERT INTO temp_video (video_uuid, video_file_name) 
            VALUES (:video_uuid, :video_file_name)
        """)
        db.session.execute(query, {"video_uuid": video_uuid, "video_file_name": filename})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"result": "fail", "msg": "DB 저장 실패", "details": str(e)}), 500

    # 백그라운드에서 AI 분석을 대기시키기 위해 파이프라인에 작업을 등록
    register_job(video_uuid, video_path)

    # 처리가 다 끝났으면 성공 메시지와 영상 ID를 반환
    return jsonify({"result": "success", "msg": "업로드 완료", "video_uuid": video_uuid}), 202


# 영상처리(AI 분석) 요청 API (/api/video/request)
@video_bp.route('/request', methods=['POST'])
def request_analysis():
    # 업로드 시 발급받았던 video_uuid를 프론트에서 보내주면 그걸 받음
    data = request.json or {}
    video_uuid = data.get('video_uuid')

    # [프론트엔드 팀 수정 대비] 
    # 나중에 프론트에서 검색어(예: "빨간 모자 쓴 사람")를 입력받아 보내주기로 했다면 주석 해제
    # query_text = data.get('query')

    if not video_uuid:
        return jsonify({"result": "fail", "msg": "video_uuid가 필요합니다."}), 400

    # 분석 결과(이미지들)가 저장될 경로를 가져옴
    result_folder = current_app.config['RESULT_FOLDER']

        # [AI 팀 수정 대비]
        # 1. AI 팀이 pipeline.py의 run_job() 파라미터 개수나 종류를 바꿨다면 여기를 똑같이 맞춰줘야 에러가 안 남
        # 2. 현재는 API 명세서에 검색어(query) 파라미터가 없어서 "자동 분석"을 강제로 넣어 에러를 방지
        #    프론트에서 검색어를 받게 되면 "자동 분석"을 지우고 query_text 변수로 교체
    try:
        # ai/pipeline.py 에 있는 실제 영상 분석 동작(run_job)을 실행
        run_job(
            job_id=video_uuid,
            query="자동 분석", # 추후 프론트에서 검색어를 받게 되면 이 부분을 변수로 바꾸면 됨
            max_frames=50,   # 최대 몇 프레임을 추출할지 결정
            result_folder=result_folder,
        )
        return jsonify({"result": "success", "msg": "AI 영상 분석 요청 완료"}), 202
    except Exception as e:
        return jsonify({"result": "fail", "msg": "분석 요청 실패", "details": str(e)}), 500