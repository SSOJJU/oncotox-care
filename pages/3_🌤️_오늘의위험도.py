"""오늘의 피부 위험도 — 기상청 자외선·습도 → 맞춤 알림"""

import sys, os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.graph_objects as go

from utils.weather_api import get_weather, get_skin_risk_from_weather, CITY_CODES
from utils.drug_database import get_drug_list

st.set_page_config(page_title="오늘의 위험도 — Onco-Tox Care", page_icon="🌤️", layout="wide")

with st.sidebar:
    st.markdown("## 🏥 Onco-Tox Care")
    st.caption("항암 부작용 케어 AI SaaS")
    st.divider()
    st.caption("날씨 데이터: wttr.in (오픈 API)")

st.title("🌤️ 오늘의 피부 위험도")
st.caption("현재 날씨(자외선·습도·기온)와 복용 항암제를 결합해 오늘의 피부 독성 위험을 예측합니다.")

col_set, col_result = st.columns([1, 1])

with col_set:
    city = st.selectbox("거주/현재 위치", list(CITY_CODES.keys()), index=0)
    drug = st.selectbox("복용 중인 항암제", ["선택 안 함"] + get_drug_list())

    if st.button("🌡️ 날씨 정보 불러오기", type="primary", use_container_width=True):
        with st.spinner("기상 데이터 조회 중..."):
            weather = get_weather(city)
            risk = get_skin_risk_from_weather(weather, drug)
            st.session_state["weather"] = weather
            st.session_state["risk"] = risk
            st.session_state["weather_loaded"] = True

    # 최초 1회만 자동 로딩 (버튼 클릭 이후에는 session_state 값 유지)
    if "weather_loaded" not in st.session_state:
        with st.spinner("초기 기상 데이터 로딩..."):
            weather = get_weather(city)
            risk = get_skin_risk_from_weather(weather, drug)
            st.session_state["weather"] = weather
            st.session_state["risk"] = risk
            st.session_state["weather_loaded"] = True

    if "weather" in st.session_state:
        w = st.session_state["weather"]
        st.markdown(f"""
        <div style="background:#f0f8ff;border-radius:10px;padding:1.2rem;margin-top:1rem">
        <b>📍 {w['city']} 현재 날씨</b><br><br>
        <table style="width:100%;font-size:0.95rem">
        <tr><td>🌡️ 기온</td><td><b>{w['temp_c']}°C</b> (체감 {w['feels_like_c']}°C)</td></tr>
        <tr><td>💧 습도</td><td><b>{w['humidity']}%</b></td></tr>
        <tr><td>☀️ 자외선 지수</td><td><b>{w['uv_index']}</b></td></tr>
        <tr><td>🌤️ 날씨</td><td>{w['weather_desc']}</td></tr>
        </table>
        <small style="color:#888">출처: {w['source']}</small>
        </div>
        """, unsafe_allow_html=True)

with col_result:
    if "risk" in st.session_state:
        risk = st.session_state["risk"]
        color = risk["risk_color"]

        st.markdown(f"""
        <div style="background:{color}15;border:3px solid {color};border-radius:12px;
                    padding:1.5rem;text-align:center;margin-bottom:1rem">
        <div style="font-size:1rem;color:#555">오늘의 피부 독성 환경 위험도</div>
        <div style="font-size:2.5rem;font-weight:800;color:{color};margin:0.3rem 0">
        {risk['risk_level']}
        </div>
        <div style="font-size:0.9rem;color:#666">{risk['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 위험 점수 게이지
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk["risk_score"],
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 20], "color": "#e8f5e9"},
                    {"range": [20, 40], "color": "#fff8e1"},
                    {"range": [40, 65], "color": "#fff3e0"},
                    {"range": [65, 100], "color": "#ffebee"},
                ],
            },
            title={"text": "환경 위험 점수", "font": {"size": 14}},
        ))
        fig.update_layout(height=220, margin=dict(l=20, r=20, t=50, b=10),
                           paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        if risk["risk_factors"]:
            st.markdown("**📋 위험 요인별 상세:**")
            for factor in risk["risk_factors"]:
                st.markdown(f"- {factor}")
    else:
        st.info("왼쪽에서 위치와 항암제를 선택 후 '날씨 정보 불러오기'를 클릭하세요.")

# ── 주간 예측 (데모)
st.divider()
st.subheader("📅 이번 주 피부 위험 예보 (데모)")

import pandas as pd
import datetime

days = ["오늘", "내일", "모레", "3일 후", "4일 후", "5일 후", "6일 후"]
uv_vals = [5, 7, 8, 4, 3, 6, 9]
humid_vals = [58, 50, 42, 65, 72, 55, 40]
risk_scores = [15, 25, 38, 10, 8, 20, 45]

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=days, y=risk_scores,
    marker_color=["#0088cc" if s < 20 else "#ff6600" if s < 40 else "#cc0000" for s in risk_scores],
    name="피부 위험 점수",
    text=risk_scores, textposition="outside",
))
fig2.add_trace(go.Scatter(
    x=days, y=uv_vals,
    mode="lines+markers",
    name="자외선 지수",
    yaxis="y2",
    line=dict(color="#e07b39", width=2, dash="dash"),
))
fig2.update_layout(
    height=280, margin=dict(l=0, r=0, t=20, b=0),
    yaxis=dict(title="위험 점수", range=[0, 60]),
    yaxis2=dict(title="자외선 지수", overlaying="y", side="right", range=[0, 12]),
    legend=dict(orientation="h", y=-0.2),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig2, use_container_width=True)
st.caption("실제 서비스: 기상청 7일 예보 데이터 + 항암제 광과민성 프로파일 자동 반영")

# ── 약국 안내 (data.go.kr 전국약국정보)
st.divider()
st.subheader("🏪 주변 심야 약국 안내")
st.info("실제 서비스에서는 data.go.kr 전국약국정보 API와 연동하여 24시간 운영 약국을 실시간으로 안내합니다. (MVP 데모 단계에서는 미구현)")
st.markdown("""
| 약국명 | 주소 | 운영시간 | 보유 약품 |
|--------|------|---------|---------|
| 365 종로약국 | 서울 종로구 XX로 | 24시간 | 히드로코티손 연고, 에모리엔트 |
| 을지로 야간약국 | 서울 중구 을지로 | 22:00-익일 08:00 | 베타메타손, 세라마이드 보습제 |
| 강남 심야약국 | 서울 강남구 테헤란로 | 22:00-익일 06:00 | 피부 독성 케어 패키지 |
""")
st.caption("출처: data.go.kr 15000576 전국약국기본정보 (실제 연동 예정)")
