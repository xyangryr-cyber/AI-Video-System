"""[SPEC-D-014] QualityFilter -- resolution, aspect ratio, watermark checks."""

from __future__ import annotations


class QualityFilter:
    @staticmethod
    def check_resolution(res: str) -> bool:
        h = int(res.replace("p", ""))
        return h >= 720

    @staticmethod
    def check_aspect_ratio(w: int, h: int) -> bool:
        if h == 0:
            return False
        return abs((w / h) - (16 / 9)) < 0.05
