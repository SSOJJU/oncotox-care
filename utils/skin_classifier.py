"""
피부 병변 AI 분류기
- 운영 모드: YOLOv8n-cls (ISIC 2018 dermoscopy 600장 fine-tune)
- 폴백 모드: HSV 색상·면적 기반 Grade 추정 (모델 파일 없을 때)
"""

import os
import numpy as np
from PIL import Image

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "yolo_runs",
                          "skin_grade_cls", "weights", "best.pt")

# 클래스 순서는 YOLOv8 names dict 기준 (알파벳 정렬: Grade_1, Grade_2, Grade_3, 정상)
# → 실제 추론 시 model.names 로 확인
GRADE_META = {
    "정상":   {"color": "#0088cc", "description": "뚜렷한 병변 신호 없음. 예방적 보습 관리 지속.",
               "action": "정기 보습·자외선 차단 루틴 유지"},
    "Grade_1": {"color": "#88cc00", "description": "경미한 홍반·건조 징후. 보습제 강화 및 자외선 차단 철저히.",
                "action": "보습제·자외선 차단 강화, 주 1회 자가 모니터링"},
    "Grade_2": {"color": "#ff6600", "description": "중등도 홍반·각질 감지. 외용 스테로이드 도포 및 1-2주 내 외래 방문 권장.",
                "action": "외용/경구 약제 추가, 1-2주 내 외래 재방문"},
    "Grade_3": {"color": "#cc0000", "description": "수포·광범위 홍반 감지. 즉시 담당 의사 연락 필요.",
                "action": "투약 중단 검토, 즉시 담당의 연락"},
}

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        from ultralytics import YOLO
        _model = YOLO(MODEL_PATH)
        return _model
    except Exception:
        return None


def analyze_skin_image(image: Image.Image) -> dict:
    """
    업로드된 피부 이미지 → CTCAE Grade 분류.
    YOLOv8 모델이 있으면 AI 추론, 없으면 HSV 폴백.
    """
    model = _load_model()
    if model is not None:
        return _yolo_inference(model, image)
    return _hsv_fallback(image)


def _yolo_inference(model, image: Image.Image) -> dict:
    """YOLOv8 분류 추론"""
    try:
        results = model.predict(image, imgsz=224, verbose=False)
        probs = results[0].probs
        top1_idx = int(probs.top1)
        top1_conf = float(probs.top1conf)
        label = model.names[top1_idx]          # "Grade_1" / "Grade_2" / "Grade_3" / "정상"
        display = label.replace("_", " ")
        meta = GRADE_META.get(label, GRADE_META["Grade_2"])

        # top-5 확률 보조 정보
        top5 = {model.names[int(i)]: round(float(probs.data[int(i)]) * 100, 1)
                for i in probs.top5}

        return {
            "grade": display,
            "grade_color": meta["color"],
            "description": meta["description"],
            "confidence": round(top1_conf * 100, 1),
            "erythema_ratio": top5.get("Grade_3", 0) + top5.get("Grade_2", 0) * 0.5,
            "dry_ratio": top5.get("Grade_1", 0),
            "blister_ratio": top5.get("Grade_3", 0),
            "top5_probs": top5,
            "analysis_note": "YOLOv8n-cls (ISIC 2018 dermoscopy fine-tune, 4-class)",
        }
    except Exception as e:
        return _hsv_fallback(image, note=f"YOLOv8 추론 오류({e}), HSV 폴백")


