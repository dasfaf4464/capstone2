"""
[ photo_analysis.py ]
Gemini를 이용한 사진 AI 분석 모듈

- analyze_photo()  : 사진 1장 분석 → main_category, sub_categories, has_person, activity 반환
- generate_stats() : 유저 통계 기반 LLM 추천 글 생성 → personality_type, recommendation 반환
- run_photo_job()  : 백그라운드 스레드로 사진 분석 + 통계 갱신 실행
"""

import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import google.generativeai as genai

# Gemini 초기화
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
_model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-3-flash-preview'))

# 동시 실행 최대 5개 제한 (Gemini Rate Limit + 서버 과부하 방지)
_executor  = ThreadPoolExecutor(max_workers=5)

# 백그라운드 job 상태 저장 (메모리)
# { photo_uuid: { status: pending/done/fail, result: {...} } }
_photo_jobs = {}
_jobs_lock  = threading.Lock()


# ─────────────────────────────────────────────
# 사진 분석
# ─────────────────────────────────────────────

def analyze_photo(photo_path: str) -> dict:
    # 사진 1장을 Gemini VLM에 전달해 main_category·sub_categories·has_person·activity 추출
    """
    사진 1장을 Gemini에 전달해서 분석 결과 반환
    반환: { main_category, sub_categories, has_person, activity }
    """
    prompt = """
이 사진을 분석해서 아래 JSON 형식으로만 답해줘. 다른 텍스트는 절대 포함하지 마.

{
  "main_category": "풍경/장소 또는 음식 또는 기록",
  "sub_categories": ["키워드1", "키워드2", "키워드3"],
  "has_person": true 또는 false,
  "activity": "활동명 또는 null"
}

규칙:
- main_category는 반드시 '풍경/장소', '음식', '기록' 중 하나
  · 풍경/장소: 공간, 배경이 주인공인 사진 (산, 바다, 도시, 실내, 호텔, 공항 등)
  · 음식: 음식, 음료가 주인공인 사진
  · 기록: 물건, 사물이 주인공인 사진 (동상, 전시품, 쇼핑상품, 기념품 등)

- sub_categories는 3~5개의 키워드 배열
  · 풍경/장소 예시: 산, 바다, 도시, 골목, 식당외부, 랜드마크, 비행기, 공항, 호텔, 실내, 야경
  · 음식 예시: 라멘, 스시, 아이스크림, 디저트, 카페, 길거리음식
  · 기록 예시: 동상, 전시품, 쇼핑상품, 기념품, 간판

- has_person: 사람이 사진의 주요 피사체인 경우에만 true
  · true 조건: 셀카, 인물 사진, 사람이 화면의 30% 이상을 차지하는 경우, 사람이 명확히 사진의 주인공인 경우
  · false 조건: 사람이 배경에 작게 찍힌 경우, 군중 속 지나가는 행인, 멀리서 점처럼 보이는 경우, 풍경 사진에 사람이 일부 포함된 경우

- activity: has_person이 true이고 사람이 특정 활동 중이면 활동명 (예: "하이킹", "수상스포츠", "사이클링"), 없으면 null
"""
    try:
        image = Image.open(photo_path)
        response = _model.generate_content([prompt, image])
        text = response.text.strip()

        # JSON 파싱
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        result = json.loads(text.strip())

        # 필드 검증
        valid_categories = ['풍경/장소', '음식', '기록']
        if result.get('main_category') not in valid_categories:
            result['main_category'] = '기록'

        if not isinstance(result.get('sub_categories'), list):
            result['sub_categories'] = []

        result['has_person'] = bool(result.get('has_person', False))

        # activity 비표준 문자열 정규화 ("없음", "-", "null", "" 등 → None)
        act = result.get('activity')
        if not act or str(act).strip().lower() in ('null', 'none', '없음', '해당없음', '-', 'n/a', 'na'):
            result['activity'] = None

        return result

    except Exception as e:
        print(f"[photo_analysis] 분석 실패: {e}")
        return {
            'main_category': None,
            'sub_categories': [],
            'has_person': False,
            'activity': None,
        }


# ─────────────────────────────────────────────
# LLM 추천 글 생성
# ─────────────────────────────────────────────

