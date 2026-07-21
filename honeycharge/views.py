from django.shortcuts import render


def home(request):
    """꿀차지 홈 - 최적 참여시간 + 예상 수익 (M1)"""
    return render(request, "honeycharge/home.html")


def earnings(request):
    """수익 대시보드 (M2) - 누적 방전량, 정산액, 배터리 기여도"""
    return render(request, "honeycharge/earnings.html")


def wallet(request):
    """꿀 지갑 (M3) - 쿠폰, 주차권, 가맹점 지도"""
    return render(request, "honeycharge/wallet.html")
