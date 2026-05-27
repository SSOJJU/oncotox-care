"""데이터 근거 — 의학 문헌 + 데이터 출처 (심사위원용)"""

import sys, os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

st.set_page_config(page_title="데이터 근거 — Onco-Tox Care", page_icon="📊", layout="wide")

with st.sidebar:
    st.markdown("## 🏥 Onco-Tox Care")
    st.caption("항암 부작용 케어 AI SaaS")
    st.divider()
    st.caption("본 페이지는 서비스의 의학적 근거와 데이터 출처를 제공합니다.")

st.title("📊 데이터 근거 및 알고리즘 출처")
st.caption("심사위원 및 의료진을 위한 기술·의학 근거 문서")

# ── 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["🏥 HIRA 공공데이터", "📚 의학적 근거", "🤖 AI 알고리즘", "⚖️ 규제 대응"])

with tab1:
    st.subheader("활용 HIRA 공공 데이터")
    st.markdown("""
    | 데이터셋 | 코드 | 출처 URL | 활용 방법 |
    |---------|------|---------|---------|
    | 질병세분류 4단상병 통계 | **L27.1** (약물유발 피부염) | opendata.hira.or.kr | 연도별·시도별 환자 규모 산출 |
    | 질병세분류 4단상병 통계 | **T45.1** (항신생물제 부작용) | opendata.hira.or.kr | 항암 부작용 입원·외래 비용 베이스라인 |
    | 질병세분류 4단상병 통계 | **Z51.1** (항암화학요법) | opendata.hira.or.kr | TAM(총유효시장) 산출 — 연간 항암 환자수 |
    | 의약품안전사용서비스 | DUR 병용금기 DB | HIRA DUR | 약물 상호작용 체크 로직 |
    | 보건복지부 마이데이터 | 투약이력 API | 나의건강기록 | 환자 항암제 자동 연동 (Phase 2) |
    """)

    with st.expander("📋 HIRA 데이터 다운로드 방법"):
        st.markdown("""
        1. [HIRA 보건의료빅데이터개방시스템](https://opendata.hira.or.kr) 접속
        2. **[질병 통계]** → **[4단상병]** → **[성별입원외래별 현황]** 탭
        3. 질병 코드 검색: `L27`, `T45`, `Z51`
        4. 기준년도 범위 선택 → Excel 다운로드
        5. 요양기관소재지별 탭 → 시도별 분포 데이터
        """)

with tab2:
    st.subheader("임상 근거 문헌")

    st.markdown("### CTCAE 기준 (FDA/NCI)")
    st.markdown("""
    - **출처**: Common Terminology Criteria for Adverse Events (CTCAE) v5.0
    - **발행처**: U.S. Department of Health and Human Services, National Institutes of Health
    - **URL**: ctep.cancer.gov/protocoldevelopment/electronic_applications/ctc.htm
    - **적용**: 피부 독성 Grade 1-3 분류 기준, 항암 임상시험 표준 척도
    """)

    st.markdown("### 주요 항암제 피부 독성 근거")
    evidence = {
        "Sorafenib 피부 독성": {
            "rate": "HFSR 45%, 전체 피부 독성 69%",
            "source": "Escudier B, et al. N Engl J Med 2007;356:125-134 (TARGET trial)",
            "doi": "10.1056/NEJMoa060655",
        },
        "EGFR 억제제 여드름형 발진": {
            "rate": "Erlotinib 75%, Cetuximab 82%",
            "source": "Lacouture ME, et al. J Clin Oncol 2006;24:4931-4939",
            "doi": "10.1200/JCO.2006.06.0889",
        },
        "Capecitabine 수족증후군": {
            "rate": "전체 54%, Grade 3+ 16%",
            "source": "Scheithauer W, et al. Ann Oncol 2003;14:1735-1743",
            "doi": "10.1093/annonc/mdg476",
        },
        "PD-1 억제제 면역 피부 독성": {
            "rate": "Pembrolizumab 34% (Grade 3: 3%)",
            "source": "Ribas A, et al. N Engl J Med 2016;375:1,893-903 (KEYNOTE-006)",
            "doi": "10.1056/NEJMoa1606774",
        },
    }
    for drug_key, ev in evidence.items():
        with st.expander(f"📄 {drug_key}"):
            st.markdown(f"""
            - **발생률**: {ev['rate']}
            - **근거**: {ev['source']}
            - **DOI**: {ev['doi']}
            """)

    st.markdown("### 국내 관련 통계")
    st.markdown("""
    - **KDCA 암 등록 통계 (2024)**: 국내 신규 암 환자 약 27만명/년
    - **건강보험심사평가원 암 요양급여비 (2024)**: 항암제 약품비 3조 8,000억원
    - **보건복지부 암 생존율 통계**: 5년 상대 생존율 72.1% (2023)
    """)