def generate_recommendation(category_stats: dict, keyword_stats: list) -> dict:
    # 유저 통계를 Gemini LLM에 주입해 성향 문구(personality_type) + 여행지 추천(recommendation) 생성
    # keyword_stats에는 sub_categories + 인물포함 + 활동명이 통합 집계되어 있음
    """
    유저 통계 기반으로 성향 문구 + 추천 글 생성
    반환: { personality_type, recommendation }
    """
    # 상위 7개 (인물포함·활동 태그도 포함된 통합 순위)
    top_keywords = [f"{item['keyword']}({item['count']}장)" for item in keyword_stats[:7]]

    prompt = f"""
아래는 유저의 여행 사진 통계야.

주카테고리 비율: {json.dumps(category_stats, ensure_ascii=False)}
상위 태그 (빈도순, 인물·활동 포함): {top_keywords}

이 데이터를 기반으로 아래 JSON 형식으로만 답해줘. 다른 텍스트는 절대 포함하지 마.

{{
  "personality_type": "당신은 ~한 여행자입니다 (20자 이내)",
  "recommendation": "다음 여행지 추천 + 이유 (3~4줄, 자연스러운 한국어)"
}}

규칙:
- personality_type은 '당신은 '으로 시작하는 20자 이내 문장
- recommendation은 구체적인 여행지 1~2곳 추천 + 이유를 3~4줄로 작성
- 통계에서 가장 많은 카테고리와 태그를 반영해서 작성
- 상위 태그에 '인물포함'이 있으면 인물 사진 찍기 좋은 명소·셀카 스팟을 추천에 포함할 것
- 상위 태그에 활동명(하이킹, 수상스포츠 등)이 있으면 해당 활동을 즐길 수 있는 여행지를 추천에 포함할 것
"""
    try:
        response = _model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        result = json.loads(text.strip())
        return result

    except Exception as e:
        print(f"[photo_analysis] 추천 생성 실패: {e}")
        return {
            'personality_type': '당신은 여행을 사랑하는 탐험가입니다',
            'recommendation': '사진이 쌓일수록 더 정확한 추천을 드릴 수 있어요. 더 많은 여행 사진을 업로드해보세요!'
        }


# ─────────────────────────────────────────────
# 백그라운드 사진 분석 job
# ─────────────────────────────────────────────

def run_photo_job(photo_uuid: str, photo_path: str, user_uuid: str, travel_uuid: str, app):
    # 백그라운드 Thread로 사진 분석 실행 (업로드 요청은 즉시 202 반환, 분석은 별도로 진행)
    with _jobs_lock:
        _photo_jobs[photo_uuid] = {'status': 'pending'}

    def _execute():
        with app.app_context():
            try:
                from ..storage.alchemy_models.photos import update_analysis_result, update_analysis_fail, get_category_stats, get_keyword_stats
                from ..storage.alchemy_models.user_stats import upsert_user_stats
                from ..storage.alchemy_models.travels import update_cover_photo

                # AI 분석
                result = analyze_photo(photo_path)

                # main_category가 None이면 분석 실패로 처리
                if result.get('main_category') is None:
                    raise ValueError('main_category가 None — AI 분석 결과 불완전')

                # DB 저장
                update_analysis_result(
                    photo_uuid=photo_uuid,
                    main_category=result['main_category'],
                    sub_categories=result['sub_categories'],
                    has_person=result['has_person'],
                    activity=result['activity'],
                )

                # 대표 썸네일 설정 (첫 번째 사진)
                update_cover_photo(travel_uuid, photo_path)

                # job 상태 갱신
                with _jobs_lock:
                    _photo_jobs[photo_uuid] = {'status': 'done', 'result': result}

                # 유저 통계 갱신
                _refresh_user_stats(user_uuid)

            except Exception as e:
                print(f"[photo_analysis] job 실패: {e}")
                # app_context는 이미 활성화돼 있으므로 중첩 금지
                from ..storage.alchemy_models.photos import update_analysis_fail
                update_analysis_fail(photo_uuid)
                with _jobs_lock:
                    _photo_jobs[photo_uuid] = {'status': 'fail'}

    _executor.submit(_execute)


def _refresh_user_stats(user_uuid: str):
    # 분석 완료 후 전체 통계 재집계 → LLM 추천 재생성 → user_stats upsert
    """유저 통계 + LLM 추천 갱신"""
    try:
        from ..storage.alchemy_models.photos import get_category_stats, get_keyword_stats
        from ..storage.alchemy_models.user_stats import upsert_user_stats

        category_stats = get_category_stats(user_uuid)
        # keyword_stats는 sub_categories + 인물포함 + 활동명 통합 집계
        keyword_stats  = get_keyword_stats(user_uuid, limit=10)

        if not category_stats:
            # 사진이 하나도 없으면 통계를 NULL로 초기화
            from ..storage.alchemy_models.user_stats import clear_user_stats
            clear_user_stats(user_uuid)
            return

        # LLM 추천 생성
        llm_result = generate_recommendation(category_stats, keyword_stats)

        upsert_user_stats(
            user_uuid=user_uuid,
            category_stats=category_stats,
            keyword_stats=keyword_stats,
            personality_type=llm_result.get('personality_type'),
            recommendation=llm_result.get('recommendation'),
        )
    except Exception as e:
        print(f"[photo_analysis] 통계 갱신 실패: {e}")


def get_photo_job_status(photo_uuid: str) -> dict:
    # 메모리(_photo_jobs dict)에서 현재 분석 job 상태 반환 (pending/done/fail/not_found)
    """job 상태 조회"""
    with _jobs_lock:
        return _photo_jobs.get(photo_uuid, {'status': 'not_found'})
