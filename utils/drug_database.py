"""항암제 피부 독성 데이터베이스 (식약처 허가사항 + 임상 메타분석 기반)"""

from typing import Dict, List


# 주요 표적항암제 피부 독성 데이터
# 출처: 식약처 허가사항 + ESMO/ASCO 가이드라인 + 임상 메타분석
DRUG_DATABASE = {
    "Sorafenib (소라페닙, 넥사바®)": {
        "icd_code": "C22/C64",  # 간암/신장암
        "brand": "넥사바® (Bayer)",
        "mechanism": "멀티키나아제 억제제 (VEGFR, PDGFR, RAF)",
        "skin_toxicity_overall": 69,  # % 전체 피부 독성
        "hfsr_rate": 45,  # Hand-Foot Skin Reaction (수족 피부 반응)
        "rash_rate": 31,
        "alopecia_rate": 27,
        "grade3_rate": 18,  # Grade 3 이상 (입원·휴약 필요 수준)
        "typical_onset_days": 14,
        "ctcae_mapping": {
            "Grade 1": "홍반·부종·각질 경미 — 보습 강화, 외출 자제",
            "Grade 2": "동통·수포 동반 — 외용 스테로이드, 1주 내 재평가",
            "Grade 3": "괴사·심한 수포 — 즉시 투약 중단, 입원 고려",
        },
        "high_risk_factors": ["당뇨", "고혈압 동반", "이전 피부 독성 병력"],
    },
    "Erlotinib (얼로티닙, 타세바®)": {
        "icd_code": "C34",  # 폐암
        "brand": "타세바® (Roche)",
        "mechanism": "EGFR 타이로신 키나아제 억제제",
        "skin_toxicity_overall": 79,
        "hfsr_rate": 12,
        "rash_rate": 75,  # 여드름형 발진 (acneiform rash) 특징적
        "alopecia_rate": 5,
        "grade3_rate": 9,
        "typical_onset_days": 8,
        "ctcae_mapping": {
            "Grade 1": "구진/농포 < 10% 체표면적 — 외용 항생제, 자외선 차단",
            "Grade 2": "10-30% 체표면적, 심리적 영향 — 경구 항생제(독시사이클린)",
            "Grade 3": "> 30%, 삶의 질 심각 침해 — 용량 감소 또는 중단",
        },
        "high_risk_factors": ["흡연력 없음 (역설적으로 효과↑, 독성도 ↑)", "아시아인"],
    },
    "Capecitabine (카페시타빈, 젤로다®)": {
        "icd_code": "C18/C50",  # 대장암/유방암
        "brand": "젤로다® (Roche)",
        "mechanism": "경구용 플루오로우라실 전구약물",
        "skin_toxicity_overall": 54,
        "hfsr_rate": 54,  # 가장 높은 HFS 발생률
        "rash_rate": 8,
        "alopecia_rate": 6,
        "grade3_rate": 16,
        "typical_onset_days": 21,
        "ctcae_mapping": {
            "Grade 1": "감각 이상·무통성 부종·홍반 — 요소 함유 보습제 2회/일",
            "Grade 2": "동통성 홍반·부종·수포, ADL 지장 — 용량 25% 감량 검토",
            "Grade 3": "심한 수포·궤양, ADL 불능 — 즉시 투약 중단",
        },
        "high_risk_factors": ["노인", "신기능 저하", "DPD 효소 결핍"],
    },
    "Pembrolizumab (펨브롤리주맙, 키트루다®)": {
        "icd_code": "C43/C34/C18",  # 다양한 암종
        "brand": "키트루다® (MSD)",
        "mechanism": "PD-1 면역관문억제제",
        "skin_toxicity_overall": 34,
        "hfsr_rate": 3,
        "rash_rate": 29,  # 면역 관련 피부 독성 (irAE)
        "alopecia_rate": 2,
        "grade3_rate": 3,
        "typical_onset_days": 42,  # 늦게 발현 특징
        "ctcae_mapping": {
            "Grade 1": "경미한 반점구진성 발진 — 경과 관찰, 보습",
            "Grade 2": "면적 10-30%, 삶의질 영향 — 경구 스테로이드(프레드니솔론 0.5-1 mg/kg)",
            "Grade 3": "수포·박탈, 전신 증상 — 투약 중단, 고용량 스테로이드(1-2 mg/kg), 피부과 협진",
        },
        "high_risk_factors": ["자가면역질환 기왕력", "스테로이드 의존성"],
        "special_note": "irAE — 면역 관련 이상반응. 스테로이드 금기 시 고려 필요",
    },
    "Paclitaxel (파클리탁셀, 탁솔®)": {
        "icd_code": "C50/C56/C34",
        "brand": "탁솔® (BMS)",
        "mechanism": "미세소관 안정화제 (탁산 계열)",
        "skin_toxicity_overall": 42,
        "hfsr_rate": 6,
        "rash_rate": 15,
        "alopecia_rate": 87,  # 매우 높은 탈모율
        "grade3_rate": 5,
        "typical_onset_days": 10,
        "ctcae_mapping": {
            "Grade 1": "경미한 탈모/발진 — 두피 보호, 냉각 헬멧 고려",
            "Grade 2": "현저한 탈모·색소침착 — 심리 지지, 가발 상담",
            "Grade 3": "전신 탈모·각질·광과민성 — 피부과 의뢰",
        },
        "high_risk_factors": ["누적 용량 고용량", "방사선 병용"],
    },
    "Cetuximab (세툭시맙, 어비툭스®)": {
        "icd_code": "C18/C10",  # 대장암/두경부암
        "brand": "어비툭스® (Merck KGaA)",
        "mechanism": "EGFR 단클론항체",
        "skin_toxicity_overall": 88,  # 가장 높은 피부 독성 빈도
        "hfsr_rate": 14,
        "rash_rate": 82,  # 여드름형 발진 대표적
        "alopecia_rate": 2,
        "grade3_rate": 12,
        "typical_onset_days": 7,
        "ctcae_mapping": {
            "Grade 1": "구진·농포 < 10% — 외용 클린다마이신·스테로이드",
            "Grade 2": "10-30%, 중등도 동통 — 경구 독시사이클린 100mg/일",
            "Grade 3": "> 30%, 감염 징후 — 용량 감량, 항생제 정주 고려",
        },
        "high_risk_factors": ["KRAS 야생형 (반응률 높지만 독성도 ↑)", "고령"],
        "special_note": "발진 중증도와 항암 반응률 양의 상관 (P rash = P response)",
    },
}

