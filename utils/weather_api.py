"""기상 데이터 API — wttr.in 기반 (API 키 불필요)"""

import requests


CITY_CODES = {
    "서울": "Seoul",
    "부산": "Busan",
    "대구": "Daegu",
    "인천": "Incheon",
    "광주": "Gwangju",
    "대전": "Daejeon",
    "울산": "Ulsan",
    "제주": "Jeju",
    "수원": "Suwon",
    "창원": "Changwon",
}


def get_weather(city: str = "서울") -> dict:
    """
    wttr.in JSON API로 현재 날씨 + 자외선 지수 조회
    실패 시 기본값 반환
    """
    city_en = CITY_CODES.get(city, city)
    try:
        url = f"https://wttr.in/{city_en}?format=j1"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            current = data["current_condition"][0]
            return {
                "city": city,
                "temp_c": int(current.get("temp_C", 22)),
                "humidity": int(current.get("humidity", 55)),
                "uv_index": int(current.get("uvIndex", 3)),
                "weather_desc": (current.get("weatherDesc") or [{}])[0].get("value", "맑음"),
                "feels_like_c": int(current.get("FeelsLikeC", 22)),
                "source": "wttr.in",
            }
    except Exception:
        pass

    # 기본값 (서울 5월 평균)
    return {
        "city": city,
        "temp_c": 21,
        "humidity": 58,
        "uv_index": 5,
        "weather_desc": "구름 조금",
        "feels_like_c": 20,
        "source": "기본값",
    }


def get_skin_risk_from_weather(weather: dict, drug_name: str = "") -> dict:
    """기상 데이터 → 피부 독성 위험 보정값 산출"""
    uv = weather.get("uv_index", 3)
    humidity = weather.get("humidity", 55)
    temp = weather.get("temp_c", 20)

    risk_factors = []
    risk_score = 0

    # 자외선 위험
    if uv >= 8:
        risk_score += 30
        risk_factors.append(f"🔴 자외선 지수 {uv} (매우 높음) — 외출 자제, SPF50+ 필수")
    elif uv >= 5:
        risk_score += 15
        risk_factors.append(f"🟠 자외선 지수 {uv} (높음) — 외출 시 SPF50+ 필수")
    elif uv >= 3:
        risk_score += 5
        risk_factors.append(f"🟡 자외선 지수 {uv} (보통) — 외출 시 SPF30+ 권장")

    # 습도 위험 (건조할수록 피부 독성 악화)
    if humidity < 35:
        risk_score += 25
        risk_factors.append(f"🔴 습도 {humidity}% (매우 건조) — 가습기 사용, 보습제 3회 이상")
    elif humidity < 50:
        risk_score += 12
        risk_factors.append(f"🟠 습도 {humidity}% (건조) — 보습제 2회 도포")

    # 고온 위험
    if temp >= 30:
        risk_score += 10
        risk_factors.append(f"🟡 기온 {temp}°C (고온) — 야외 활동 최소화")

    # EGFR 계열 특별 경고
    if "Erlotinib" in drug_name or "Cetuximab" in drug_name:
        if uv >= 3:
            risk_score += 10
            risk_factors.append("⚠️ EGFR 억제제 복용 중 — 광과민성 반응 위험, 자외선 차단 필수")

    if risk_score >= 40:
        level = "높음"
        level_color = "#cc0000"
    elif risk_score >= 20:
        level = "주의"
        level_color = "#ff6600"
    elif risk_score >= 5:
        level = "보통"
        level_color = "#ffaa00"
    else:
        level = "낮음"
        level_color = "#0088cc"

    return {
        "risk_score": min(risk_score, 100),
        "risk_level": level,
        "risk_color": level_color,
        "risk_factors": risk_factors,
        "recommendation": _get_recommendation(risk_score, humidity, uv),
    }


def _get_recommendation(risk_score: int, humidity: int, uv: int) -> str:
    if risk_score >= 40:
        return "오늘은 외출을 가급적 자제하세요. 외출이 불가피하다면 SPF50+ 자외선 차단제 + 긴 소매 착용 필수."
    elif risk_score >= 20:
        return "외출 전 SPF50+ 선크림 도포. 2시간마다 덧바르기. 보습제 추가 도포 권장."
    elif humidity < 50:
        return "건조한 날씨 — 보습제를 오늘은 한 번 더 발라주세요."
    else:
        return "오늘은 피부 관리 조건이 양호합니다. 정기 보습·자외선 차단 루틴 유지."
