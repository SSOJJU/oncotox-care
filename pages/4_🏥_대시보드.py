"""B2B 대시보드 — 제약사·병원 전용 부작용 현황 모니터링"""

import sys, os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static

from utils.hira_oncotox import get_L27_trends, get_T45_trends, get_Z51_trends, get_sido_L27

st.set_page_config(page_title="B2B 대시보드 — Onco-Tox Care", page_icon="🏥", layout="wide")

with st.sidebar:
    st.markdown("## 🏥 Onco-Tox Care")
    st.caption("제약사·병원 전용 관리자 뷰")
    st.divider()
    dashboard_type = st.radio("대시보드 유형", ["제약사 뷰", "병원 종양내과 뷰"])
    target_drug = st.selectbox("모니터링 약물", ["Sorafenib", "Erlotinib", "Capecitabine", "Pembrolizumab"])
    period = st.selectbox("기간", ["최근 1개월", "최근 3개월", "최근 6개월", "2024 연간"])
    st.divider()
    st.caption("⚠️ 본 대시보드는 가명 처리된 집계 데이터를 표시합니다.")

st.title("🏥 B2B 관리자 대시보드")
st.caption(f"{'제약사' if dashboard_type == '제약사 뷰' else '병원 종양내과'} 전용 — {target_drug} 부작용 모니터링")

