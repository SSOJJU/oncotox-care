"""피부 모니터링 — 사진 업로드 → AI Grade 분류 → 행동 가이드"""

import sys, os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from PIL import Image
import plotly.graph_objects as go
import datetime

from utils.skin_classifier import analyze_skin_image, get_demo_result, model_is_ready
from utils.drug_database import CTCAE_CRITERIA, GENERAL_GUIDELINES, get_drug_list

st.set_page_config(page_title="피부 모니터링 — Onco-Tox Care", page_icon="📸", layout="wide")

with st.sidebar:
    st.markdown("## 🏥 Onco-Tox Care")
    st.caption("항암 부작용 케어 AI SaaS")
    st.divider()
    st.caption("⚠️ 본 AI 분석은 의료기기 허가 전 참고 정보이며, 최종 판단은 담당 의사에게 문의하세요.")

st.title("📸 피부 모니터링")
st.caption("항암제 복용 중 피부 변화를 AI가 매일 분석합니다.")

# 모델 상태 배너
if model_is_ready():
    st.success("🤖 **YOLOv8 AI 모델 준비 완료** — ISIC 2018 dermoscopy 600장 fine-tune (4-class CTCAE Grade 분류)")
else:
    st.warning("⏳ **YOLOv8 모델 학습 중** — 완료 전까지 HSV 색상 분석 폴백 모드로 작동합니다.")

# ── 입력 섹션
col_input, col_result = st.columns([1, 1])

with col_input:
    st.subheader("1️⃣ 오늘의 피부 상태 입력")

    drug_list = get_drug_list()
    selected_drug = st.selectbox("현재 복용 중인 항암제", ["선택 안 함"] + drug_list)

    upload_mode = st.radio("분석 모드", ["📷 사진 업로드 (실제 분석)", "🎬 데모 시나리오 (시연용)"],
                            horizontal=True)

    result = None
    img_display = None

    if upload_mode == "📷 사진 업로드 (실제 분석)":
        uploaded = st.file_uploader(
            "피부 사진 업로드 (손바닥·발바닥·발진 부위)", type=["jpg", "jpeg", "png"],
            help="직접 촬영한 선명한 사진일수록 분석 정확도가 높아집니다."
        )
        if uploaded:
            img = Image.open(uploaded)
            img_display = img
            st.image(img, caption="업로드된 이미지", use_container_width=True)
            with st.spinner("AI 분석 중..."):
                result = analyze_skin_image(img)
    else:
        scenario = st.select_slider(
            "시나리오 선택",
            options=["normal", "grade1", "grade2", "grade3"],
            value="grade2",
            format_func=lambda x: {"normal": "정상", "grade1": "Grade 1", "grade2": "Grade 2", "grade3": "Grade 3"}[x],
        )
        result = get_demo_result(scenario)
        st.info("ℹ️ 데모 모드: 실제 이미지 없이 시나리오 결과를 시연합니다.")

    vas_score = st.slider("통증 지수 (VAS 0-10)", 0, 10, 2, help="0=통증 없음, 10=극심한 통증")
    body_part = st.multiselect("부위 선택", ["손바닥", "발바닥", "얼굴/두경부", "몸통", "팔/다리", "두피"])
    st.text_area("기타 메모 (증상 변화, 특이사항)", height=80, placeholder="예: 어제보다 홍반 부위 넓어짐")

    analyze_btn = st.button("🔍 AI 분석 실행", type="primary", use_container_width=True,
                             disabled=(upload_mode == "📷 사진 업로드 (실제 분석)" and result is None))

