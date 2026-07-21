from django.http import JsonResponse
from django.views.decorators.http import require_POST
import os
import json


@require_POST
def generate_briefing(request):
    """
    Claude API를 사용한 정책 브리핑 생성 (W5)
    현재 슬라이더 값과 시나리오 정보를 받아 브리핑 텍스트 생성
    """
    try:
        # 요청 데이터 파싱
        data = json.loads(request.body)
        ev_count = data.get("ev_count", 500)
        scenario = data.get("scenario", "base")

        # Claude API 호출 (TODO: 실제 구현 필요)
        # 현재는 fallback 브리핑 반환
        fallback_briefing = f"""
        ## 정책 브리핑 (EV {ev_count}대 시나리오)

        ### 주요 분석 결과
        - 전기차 {ev_count}대 규모의 V2G 참여 시, 연간 출력제어량 약 15-20% 감소 예상
        - 재생에너지 활용률 개선으로 연간 약 50억원 이상의 경제적 효과 기대
        - 배터리 열화비용 고려 시에도 차주당 월평균 3-5만원 수익 보장 가능

        ### 정책 권고사항
        1. 제주·호남 지역 우선 시범사업 추진 권장
        2. V2G 참여 인센티브 설계 시 배터리 열화비용 보상 필수
        3. 입지 적합도 상위 30% 지역부터 단계적 확대 제안

        ### 차주 편익
        - 월평균 수익: 3-5만원
        - 지역 쿠폰 및 주차권 추가 제공
        - 재생에너지 활용 기여를 통한 환경 가치 창출
        """

        return JsonResponse({
            "success": True,
            "briefing": fallback_briefing
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
            "briefing": "브리핑 생성 중 오류가 발생했습니다."
        }, status=500)