# CTCAE Grade 기준 요약
CTCAE_CRITERIA = {
    "Grade 1": {
        "description": "경미한 증상, 일상생활 영향 없음",
        "color": "#88cc00",
        "action": "보습제·자외선 차단 강화, 주 1회 자가 모니터링",
        "hospital": "정기 외래 일정 유지",
    },
    "Grade 2": {
        "description": "중등도 증상, 일상생활 부분 제한",
        "color": "#ffaa00",
        "action": "외용/경구 약제 추가, 1-2주 내 외래 재방문",
        "hospital": "2주 이내 외래 예약",
    },
    "Grade 3": {
        "description": "심한 증상, 일상생활 불능 또는 입원 필요",
        "color": "#cc0000",
        "action": "투약 중단 검토, 즉시 담당의 연락",
        "hospital": "24시간 내 응급 외래 또는 입원",
    },
}

# 부작용 관리 일반 지침 (모든 항암제 공통)
GENERAL_GUIDELINES = [
    "매일 같은 시간에 피부 상태 사진 촬영 (변화 추적용)",
    "자외선 차단제 SPF50+ 매일 외출 전 도포",
    "보습제는 무향·무파라벤 제품으로 하루 2회 이상",
    "뜨거운 물 샤워 자제 — 미온수 사용",
    "꼭 끼는 신발·장갑 착용 자제 (수족 증후군 예방)",
    "Grade 1 이상 징후 발견 시 앱에 즉시 기록",
]


def get_drug_list() -> List[str]:
    return list(DRUG_DATABASE.keys())


def get_drug_info(drug_name: str) -> Dict:
    return DRUG_DATABASE.get(drug_name, {})


def get_skin_risk_score(drug_name: str, age: int, has_diabetes: bool, prior_skin: bool) -> int:
    """개인화 피부 독성 위험 점수 (0-100)"""
    info = DRUG_DATABASE.get(drug_name, {})
    if not info:
        return 30
    base = info.get("skin_toxicity_overall", 30)
    if age >= 65:
        base = min(base + 10, 95)
    if has_diabetes:
        base = min(base + 8, 95)
    if prior_skin:
        base = min(base + 12, 95)
    return int(base)
