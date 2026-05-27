"""
피부 병변 AI 분류기
MVP 단계: 색상(HSV) + 면적 기반 Grade 추정 (데모 모드)
정식 출시: YOLOv8 fine-tuned on ISIC + 항암 피부 독성 데이터셋
"""

import io
import numpy as np
from PIL import Image


def analyze_skin_image(image: Image.Image) -> dict:
    """
    업로드된 피부 이미지를 분석하여 CTCAE Grade 및 부위 설명 반환.

    MVP 알고리즘:
    1. 이미지를 RGB → HSV 변환
    2. 홍반 픽셀 비율 (H: 340-360, 0-20 / S: >50 / V: >50) 계산
    3. 병변 픽셀 밀집도 (OpenCV contour 없이 단순 면적 비율) 추정
    4. Grade 1-3 분류
    """
    try:
        img_array = np.array(image.convert("RGB")).astype(np.float32)
        h, w = img_array.shape[:2]
        total_pixels = h * w

        # HSV 변환 (수동)
        r, g, b = img_array[:, :, 0] / 255, img_array[:, :, 1] / 255, img_array[:, :, 2] / 255
        cmax = np.maximum(np.maximum(r, g), b)
        cmin = np.minimum(np.minimum(r, g), b)
        delta = cmax - cmin

        # Saturation
        sat = np.where(cmax > 0, delta / (cmax + 1e-6), 0)
        # Value
        val = cmax
        # Hue
        hue = np.zeros_like(r)
        mask_r = (cmax == r) & (delta > 0)
        hue[mask_r] = (60 * ((g[mask_r] - b[mask_r]) / delta[mask_r]) % 360)
        mask_g = (cmax == g) & (delta > 0)
        hue[mask_g] = 60 * ((b[mask_g] - r[mask_g]) / delta[mask_g]) + 120
        mask_b = (cmax == b) & (delta > 0)
        hue[mask_b] = 60 * ((r[mask_b] - g[mask_b]) / delta[mask_b]) + 240

        # 홍반 판정: hue (0-25° or 335-360°) + 충분한 채도/밝기
        erythema_mask = (
            ((hue <= 25) | (hue >= 335)) &
            (sat > 0.25) &
            (val > 0.30)
        )
        # 각질/건조 판정: 낮은 채도, 중간 밝기 (흰색 배경 제외하기 위해 val 상한 추가)
        dry_mask = (sat < 0.15) & (val > 0.55) & (val < 0.92)
        # 수포 판정: 매우 높은 밝기, 낮은 채도 — 반드시 주변 홍반 동반 조건 체크는 Grade 판정 시 처리
        blister_mask = (sat < 0.10) & (val > 0.85)

        erythema_ratio = float(erythema_mask.sum()) / total_pixels
        dry_ratio = float(dry_mask.sum()) / total_pixels
        blister_ratio = float(blister_mask.sum()) / total_pixels

        # Grade 판정
        # 수포: 홍반이 최소 3% 이상 동반될 때만 인정 (흰 배경 오분류 방지)
        blister_with_erythema = blister_ratio > 0.05 and erythema_ratio > 0.03
        if blister_with_erythema or erythema_ratio > 0.40:
            grade = "Grade 3"
            grade_color = "#cc0000"
            description = "수포·광범위 홍반 감지. 즉시 담당 의사 연락 필요."
            confidence = min(55 + int(erythema_ratio * 80), 88)
        elif erythema_ratio > 0.18 or dry_ratio > 0.35:
            grade = "Grade 2"
            grade_color = "#ff6600"
            description = "중등도 홍반·각질 감지. 외용 스테로이드 도포 및 1-2주 내 외래 방문 권장."
            confidence = min(52 + int(erythema_ratio * 60), 85)
        elif erythema_ratio > 0.06 or dry_ratio > 0.15:
            grade = "Grade 1"
            grade_color = "#88cc00"
            description = "경미한 홍반·건조 징후. 보습제 강화 및 자외선 차단 철저히."
            confidence = min(50 + int(erythema_ratio * 50), 82)
        else:
            grade = "정상 범위"
            grade_color = "#0088cc"
            description = "뚜렷한 병변 신호 없음. 예방적 보습 관리 지속."
            confidence = 70

        return {
            "grade": grade,
            "grade_color": grade_color,
            "description": description,
            "confidence": confidence,
            "erythema_ratio": round(erythema_ratio * 100, 1),
            "dry_ratio": round(dry_ratio * 100, 1),
            "blister_ratio": round(blister_ratio * 100, 1),
            "analysis_note": "MVP 분석 모드 (색상·면적 기반). 정식 YOLOv8 모델 탑재 예정.",
        }

    except Exception as e:
        return {
            "grade": "분석 오류",
            "grade_color": "#888888",
            "description": f"이미지 분석 중 오류: {e}",
            "confidence": 0,
            "erythema_ratio": 0,
            "dry_ratio": 0,
            "blister_ratio": 0,
            "analysis_note": "이미지 형식을 확인해 주세요.",
        }


def get_demo_result(scenario: str = "grade2") -> dict:
    """데모용 결과값 — 실제 이미지 없을 때 시연용"""
    scenarios = {
        "grade1": {
            "grade": "Grade 1", "grade_color": "#88cc00",
            "description": "경미한 홍반·건조 징후. 보습제 강화 및 자외선 차단 철저히.",
            "confidence": 78, "erythema_ratio": 8.2, "dry_ratio": 18.5, "blister_ratio": 0.1,
            "analysis_note": "데모 시나리오",
        },
        "grade2": {
            "grade": "Grade 2", "grade_color": "#ff6600",
            "description": "중등도 홍반·각질 감지. 외용 스테로이드 도포 및 1-2주 내 외래 방문 권장.",
            "confidence": 82, "erythema_ratio": 22.7, "dry_ratio": 38.1, "blister_ratio": 0.8,
            "analysis_note": "데모 시나리오",
        },
        "grade3": {
            "grade": "Grade 3", "grade_color": "#cc0000",
            "description": "수포·광범위 홍반 감지. 즉시 담당 의사 연락 필요.",
            "confidence": 87, "erythema_ratio": 44.3, "dry_ratio": 25.6, "blister_ratio": 6.2,
            "analysis_note": "데모 시나리오",
        },
        "normal": {
            "grade": "정상 범위", "grade_color": "#0088cc",
            "description": "뚜렷한 병변 신호 없음. 예방적 보습 관리 지속.",
            "confidence": 74, "erythema_ratio": 3.1, "dry_ratio": 9.4, "blister_ratio": 0.0,
            "analysis_note": "데모 시나리오",
        },
    }
    return scenarios.get(scenario, scenarios["grade2"])