with col_result:
    st.subheader("2️⃣ AI 분석 결과")

    if result:
        grade = result["grade"]
        color = result["grade_color"]
        confidence = result["confidence"]

        # Grade 배지
        st.markdown(f"""
        <div style="background:{color}15;border:3px solid {color};border-radius:12px;
                    padding:1.5rem;text-align:center;margin-bottom:1rem">
        <div style="font-size:2rem;font-weight:800;color:{color}">{grade}</div>
        <div style="font-size:0.9rem;color:#555;margin-top:0.3rem">{result['description']}</div>
        <div style="font-size:0.85rem;color:#888;margin-top:0.5rem">
            AI 신뢰도: <b>{confidence}%</b>
        </div>
        </div>
        """, unsafe_allow_html=True)

        # YOLOv8 확률 분포 차트 (모델 결과) 또는 HSV 지표 (폴백)
        top5 = result.get("top5_probs", {})
        if top5:
            grade_order = ["정상", "Grade_1", "Grade_2", "Grade_3"]
            labels_disp = ["정상", "Grade 1", "Grade 2", "Grade 3"]
            bar_colors = ["#0088cc", "#88cc00", "#ff6600", "#cc0000"]
            vals = [top5.get(g, 0) for g in grade_order]
            fig_bar = go.Figure(go.Bar(
                x=labels_disp, y=vals,
                marker_color=bar_colors,
                text=[f"{v:.1f}%" for v in vals],
                textposition="outside",
            ))
            fig_bar.update_layout(
                height=200, margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(range=[0, 110], title="확률 (%)"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            metrics = [
                ("홍반 면적 비율", result["erythema_ratio"], 50, "#e07b39"),
                ("건조/각질 비율", result["dry_ratio"], 60, "#aa8844"),
                ("수포 면적 비율", result["blister_ratio"], 15, "#cc4444"),
            ]
            for label, val, max_val, mcolor in metrics:
                pct = min(val / max_val, 1.0)
                st.markdown(f"""
                <div style="margin-bottom:0.5rem">
                <div style="display:flex;justify-content:space-between;font-size:0.85rem">
                <span>{label}</span><span style="color:{mcolor};font-weight:600">{val:.1f}%</span>
                </div>
                <div style="background:#eee;border-radius:4px;height:8px">
                <div style="background:{mcolor};width:{pct*100:.0f}%;height:8px;border-radius:4px"></div>
                </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # CTCAE 기준 + 권고 조치
        if grade in CTCAE_CRITERIA:
            criteria = CTCAE_CRITERIA[grade]
            st.markdown(f"""
            <div style="background:#f8f9fa;border-radius:8px;padding:1rem">
            <b style="color:{color}">📋 CTCAE 기준</b><br>
            <span style="font-size:0.9rem">{criteria['description']}</span><br><br>
            <b>✅ 권고 조치:</b> {criteria['action']}<br>
            <b>🏥 병원 방문:</b> {criteria['hospital']}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # VAS 연동 경고
        if vas_score >= 7:
            st.error(f"🚨 통증 지수 {vas_score}/10 — 즉시 담당 의사에게 연락하세요.")
        elif vas_score >= 4:
            st.warning(f"⚠️ 통증 지수 {vas_score}/10 — 2일 내 외래 방문 권장.")

        # 일반 관리 지침
        with st.expander("📌 오늘의 피부 관리 체크리스트"):
            for guideline in GENERAL_GUIDELINES:
                st.checkbox(guideline, value=False)

        st.caption(f"_{result['analysis_note']}_")
        st.caption("⚠️ 본 AI 분석은 의료기기 허가 전 참고 정보입니다. 정확한 진단은 의료기관을 방문하세요.")

    else:
        st.info("피부 사진을 업로드하거나 데모 모드를 선택하고 '분석 실행'을 클릭하세요.")
        st.markdown("""
        <div style="background:#f0f8ff;border-radius:8px;padding:1.2rem;margin-top:1rem">
        <b>📊 CTCAE Grade 기준</b>
        <table style="width:100%;margin-top:0.5rem;font-size:0.85rem">
        <tr><td style="color:#88cc00;font-weight:600">Grade 1</td><td>경미, 일상생활 영향 없음</td></tr>
        <tr><td style="color:#ff6600;font-weight:600">Grade 2</td><td>중등도, 부분 제한</td></tr>
        <tr><td style="color:#cc0000;font-weight:600">Grade 3</td><td>심각, 입원·투약 중단 필요</td></tr>
        </table>
        </div>
        """, unsafe_allow_html=True)

# ── 기록 히스토리 (데모)
st.divider()
st.subheader("📅 최근 30일 모니터링 이력 (데모)")

import pandas as pd
import numpy as np

np.random.seed(42)
dates = pd.date_range(end=datetime.date.today(), periods=30)
grades_num = np.clip(np.array([0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 2, 2, 2, 1, 1, 1, 1,
                                2, 2, 1, 1, 0, 0, 0, 1, 1, 2]), 0, 3)
grade_labels = ["정상", "Grade 1", "Grade 2", "Grade 3"]
colors_map = {0: "#0088cc", 1: "#88cc00", 2: "#ff6600", 3: "#cc0000"}

fig_hist = go.Figure()
for g in range(4):
    mask = grades_num == g
    fig_hist.add_trace(go.Scatter(
        x=dates[mask], y=grades_num[mask],
        mode="markers", name=grade_labels[g],
        marker=dict(size=12, color=colors_map[g], symbol="circle"),
    ))
fig_hist.update_layout(
    height=220, margin=dict(l=0, r=0, t=10, b=0),
    yaxis=dict(tickvals=[0, 1, 2, 3], ticktext=["정상", "G1", "G2", "G3"]),
    xaxis_title="날짜", showlegend=True,
    legend=dict(orientation="h", y=-0.35),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_hist, use_container_width=True)
st.caption("실제 서비스에서는 매일 기록이 누적되어 추이 분석에 활용됩니다.")
