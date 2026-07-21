from django.shortcuts import render
import json
import os
from django.conf import settings


def index(request):
    """대시보드 메인 페이지"""
    return render(request, "dashboard/index.html")


def siting_map(request):
    """입지 지도 뷰 (W1)"""
    return render(request, "dashboard/map.html")


def schedule_view(request):
    """스케줄 뷰 (W2)"""
    return render(request, "dashboard/schedule.html")


def scenario_comparison(request):
    """시나리오 비교 뷰 (W4)"""
    return render(request, "dashboard/scenario.html")
