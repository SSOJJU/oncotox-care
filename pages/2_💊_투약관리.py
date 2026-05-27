"""투약 관리 — 항암제 선택 → 피부 독성 확률 + DUR 병용금기 체크"""

import sys, os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.graph_objects as go

from utils.drug_database import DRUG_DATABASE, get_drug_list, get_skin_risk_score

st.set_page_config(page_title="투약 관리 — Onco-Tox Care", page_icon="💊", layout="wide")

with st.sidebar:
    st.markdown("## 🏥 Onco-Tox Care")
    st.caption("항암 부작용 케어 AI SaaS")
    st.divider()
    st.caption("⚠️ 본 정보는 식약처 허가사항 기반 참고 자료입니다.")

st.title("💊 투약 관리 & 부작용 확률")
st.caption("복용 중인 항암제를 선택하면 피부 독성 발생 확률과 관리 가이드를 제공합니다.")

drug_list = get_drug_list()
selected_drug = st.selectbox("항암제 선택", drug_list, index=0)
info = DRUG_DATABASE[selected_drug]

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"📊 {selected_drug} 피부 독성 프로파일")

    # 레이더 차트
    categories = ["전체 피부독성", "수족피부반응", "여드름형 발진", "탈모", "Grade3+"]
    values = [
        info["skin_toxicity_overall"],
        info["hfsr_rate"],
        info["rash_rate"],
        info["alopecia_rate"],
        info["grade3_rate"],
    ]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(26,107,138,0.2)",
        line=dict(color="#1a6b8a", width=2),
        name=selected_drug[:20],
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=350, margin=dict(l=30, r=30, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # 핵심 수치 카드
    metric_cols = st.columns(3)
    metric_cols[0].metric("전체 피부 독성", f"{info['skin_toxicity_overall']}%")
    metric_cols[1].metric("Grade 3+ 비율", f"{info['grade3_rate']}%", delta="입원 위험", delta_color="inverse")
    metric_cols[2].metric("평균 발현 시기", f"{info['typical_onset_days']}일째")

with col2:
    st.subheader("🎯 CTCAE Grade별 기준 및 권고 조치")

    for grade, criteria in info["ctcae_mapping"].items():
        colors = {"Grade 1": "#88cc00", "Grade 2": "#ff6600", "Grade 3": "#cc0000"}
        c = colors.get(grade, "#888")
        st.markdown(f"""
        <div style="background:{c}10;border-left:4px solid {c};padding:0.8rem;border-radius:0 8px 8px 0;margin-bottom:0.7rem">
        <b style="color:{c}">{grade}</b><br>
        <span style="font-size:0.9rem">{criteria}</span>
        </div>
        """, unsafe_allow_html=True)

    if "special_note" in info:
        st.info(f"💡 **특이사항**: {info['special_note']}")

    # 고위험 인자
    if info.get("high_risk_factors"):
        st.markdown("**⚠️ 고위험 인자 (독성 발생 가능성 높이는 조건):**")
        for factor in info["high_risk_factors"]:
            st.markdown(f"- {factor}")

# ── 개인화 위험도 계산
st.divider()
st.subheader("🧬 개인 맞춤 피부 독성 위험 점수")

p_cols = st.columns(4)
with p_cols[0]:
    age = st.number_input("나이", 20, 90, 58)
with p_cols[1]:
    has_diabetes = st.checkbox("당뇨 동반")
with p_cols[2]:
    prior_skin = st.checkbox("이전 피부 독성 병력")
with p_cols[3]:
    renal = st.checkbox("신기능 저하")

personal_score = get_skin_risk_score(selected_drug, age, has_diabetes, prior_skin)

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=personal_score,
    delta={"reference": info["skin_toxicity_overall"], "valueformat": ".0f"},
    title={"text": "개인 피부 독성 위험 점수", "font": {"size": 16}},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#1a6b8a"},
        "steps": [
            {"range": [0, 30], "color": "#e8f5e9"},
            {"range": [30, 60], "color": "#fff8e1"},
            {"range": [60, 80], "color": "#ffebee"},
            {"range": [80, 100], "color": "rgba(204,0,0,0.12)"},
        ],
        "threshold": {"line": {"color": "#cc0000", "width": 3}, "value": 70},
    },
))
fig_gauge.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20),
                         paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_gauge, use_container_width=True)

if personal_score >= 70:
    st.error("🔴 고위험 — 치료 시작 전 반드시 피부과 베이스라인 검사 수행 권장.")
elif personal_score >= 50:
    st.warning("🟠 중위험 — 주 2회 피부 모니터링 및 예방적 보습제 처방 권장.")
else:
    st.success("🟢 저위험 — 주 1회 정기 모니터링 및 기본 예방 조치.")

# ── DUR 병용 체크
st.divider()
st.subheader("🔍 DUR 병용금기 간이 체크 (HIRA DUR 기반)")

add_meds = st.multiselect(
    "동시에 복용 중인 다른 약물 (해당 사항 선택)",
    ["아스피린", "이부프로펜(NSAIDs)", "와파린", "스테로이드(경구)", "항생제(퀴놀론계)",
     "항히스타민제", "메트포르민", "혈압약(ACE억제제)", "프로톤펌프억제제(PPI)"],
)

if add_meds:
    warnings = []
    if "와파린" in add_meds and "Capecitabine" in selected_drug:
        warnings.append("⚠️ **카페시타빈 + 와파린**: INR 증가 → 출혈 위험. 정기 INR 모니터링 필수 (HIRA DUR 주의)")
    if "이부프로펜(NSAIDs)" in add_meds:
        warnings.append("⚠️ **NSAIDs 병용**: 신독성·위장관 독성 위험 증가. 아세트아미노펜 우선 사용 권장")
    if "스테로이드(경구)" in add_meds and "Pembrolizumab" in selected_drug:
        warnings.append("⚠️ **PD-1 억제제 + 스테로이드**: 스테로이드가 면역치료 효과를 저하시킬 수 있음 — 담당의 협의 필수")
    if "항생제(퀴놀론계)" in add_meds and ("Erlotinib" in selected_drug or "Cetuximab" in selected_drug):
        warnings.append("✅ **EGFR 억제제 + 독시사이클린(퀴놀론)**: Grade 2+ 여드름형 발진에 공식 권고 병용 (ESMO 가이드라인)")

    if warnings:
        for w in warnings:
            st.markdown(w)
    else:
        st.success("선택된 약물 조합에서 주요 상호작용 정보 없음. 담당 약사·의사에게 최종 확인 권장.")
else:
    st.info("병용 약물을 선택하면 HIRA DUR 기반 상호작용 정보를 제공합니다.")

st.caption("출처: HIRA 의약품안전사용서비스(DUR) · ESMO/ASCO 가이드라인 · 식약처 허가사항")