with tab3:
    st.subheader("AI 알고리즘 설계 근거")

    st.markdown("### MVP: 색상·면적 기반 Grade 추정")
    st.markdown("""
    **알고리즘 로직**:
    ```
    1. 입력 이미지 → RGB → HSV 색공간 변환
    2. 홍반 픽셀 마스크: H ∈ [0°,25°] ∪ [335°,360°], S > 25%, V > 30%
    3. 각질/건조 마스크: S < 15%, V > 65%
    4. 수포 마스크: S < 10%, V > 82%
    5. 각 마스크 픽셀 비율 → CTCAE Grade 1-3 매핑
    ```
    """)

    st.markdown("### 정식 출시: YOLOv8 기반 피부 병변 감지")
    st.markdown("""
    | 항목 | 내용 |
    |------|------|
    | **Base model** | YOLOv8n (Ultralytics) — 경량화, 모바일 추론 가능 |
    | **학습 데이터셋** | ISIC 2018/2019 피부 병변 데이터셋 + 항암 피부 독성 이미지 (수집 예정) |
    | **분류 클래스** | 정상, HFSR Grade 1-3, 여드름형 발진 Grade 1-3, 탈모, 색소침착 |
    | **정확도 목표** | CTCAE Grade 분류 AUC ≥ 0.85 |
    | **검증 방법** | 피부과 전문의 판독과 blind comparison |
    """)

    st.markdown("### 멀티소스 융합 보정 모델")
    st.markdown("""
    ```python
    # 최종 위험 점수 산출식
    final_risk = (
        0.50 × yolo_grade_score +      # AI 피부 이미지 분석
        0.20 × weather_risk_score +    # 기상 환경 (자외선·습도)
        0.20 × drug_baseline_rate +    # 항암제 독성 프로파일
        0.10 × wearable_stress_score   # 웨어러블 체온·심박 (Phase 2)
    )
    ```
    """)

with tab4:
    st.subheader("규제 준수 및 의료법 대응")

    st.markdown("### 의료기기 소프트웨어(SaMD) 로드맵")
    st.markdown("""
    | Phase | 상태 | 규제 전략 |
    |-------|------|---------|
    | Phase 1 (현재) | MVP | "피부 변화 모니터링 참고 정보" — 의료기기 해당 없음 |
    | Phase 2 (1년차) | B2B SaaS | 의료기기법 시행규칙 제2조 예외: 단순 정보 제공 소프트웨어 |
    | Phase 3 (2-3년차) | DTx 허가 | 식약처 의료기기 소프트웨어 2등급 허가 신청 (임상 데이터 필요) |
    """)

    st.markdown("### 개인정보 보호")
    st.markdown("""
    - **가명처리**: 개인정보보호법 제28조의2 — 환자 사진/처방 데이터 가명 처리 후 저장
    - **K-CURE 가이드라인**: 보건의료 데이터 활용 가이드라인 준수
    - **데이터 분리**: 환자 사진 (S3 별도 계정) / 처방 데이터 (PostgreSQL 암호화) / 분석 결과 (집계 테이블)
    - **동의 체계**: 마이데이터 연동 시 환자 동의 후 최소 데이터 원칙
    """)

    st.markdown("### 면책 고지 (서비스 내 표시)")
    st.info("""
    ⚠️ **면책 고지 (모든 페이지 하단 고정)**

    본 서비스는 의료기기 허가 전 참고 정보만 제공하며, 의료 진단 또는 치료 결정을 대체하지 않습니다.
    AI 분석 결과는 보조적 참고 자료이며, 최종 판단은 반드시 담당 의사에게 문의하시기 바랍니다.
    """)