# ── 핵심 KPI
kpi_cols = st.columns(5)
np.random.seed(42)
kpi_vals = [
    ("모니터링 중 환자", "247명", "+12 (이번 달)", "#1a6b8a"),
    ("Grade 2+ 발생률", "23.4%", "전월 대비 -2.1%", "#e07b39"),
    ("Grade 3 발생", "8건", "투약 중단 3건", "#cc4444"),
    ("조기 개입 성공", "71%", "응급실 미방문", "#229944"),
    ("평균 Grade 발현일", "16일째", f"{target_drug} 기준", "#8844cc"),
]
for col, (label, value, sub, color) in zip(kpi_cols, kpi_vals):
    with col:
        st.markdown(f"""
        <div style="background:{color}12;border:2px solid {color}44;border-radius:10px;
                    padding:0.8rem;text-align:center">
        <div style="font-size:0.75rem;color:#555">{label}</div>
        <div style="font-size:1.5rem;font-weight:700;color:{color}">{value}</div>
        <div style="font-size:0.75rem;color:#888">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📈 부작용 Grade 발생 추이 (최근 30일, 데모)")
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    grade1 = np.random.poisson(8, 30)
    grade2 = np.random.poisson(4, 30)
    grade3 = np.array([0]*20 + [1, 2, 0, 1, 0, 1, 0, 1, 0, 1])

    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=grade1, name="Grade 1", marker_color="#88cc0088"))
    fig.add_trace(go.Bar(x=dates, y=grade2, name="Grade 2", marker_color="#ff660088"))
    fig.add_trace(go.Bar(x=dates, y=grade3, name="Grade 3", marker_color="#cc000088"))
    fig.update_layout(
        barmode="stack", height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", y=-0.25),
        yaxis_title="발생 건수",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 Grade 분포 (현재 모니터링 중)")
    labels = ["정상", "Grade 1", "Grade 2", "Grade 3"]
    values = [142, 68, 31, 6]
    colors = ["#0088cc", "#88cc00", "#ff6600", "#cc0000"]

    fig_pie = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=colors,
        hole=0.4,
        textinfo="label+percent",
    ))
    fig_pie.update_layout(
        height=300, margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── 지역별 부작용 지도
st.divider()
st.subheader("🗺️ 시도별 L27.1 약물유발 피부염 현황 (HIRA 2024)")

col_map, col_table = st.columns([2, 1])

with col_map:
    sido_df = get_sido_L27()
    m = folium.Map(location=[36.5, 127.8], zoom_start=6, tiles="CartoDB positron")
    max_p = sido_df["patients"].max()
    for _, row in sido_df.iterrows():
        radius = max(8, int(row["patients"] / max_p * 45))
        color = "#cc0000" if row["rate_per_100k"] > 40 else "#ff6600" if row["rate_per_100k"] > 35 else "#88cc00"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.55, weight=2,
            popup=folium.Popup(
                f"<b>{row['sido']}</b><br>L27.1 환자: {int(row['patients']):,}명<br>"
                f"10만명당: {row['rate_per_100k']:.1f}명",
                max_width=180,
            ),
            tooltip=f"{row['sido']}: {int(row['patients']):,}명",
        ).add_to(m)
    folium_static(m, height=350)

with col_table:
    st.dataframe(
        sido_df[["sido", "patients", "rate_per_100k"]].rename(
            columns={"sido": "시도", "patients": "환자수(명)", "rate_per_100k": "10만명당"}
        ).sort_values("rate_per_100k", ascending=False).reset_index(drop=True),
        use_container_width=True, height=350,
    )
    st.caption("출처: HIRA 보건의료빅데이터개방시스템 (2024)")

# ── RWE 리포트 (데모)
st.divider()
st.subheader("📄 RWE 시판 후 조사 보고서 자동 생성 (데모)")

if st.button("📥 PMS 보고서 초안 생성 (PDF)", type="secondary"):
    with st.spinner("HIRA 데이터 기반 보고서 생성 중..."):
        pass  # 실제 생성 로직 자리 (time.sleep 제거 — Streamlit UI 블로킹 방지)
    st.success("✅ 보고서 초안 생성 완료!")
    st.markdown(f"""
    **[{target_drug} 시판 후 피부 독성 모니터링 보고서 — 2024 Q1-Q4]**

    - **모니터링 기간**: 2024.01.01 ~ 2024.12.31
    - **대상 환자 수**: 247명 (서비스 가입 기준)
    - **전체 피부 독성 발생률**: 23.4% (Grade 1+)
    - **Grade 3 발생 건수**: 8건 (3.2%), 투약 중단 3건 포함
    - **AI 조기 감지 → 조치 성공률**: 71% (Grade 3 진행 전 개입)
    - **추정 응급실 내원 절감**: 연간 약 **5,640만원** 절감 (건당 120만원 × 47건)
    - **HIRA T45.1 청구 대비 당사 감지 민감도**: 94.2%

    ---
    *본 보고서는 Onco-Tox Care 플랫폼 수집 데이터 + HIRA 가명결합 데이터 기반으로 자동 생성됩니다.*
    *식약처 PMS 보고 서식에 맞춰 최종 검토 후 제출하세요.*
    """)

# ── 비용 절감 분석
st.divider()
st.subheader("💰 비용 절감 시뮬레이션")

t45 = get_T45_trends()
years = t45["year"].tolist()
total_patients = t45["patients"].tolist()
hospitalized = [int(p * 0.58) for p in total_patients]  # 58% 입원 비율
cost_without = [int(h * 120) for h in hospitalized]  # 건당 120만원
cost_with = [int(c * 0.29) for c in cost_without]  # AI 개입 시 71% 절감

fig_cost = go.Figure()
fig_cost.add_trace(go.Bar(x=years, y=cost_without, name="개입 전 진료비 (백만원)", marker_color="#cc444488"))
fig_cost.add_trace(go.Bar(x=years, y=cost_with, name="AI 조기개입 후 (백만원)", marker_color="#22994488"))
fig_cost.update_layout(
    barmode="group", height=280,
    margin=dict(l=0, r=0, t=20, b=0),
    yaxis_title="진료비 (백만원)",
    legend=dict(orientation="h", y=-0.25),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_cost, use_container_width=True)
st.caption("HIRA T45.1 입원 환자 기준, AI 선제 개입 71% 성공 시나리오 (내부 시뮬레이션)")
