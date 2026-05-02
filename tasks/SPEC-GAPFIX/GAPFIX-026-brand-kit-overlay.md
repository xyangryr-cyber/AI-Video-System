# [SPEC-GAPFIX-026] brand_kit_overlay — 真实 Remotion Sequence

## Metadata
- **task_id**: SPEC-GAPFIX-026
- **spec_ref**: Design Spec §7.1
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: L

## Scope
Replace the stub `brand_kit_overlay.py` (currently `video_path.replace(".mp4", "_branded.mp4")`) with a real Remotion sequence that renders intro/outro/watermark using brand kit assets.

## Allowed Files
- `src/backend/services/brand_kit_overlay.py`
- `tests/unit/services/test_brand_kit_overlay.py`

## Forbidden Files
- `HARNESS.md`

## Current State
```python
# Stub: just renames the file
def apply_brand_kit(video_path: str, brand_kit: dict) -> str:
    return video_path.replace(".mp4", "_branded.mp4")
```

## Acceptance Criteria
- [ ] AC-1: `apply_brand_kit()` 生成包含以下 Remotion sequence 的视频:
  - Intro: `AbsoluteFill` + brand logo fade-in (0.5s)
  - Outro: `AbsoluteFill` + watermark fade-out (0.5s)
  - Main content: watermark overlay at bottom-right
- [ ] AC-2: 函数签名不变 (`video_path, brand_kit -> str`)
- [ ] AC-3: brand_kit 参数包含 `logo_url`, `watermark_url`, `color_palette`
- [ ] AC-4: 输出文件确实不同于输入 (不是简单字符串替换)

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/services/test_brand_kit_overlay.py -v
.venv/bin/python3 -m ruff check src/backend/services/brand_kit_overlay.py
```

## Completion Definition
`apply_brand_kit()` 生成包含 intro/outro/watermark 的真实 Remotion 视频。测试通过。

## Risk Note
如果 Remotion 环境不可用，保留 stub 作为 fallback 但添加 WARN 日志。
