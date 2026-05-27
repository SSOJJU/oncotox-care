# STEP 3 — MVP 빌드 현황

## ✅ 완료 (2026-05-27)

### 유틸리티 모듈
- [x] `utils/hira_oncotox.py` — HIRA L27.1/T45.1/Z51.1 통계 로더 (CSV 자동 생성)
- [x] `utils/drug_database.py` — 6종 주요 항암제 피부 독성 DB (식약처 허가사항 기반)
- [x] `utils/skin_classifier.py` — HSV 색상 분석 기반 Grade 1-3 분류 (MVP 데모 모드)
- [x] `utils/weather_api.py` — wttr.in API 연동 (서울 실시간 테스트 완료)

### Streamlit 앱
- [x] `app.py` — 홈: HIRA KPI 카드 + 연도별 추이 + 지도 + 수익모델
- [x] `pages/1_📸_피부모니터링.py` — 이미지 업로드 + AI Grade 분류 + 30일 이력
- [x] `pages/2_💊_투약관리.py` — 항암제 프로파일 + DUR 체크 + 개인 위험 점수
- [x] `pages/3_🌤️_오늘의위험도.py` — 기상 API + 7일 예보 + 심야약국 안내
- [x] `pages/4_🏥_대시보드.py` — B2B: KPI + 발생 추이 + 지도 + PMS 보고서
- [x] `pages/5_📊_데이터근거.py` — HIRA 출처 + 임상 문헌 DOI + 규제 대응

### 데이터
- [x] `data/hira/hira_L27_trends.csv` — L27.1 2018-2024 연도별
- [x] `data/hira/hira_T45_trends.csv` — T45.1 2018-2024 연도별 (진료비 포함)
- [x] `data/hira/hira_Z51_trends.csv` — Z51.1 항암화학요법 환자수
- [x] `data/hira/hira_sido_L27.csv` — 시도별 L27.1 환자 분포

## 🔲 남은 작업 (2026-05-28)

- [ ] Streamlit Community Cloud 배포 (GitHub 푸시 필요)
- [ ] 화면 캡처 5장 저장
- [ ] 30초 시연 GIF 제작
- [ ] 사업계획서 [기술구현] + [데이터활용] 섹션 작성

## 앱 실행 방법

```bash
cd /home/ubuntu/kstart/oncotox
source venv/bin/activate
streamlit run app.py --server.port 8502 --server.headless true
# → http://127.0.0.1:8502
```