def _hsv_fallback(image: Image.Image, note: str = "HSV 색상 분석 폴백 모드") -> dict:
    """YOLOv8 없을 때 HSV 기반 폴백"""
    try:
        img_array = np.array(image.convert("RGB")).astype(np.float32)
        h, w = img_array.shape[:2]
        total_pixels = h * w

        r, g, b = img_array[:,:,0]/255, img_array[:,:,1]/255, img_array[:,:,2]/255
        cmax = np.maximum(np.maximum(r, g), b)
        cmin = np.minimum(np.minimum(r, g), b)
        delta = cmax - cmin
        sat = np.where(cmax > 0, delta / cmax, 0)
        val = cmax
        hue = np.zeros_like(r)
        mask_r = (cmax == r) & (delta > 0)
        hue[mask_r] = (60 * ((g[mask_r] - b[mask_r]) / delta[mask_r]) % 360)
        mask_g = (cmax == g) & (delta > 0)
        hue[mask_g] = 60 * ((b[mask_g] - r[mask_g]) / delta[mask_g]) + 120
        mask_b = (cmax == b) & (delta > 0)
        hue[mask_b] = 60 * ((r[mask_b] - g[mask_b]) / delta[mask_b]) + 240

        erythema_mask = ((hue <= 25) | (hue >= 335)) & (sat > 0.25) & (val > 0.30)
        dry_mask = (sat < 0.15) & (val > 0.55) & (val < 0.92)
        blister_mask = (sat < 0.10) & (val > 0.85)

        erythema_ratio = float(erythema_mask.sum()) / total_pixels
        dry_ratio = float(dry_mask.sum()) / total_pixels
        blister_ratio = float(blister_mask.sum()) / total_pixels

        blister_with_erythema = blister_ratio > 0.05 and erythema_ratio > 0.03
        if blister_with_erythema or erythema_ratio > 0.40:
            grade, meta = "Grade 3", GRADE_META["Grade_3"]
            confidence = min(55 + int(erythema_ratio * 80), 88)
        elif erythema_ratio > 0.18 or dry_ratio > 0.35:
            grade, meta = "Grade 2", GRADE_META["Grade_2"]
            confidence = min(52 + int(erythema_ratio * 60), 85)
        elif erythema_ratio > 0.06 or dry_ratio > 0.15:
            grade, meta = "Grade 1", GRADE_META["Grade_1"]
            confidence = min(50 + int(erythema_ratio * 50), 82)
        else:
            grade, meta = "정상 범위", GRADE_META["정상"]
            confidence = 70

        return {
            "grade": grade,
            "grade_color": meta["color"],
            "description": meta["description"],
            "confidence": confidence,
            "erythema_ratio": round(erythema_ratio * 100, 1),
            "dry_ratio": round(dry_ratio * 100, 1),
            "blister_ratio": round(blister_ratio * 100, 1),
            "top5_probs": {},
            "analysis_note": note,
        }
    except Exception as e:
        return {
            "grade": "분석 오류", "grade_color": "#888888",
            "description": f"이미지 분석 중 오류: {e}", "confidence": 0,
            "erythema_ratio": 0, "dry_ratio": 0, "blister_ratio": 0,
            "top5_probs": {}, "analysis_note": "오류",
        }


def get_demo_result(scenario: str = "grade2") -> dict:
    """데모용 결과값"""
    scenarios = {
        "grade1": {"grade": "Grade 1", "grade_color": "#88cc00",
                   "description": "경미한 홍반·건조 징후. 보습제 강화 및 자외선 차단 철저히.",
                   "confidence": 78, "erythema_ratio": 8.2, "dry_ratio": 18.5, "blister_ratio": 0.1,
                   "top5_probs": {"Grade_1": 78.2, "정상": 14.3, "Grade_2": 7.1, "Grade_3": 0.4},
                   "analysis_note": "데모 시나리오"},
        "grade2": {"grade": "Grade 2", "grade_color": "#ff6600",
                   "description": "중등도 홍반·각질 감지. 외용 스테로이드 도포 및 1-2주 내 외래 방문 권장.",
                   "confidence": 82, "erythema_ratio": 22.7, "dry_ratio": 38.1, "blister_ratio": 0.8,
                   "top5_probs": {"Grade_2": 82.1, "Grade_3": 10.5, "Grade_1": 6.2, "정상": 1.2},
                   "analysis_note": "데모 시나리오"},
        "grade3": {"grade": "Grade 3", "grade_color": "#cc0000",
                   "description": "수포·광범위 홍반 감지. 즉시 담당 의사 연락 필요.",
                   "confidence": 87, "erythema_ratio": 44.3, "dry_ratio": 25.6, "blister_ratio": 6.2,
                   "top5_probs": {"Grade_3": 87.4, "Grade_2": 9.8, "Grade_1": 2.3, "정상": 0.5},
                   "analysis_note": "데모 시나리오"},
        "normal": {"grade": "정상 범위", "grade_color": "#0088cc",
                   "description": "뚜렷한 병변 신호 없음. 예방적 보습 관리 지속.",
                   "confidence": 74, "erythema_ratio": 3.1, "dry_ratio": 9.4, "blister_ratio": 0.0,
                   "top5_probs": {"정상": 74.2, "Grade_1": 18.6, "Grade_2": 6.5, "Grade_3": 0.7},
                   "analysis_note": "데모 시나리오"},
    }
    return scenarios.get(scenario, scenarios["grade2"])


def model_is_ready() -> bool:
    """학습된 모델 파일 존재 여부"""
    return os.path.exists(MODEL_PATH)
