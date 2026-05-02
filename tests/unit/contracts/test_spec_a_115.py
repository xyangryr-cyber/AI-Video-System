"""SPEC-A-115 (v3.18 D13): DeliveryVariant + SubtitleDownload."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.shared.schemas.artifacts import DeliveryVariant, SubtitleDownload


def test_delivery_variant_full():
    v = DeliveryVariant(
        platform="bilibili",
        resolution="1920x1080",
        codec="H.264",
        aspect_ratio="16:9",
        file_size_mb=180.0,
        download_url="https://cdn/final_bilibili.mp4",
    )
    assert v.platform == "bilibili"
    assert v.file_size_mb == 180.0


def test_delivery_variant_requires_positive_size():
    with pytest.raises(ValidationError):
        DeliveryVariant(
            platform="x",
            resolution="1x1",
            codec="x",
            aspect_ratio="1:1",
            file_size_mb=0,
            download_url="https://x",
        )


def test_subtitle_download_full():
    s = SubtitleDownload(format="srt", download_url="https://cdn/sub.srt")
    assert s.format == "srt"
