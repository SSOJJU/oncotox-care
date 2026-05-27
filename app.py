"""Onco-Tox Care — 항암 부작용 케어 AI SaaS 플랫폼 홈"""

import sys
import os
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.hira_oncotox import (
    get_L27_trends, get_T45_trends, get_Z51_trends,
    get_sido_L27, get_market_summary,
)

st.set_page_config(
    page_title="Onco-Tox Care",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 사이드바
with st.sidebar:
    st.markdown("## 🏥 Onco-Tox Care")
    st.caption("항암 부작용 케어 AI SaaS 플랫폼")
    st.divider()
    st.markdown("""
**메뉴**
- 🏠 홈 (현재)
- 📸 피부 모니터링
- 💊 투약 관리
- 🌤️ 오늘의 피부 위험도
- 🏥 B2B 대시보드
- 📊 데이터 근거
    """)
    st.divider()
    st.caption("⚠️ 본 서비스는 참고 정보만 제공하며 의료 진단을 대체하지 않습니다.")

# ── 헤더
st.markdown("""
<div style="background: linear-gradient(90deg,#1a6b8a,#0d3b52); color:white; padding:2rem; border-radius:12px; margin-bottom:1.5rem">
<h1 style="margin:0;font-size:2.2rem">🏥 Onco-Tox Care</h1>
<p style="margin:0.5rem 0 0 0;font-size:1.1rem;opacity:0.9">
항암 치료 중 부작용을 AI가 매일 모니터링 · 선제적 개입으로 응급실 비용 절감
</p>
</div>
""", unsafe_allow_html=True)

# ── KPI 카드
summary = get_market_summary()
cols = st.columns(5)
kpi_data = [
    ("연간 항암화학요법\n환자 수", f"{summary['항암화학요법_환자수']:,}명", "#1a6b8a"),
    ("약물 유발 피부염\n환자 수 (L27.1)", f"{summary['약물유발피부염_환자수']:,}명", "#e07b39"),
    ("항신생물제\n부작용 (T45.1)", f"{summary['항신생물제_부작용_환자수']:,}명", "#cc4444"),
    ("부작용 연간\n진료비", f"{summary['부작용_진료비_억원']:,}억원", "#8844cc"),
    ("AI 선제 개입 시\n절감 잠재액", f"~{summary['응급실_절감_잠재액_억원']:,}억원", "#229944"),
]
for col, (label, value, color) in zip(cols, kpi_data):
    with col:
        st.markdown(f"""
        <div style="background:{color}15;border:2px solid {color}44;border-radius:10px;padding:1rem;text-align:center">
        <div style="font-size:0.8rem;color:#555;white-space:pre-line">{label}</div>
        <div style="font-size:1.6rem;font-weight:700;color:{color}">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── 연도별 추이 차트
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 항암 관련 부작용 환자 수 추이 (HIRA)")
    l27 = get_L27_trends()
    t45 = get_T45_trends()
    z51 = get_Z51_trends()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=z51["year"], y=z51["patients"],
        name="Z51.1 항암화학요법 환자",
        line=dict(color="#1a6b8a", width=3),
        mode="lines+markers",
    ))
    fig.add_trace(go.Scatter(
        x=l27["year"], y=l27["patients"],
        name="L27.1 약물유발 피부염",
        line=dict(color="#e07b39", width=3),
        mode="lines+markers",
    ))
    fig.add_trace(go.Scatter(
        x=t45["year"], y=t45["patients"],
        name="T45.1 항신생물제 부작용",
        line=dict(color="#cc4444", width=3),
        mode="lines+markers",
    ))
    fig.update_layout(
        height=320, margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", y=-0.25),
        yaxis_title="환자 수",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(tickmode="array", tickvals=list(range(2018, 2025)))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("출처: HIRA 보건의료빅데이터개방시스템 질병세분류(4단) 통계")

with col2:
    st.subheader("🗺️ 시도별 약물유발 피부염 환자 분포 (2024)")
    import folium
    from streamlit_folium import folium_static

    sido_df = get_sido_L27()
    m = folium.Map(location=[36.5, 127.8], zoom_start=6, tiles="CartoDB positron")
    max_p = sido_df["patients"].max()
    for _, row in sido_df.iterrows():
        radius = max(8, int(row["patients"] / max_p * 40))
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color="#e07b39",
            fill=True,
            fill_color="#e07b39",
            fill_opacity=0.55,
            weight=2,
            popup=folium.Popup(
                f"<b>{row['sido']}</b><br>"
                f"L27.1 환자수: <b>{int(row['patients']):,}명</b><br>"
                f"10만명당: {row['rate_per_100k']:.1f}명<br>"
                f"<small>출처: HIRA 2024</small>",
                max_width=200,
            ),
            tooltip=f"🏥 {row['sido']} — {int(row['patients']):,}명",
        ).add_to(m)
    folium_static(m, height=320)
    st.caption("출처: HIRA 요양기관소재지별 L27.1 통계 (2024)")

# ── 서비스 차별점
st.divider()
st.subheader("🚀 Onco-Tox Care 3대 차별점")

cols2 = st.columns(3)
differentiators = [
    ("📸 AI 피부 Grade 분류",
     "YOLOv8 기반 피부 병변 자동 인식\nCTCAE Grade 1→3 중증도 분류\n→ 수작업 판독 대비 정확도·속도 향상",
     "#1a6b8a"),
    ("🌤️ 환경-의료 데이터 융합",
     "기상청 자외선·습도 + 환자 복용 항암제\n+ 웨어러블 체온 교차 분석\n→ 선제적 피부 독성 악화 예측",
     "#e07b39"),
    ("💼 B2B 제약사 SaaS",
     "제약사 전용 부작용 발생 실시간 대시보드\nHIRA T45 기반 RWE 데이터 맵핑\n→ 시판 후 조사(PMS) 보고서 자동 생성",
     "#229944"),
]
for col, (title, desc, color) in zip(cols2, differentiators):
    with col:
        st.markdown(f"""
        <div style="border-left:4px solid {color};padding:1rem;background:{color}08;border-radius:0 8px 8px 0">
        <b style="color:{color};font-size:1.05rem">{title}</b>
        <p style="margin-top:0.5rem;font-size:0.9rem;white-space:pre-line">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

# ── 수익 모델
st.divider()
st.subheader("💰 수익 모델 — 3자 통합 구조")

rev_cols = st.columns(4)
rev_data = [
    ("B2B\n제약사", "PMS 보고서 자동화\n연간 데이터 구독", "1억원/계약\n× 3개사 목표", "#1a6b8a"),
    ("B2B\n병원", "종양내과 전용\nSaaS 구독", "월 50-100만원\n× 50개 병원", "#229944"),
    ("B2G\n보건소", "시도 단위\n암 관리 대시보드", "시범사업\n→ 정규 도입", "#8844cc"),
    ("B2C\n환자", "프리미엄\n구독 서비스", "월 2,900원\nFreemium", "#e07b39"),
]
for col, (tier, desc, price, color) in zip(rev_cols, rev_data):
    with col:
        st.markdown(f"""
        <div style="background:{color}12;border:2px solid {color}55;border-radius:10px;padding:1rem;text-align:center">
        <div style="font-size:1rem;font-weight:700;color:{color};white-space:pre-line">{tier}</div>
        <div style="font-size:0.8rem;color:#444;margin:0.4rem 0;white-space:pre-line">{desc}</div>
        <div style="font-size:0.95rem;font-weight:600;color:{color};white-space:pre-line">{price}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
