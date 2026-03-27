from flask import Blueprint, request, jsonify, current_app, send_file
import os

# AI 임베딩 함수 가져오기
from ..ai.embeddings import load_model, get_text_embedding

archive_bp = Blueprint('archive', __name__, url_prefix='/api/archive')

@archive_bp.route('/save', methods=['POST'])
def save_image():
    # TODO: 회원인지 검사하는 로직 포함 & 이미지 저장 처리
    return jsonify({"message": "이미지가 저장되었습니다."}), 201

@archive_bp.route('/tag/<frame_id>', methods=['PATCH'])
def update_tag(frame_id):
    data = request.json
    user_tags = data.get('user_tags', [])
    # TODO: 특정 이미지(frame_id)에 사용자가 입력한 태그(user_tags) 업데이트
    return jsonify({
        "message": "태그가 업데이트 되었습니다.",
        "frame_id": frame_id,
        "updated_tags": user_tags
    }), 200

@archive_bp.route('/list', methods=['GET'])
def get_archive_list():
    # TODO: 태그별, 날짜별 자동 분류된 이미지 리스트 DB 조회
    return jsonify({
        "items": [
            {"frame_id": "f_001", "image_path": "/images/f_001.jpg", "timestamp": 12.5, "refined_tags": ["person", "red_shirt"]}
        ]
    }), 200

@archive_bp.route('/search', methods=['GET'])
def search_archive():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "검색어가 필요합니다."}), 400

    try:
        # 모델 로드 및 사용자 검색어(query)를 임베딩 벡터로 변환
        model = load_model()
        query_vec = get_text_embedding(model, query)
        
        # TODO: DB 연결 후 저장된 이미지 임베딩과 cosine_similarity 비교 -> Top 5 추출
        
        return jsonify({
            "query":   query,
            "results": [],
            "message": "텍스트 임베딩 변환 성공 (DB 연결 후 구현 예정)",
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"검색 중 오류 발생: {str(e)}"}), 500

@archive_bp.route('/download/<frame_id>', methods=['GET'])
def download_image(frame_id):
    # 프론트에서 {job_id}_top{rank}.jpg 와 같이 파일명을 그대로 넘긴다고 가정
    result_folder = current_app.config['RESULT_FOLDER']
    file_path = os.path.join(result_folder, frame_id)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "파일을 찾을 수 없습니다."}), 404
        
    # 브라우저가 이미지를 띄우지 않고 바로 다운로드하도록 설정
    return send_file(
        file_path, 
        mimetype='image/jpeg', 
        as_attachment=True, 
        download_name=frame_id
    )