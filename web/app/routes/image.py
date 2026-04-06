from flask import Blueprint, request, jsonify, current_app, send_file
import os

# '/api/image'로 시작하는 요청을 처리
image_bp = Blueprint('image', __name__, url_prefix='/api/image')

# 이미지 목록 조회 API (/api/image)
# URL 끝에 파라미터로 id를 받음 (예: /api/image?id=hong123)
@image_bp.route('', methods=['GET'])
def get_images():
    # 주소창(쿼리 스트링)에 포함된 id 값을 가져옴
    user_id = request.args.get('id')
    
    if not user_id:
        return jsonify({"result": "fail", "msg": "id 파라미터가 필요합니다."}), 400

    # [DB 및 AI 팀 완성 시 연동 대비]
    # 현재는 AI 팀이 추출한 이미지를 하드디스크에만 저장하고 DB 테이블(images)에 넣지 않음
    # 추후 이 부분이 완성되면, 여기서 빈 리스트([]) 대신 DB에서 SELECT 해온 데이터를 넘겨주도록 코드를 수정
    return jsonify({
        "result": "success",
        "msg": "이미지 목록 조회 성공",
        "data": [] 
    }), 200


# 이미지 저장(다운로드) API (/api/image/download/<image_uuid>)
@image_bp.route('/download/<image_uuid>', methods=['GET'])
def download_image(image_uuid):
    # 결과 이미지들이 저장되어 있는 폴더 경로를 가져옴
    result_folder = current_app.config['RESULT_FOLDER']
    
    # [AI 팀 수정 대비]
    # AI 팀이 파이프라인에서 저장하는 이미지 확장자(.jpg -> .png)나,
    # 파일 이름 생성 규칙을 바꾼다면 아래 f"{image_uuid}.jpg" 부분을 똑같이 맞춰줘야 프론트가 다운로드할 수 있음
    # 폴더 경로와 파일 이름을 합쳐서 실제 파일의 위치를 찾음
    # AI 파이프라인에서 추출된 이미지가 보통 .jpg로 저장된다고 가정
    file_path = os.path.join(result_folder, f"{image_uuid}.jpg")
    
    # 서버에 파일이 실제로 존재하는지 검사
    if not os.path.exists(file_path):
        return jsonify({"result": "fail", "msg": "파일을 찾을 수 없습니다."}), 404
        
    # send_file 함수를 사용해 파일을 브라우저로 전송
    # as_attachment=True 로 설정하면 웹 브라우저가 이미지를 새 창에서 열지 않고 '파일 다운로드'를 수행
    return send_file(
        file_path, 
        mimetype='image/jpeg', 
        as_attachment=True, 
        download_name=f"{image_uuid}.jpg" # 다운로드될 때 저장되는 파일 이름 설정
    )