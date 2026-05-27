# STEP 1 — 시스템 아키텍처

## 서비스 구조 (3자 통합 SaaS)

```
환자 앱 (B2C)           AI 엔진              B2B 대시보드
─────────────────   ─────────────────    ─────────────────────
피부 사진 업로드   → YOLOv8 Grade 분류  → 부작용 발생 히트맵
VAS 통증 입력      → 멀티소스 위험 보정 → 투약 중단 임계치 알림
투약이력 연동      → 선제적 개입 시점   → PMS 보고서 자동 생성
```

## 기술 스택 (MVP)

| Layer | Tech |
|-------|------|
| Frontend | Streamlit (멀티페이지) |
| AI 피부 분류 | YOLOv8 / 색상-면적 기반 Grade 추정 (데모) |
| 데이터 처리 | pandas, scikit-learn |
| 지도 시각화 | Folium + streamlit-folium |
| 차트 | Plotly |
| 날씨 | wttr.in API (키 불필요) |
| 배포 | Streamlit Community Cloud |

## 페이지 구성

```
oncotox/
├── app.py                    ← 홈 (HIRA 통계 대시보드)
├── pages/
│   ├── 1_📸_피부모니터링.py ← 핵심: 사진 업로드 → AI Grade
│   ├── 2_💊_투약관리.py    ← 항암제 선택 → 부작용 확률 + DUR
│   ├── 3_🌤️_오늘의위험도.py ← 기상청 자외선·습도 → 피부 위험 알림
│   ├── 4_🏥_대시보드.py    ← B2B: HIRA 지역별 현황 + 비용 분석
│   └── 5_📊_데이터근거.py  ← 의학 근거 문헌 + 출처
└── utils/
    ├── hira_oncotox.py      ← HIRA L27.1/T45.1 데이터 처리
    ├── skin_classifier.py   ← AI 피부 Grade 분류
    ├── drug_database.py     ← 항암제 + 부작용 확률 DB
    └── weather_api.py       ← 기상 데이터 API
```
