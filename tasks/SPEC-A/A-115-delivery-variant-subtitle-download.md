# [SPEC-A-115] DeliveryVariant + SubtitleDownload (v3.18 D13)

## Metadata
- **task_id**: SPEC-A-115
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D13
- **depends_on**: [SPEC-A-105]

## Scope
Per-platform final delivery metadata (P12): resolution, codec, aspect ratio, file size, download URL. Plus a separate subtitle-download model.

## Acceptance Criteria
- [ ] AC-1: DeliveryVariant: platform, resolution, codec, aspect_ratio, file_size_mb, download_url.
- [ ] AC-2: SubtitleDownload: format, download_url.

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_115.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_delivery_variant_full | tests/unit/contracts/test_spec_a_115.py |
| AC-1 | test_delivery_variant_requires_positive_size | tests/unit/contracts/test_spec_a_115.py |
| AC-2 | test_subtitle_download_full | tests/unit/contracts/test_spec_a_115.py |
