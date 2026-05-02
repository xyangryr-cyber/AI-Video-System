# [SPEC-GAPFIX-027] Whisper 强制对齐

## Metadata
- **task_id**: SPEC-GAPFIX-027
- **spec_ref**: Design Spec §7.2
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: L

## Scope
Replace the stub word-timing implementation in `src/backend/services/subtitle_generator.py` (currently evenly distributes word times) with a real Whisper API call using `word_timestamps=True`. Fall back to aeneas forced alignment if Whisper is unavailable.

## Allowed Files
- `src/backend/services/subtitle_generator.py`
- `tests/unit/services/test_subtitle_generator.py`

## Forbidden Files
- `HARNESS.md`

## Current State
```python
# Stub: evenly distributes word times across segment duration
def align_words(text: str, audio_path: str, start_sec: float, end_sec: float) -> list[dict]:
    words = text.split()
    duration = end_sec - start_sec
    interval = duration / len(words)
    return [{"word": w, "start": start_sec + i*interval, "end": start_sec + (i+1)*interval} for i, w in enumerate(words)]
```

## Acceptance Criteria
- [ ] AC-1: 调用 Whisper API (`word_timestamps=True`) 获取字词级时间戳
- [ ] AC-2: 每个 word 的 `start` 与实际音频位置偏差 < 200ms
- [ ] AC-3: Whisper 不可用时 fallback 到 aeneas 强制对齐
- [ ] AC-4: 两者都不可用时 fallback 到均分算法 + WARN 日志

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/services/test_subtitle_generator.py -v
.venv/bin/python3 -m ruff check src/backend/services/subtitle_generator.py
```

## Completion Definition
`align_words()` 优先使用 Whisper API 获取真实字词时间戳，必要时 fallback。测试通过。

## Risk Note
Whisper API token 权限不足是已知问题 (ByteDance TTS token 同样待审批)。先实现接口抽象 + fallback 链，token 就绪后无需代码改动。
