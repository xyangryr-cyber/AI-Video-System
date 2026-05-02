"""[SPEC-C-019] SfxSegmentMixService -- P6 per-segment SFX mix.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-4 item 1.

Consumes a validated ``SfxLayoutPlan`` (per trigger list) + an upstream
``base_master`` (narration_master or bgm_mix_master) and produces, for
each narration segment, a per-segment mp3 under
``phase_6/sfx_applied_segments/seg_XX.mp3`` plus a merged
``phase_6/sfx_mix_segments.json`` side-car compatible with the
``SfxMixSegments`` schema.

Contract (AC-7): ``base_master.kind`` MUST be one of
``{narration_master, bgm_mix_master}``; otherwise we raise
``InvalidBaseMasterError`` BEFORE any disk I/O.

Incremental re-mix contract (AC-5): calling ``mix_segment`` for a given
``segment_id`` only rewrites the mp3 for THAT segment and only updates
(or inserts) that segment's entry in ``sfx_mix_segments.json``. Sibling
segments' bytes on disk and their JSON checksums remain untouched.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Callable, List, Tuple

from src.backend.exceptions.sfx_exceptions import InvalidBaseMasterError
from src.shared.schemas.audio_master import (
    BgmMixMasterArtifact,
    MasterAudioArtifact,
    NarrationMasterArtifact,
)
from src.shared.schemas.sfx_layout_plan import SfxLayoutTrigger
from src.shared.schemas.sfx_mix_segments import (
    SfxMixSegment,
    SfxMixSegments,
)


PHASE_6_DIR = "phase_6"
APPLIED_DIR = "sfx_applied_segments"
SEGMENTS_JSON_NAME = "sfx_mix_segments.json"

SfxResolver = Callable[[SfxLayoutTrigger], Path]


class SfxSegmentMixService:
    """Mix one narration segment's slice of base_master with its triggers."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        # conn is retained for symmetry with the other P-layer services
        # (NarrationMasterAssembler / BgmMixRenderer) even though this
        # service does not itself write the DB; future extensions (e.g.
        # per-segment task_ledger rows) will reuse it.
        self._conn = conn

    def mix_segment(
        self,
        project_id: str,
        project_root: Path,
        segment_id: str,
        base_master: MasterAudioArtifact,
        triggers: List[SfxLayoutTrigger],
        sfx_resolver: SfxResolver,
    ) -> SfxMixSegment:
        _check_base_master_kind(base_master)

        seg_start, seg_duration = _resolve_segment_window(
            project_root, base_master, segment_id
        )
        base_path = _resolve_base_path(project_root, base_master)
        applied_triggers = _clip_triggers_to_window(triggers, seg_start, seg_duration)

        phase_dir = project_root / PHASE_6_DIR
        out_rel = f"{PHASE_6_DIR}/{APPLIED_DIR}/{segment_id}.mp3"
        checksum = _render_segment_mp3(
            project_root=project_root,
            out_rel=out_rel,
            base_path=base_path,
            seg_start=seg_start,
            seg_duration=seg_duration,
            applied_triggers=applied_triggers,
            sfx_resolver=sfx_resolver,
        )

        existing = _load_existing_mix(phase_dir, base_master.file_path)
        segment = SfxMixSegment(
            segment_id=segment_id,
            file_path=out_rel,
            applied_triggers=[t.trigger_id for t in applied_triggers],
            checksum=checksum,
            version=_next_version_for(existing, segment_id),
        )
        _write_upserted(phase_dir, base_master.file_path, existing, segment)
        return segment


# ---- module-level helpers --------------------------------------------


def _check_base_master_kind(base_master: MasterAudioArtifact) -> None:
    if not isinstance(base_master, (NarrationMasterArtifact, BgmMixMasterArtifact)):
        raise InvalidBaseMasterError(
            f"base_master.kind must be narration_master or "
            f"bgm_mix_master; got {base_master.kind!r}"
        )


def _resolve_base_path(project_root: Path, base_master: MasterAudioArtifact) -> Path:
    base_path = (project_root / base_master.file_path).resolve()
    if not base_path.is_file():
        raise FileNotFoundError(f"base_master file missing on disk: {base_path}")
    return base_path


def _resolve_segment_window(
    project_root: Path,
    base_master: MasterAudioArtifact,
    segment_id: str,
) -> Tuple[float, float]:
    windows = _compute_segment_windows(
        project_root, list(base_master.derived_from_segments)
    )
    return _find_window(windows, segment_id)


def _next_version_for(existing: SfxMixSegments, segment_id: str) -> int:
    prev = next((s for s in existing.segments if s.segment_id == segment_id), None)
    return 1 if prev is None else prev.version + 1


def _render_segment_mp3(
    project_root: Path,
    out_rel: str,
    base_path: Path,
    seg_start: float,
    seg_duration: float,
    applied_triggers: List[SfxLayoutTrigger],
    sfx_resolver: SfxResolver,
) -> str:
    out_path = project_root / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".tmp.mp3")
    tmp_path.unlink(missing_ok=True)
    try:
        _run_segment_mix(
            base_path=base_path,
            segment_start_s=seg_start,
            segment_duration_s=seg_duration,
            triggers=applied_triggers,
            sfx_resolver=sfx_resolver,
            out_path=tmp_path,
        )
        checksum = _sha256_of_file(tmp_path)
        tmp_path.replace(out_path)
        return checksum
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _clip_triggers_to_window(
    triggers: List[SfxLayoutTrigger],
    seg_start: float,
    seg_duration: float,
) -> List[SfxLayoutTrigger]:
    """Keep only triggers that land inside [seg_start, seg_start+seg_duration)
    and truncate each trigger's duration to fit the remaining window."""
    clipped: List[SfxLayoutTrigger] = []
    for t in triggers:
        offset = t.planned_time_sec - seg_start
        if offset < 0 or offset >= seg_duration:
            continue
        usable = min(t.duration_seconds, seg_duration - offset)
        if usable <= 0:
            continue
        clipped.append(t.model_copy(update={"duration_seconds": usable}))
    return clipped


def _compute_segment_windows(
    project_root: Path,
    narration_segments: List[str],
) -> List[Tuple[str, float, float]]:
    """For each narration segment in order, return (segment_id, start_s, duration_s).

    Uses raw ``phase_4/seg_*.mp3`` durations because the master audio file
    is an order-preserving concatenation of those segments (both
    narration_master and bgm_mix_master preserve the narration timeline).
    """
    phase_4 = project_root / "phase_4"
    out: List[Tuple[str, float, float]] = []
    cumulative = 0.0
    for seg_id in narration_segments:
        seg_path = phase_4 / f"{seg_id}.mp3"
        if not seg_path.is_file():
            raise FileNotFoundError(
                f"narration segment file missing on disk: {seg_path}"
            )
        dur = _probe_duration_seconds(seg_path)
        out.append((seg_id, cumulative, dur))
        cumulative += dur
    return out


def _find_window(
    windows: List[Tuple[str, float, float]], segment_id: str
) -> Tuple[float, float]:
    for seg_id, start, dur in windows:
        if seg_id == segment_id:
            return start, dur
    raise KeyError(
        f"segment_id {segment_id!r} not in base_master.derived_from_segments"
    )


def _ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        raise RuntimeError("ffmpeg binary not found on PATH")
    return found


def _ffprobe_bin() -> str:
    found = shutil.which("ffprobe")
    if not found:
        raise RuntimeError("ffprobe binary not found on PATH")
    return found


def _probe_duration_seconds(path: Path) -> float:
    ffprobe = _ffprobe_bin()
    out = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(out.stdout.strip())


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _resolve_sfx_inputs(
    triggers: List[SfxLayoutTrigger], sfx_resolver: SfxResolver
) -> List[Path]:
    resolved: List[Path] = []
    for t in triggers:
        p = Path(sfx_resolver(t)).resolve()
        if not p.is_file():
            raise FileNotFoundError(
                f"sfx source missing for trigger {t.trigger_id}: {p}"
            )
        resolved.append(p)
    return resolved


def _build_filter_complex(
    segment_start_s: float,
    segment_duration_s: float,
    triggers: List[SfxLayoutTrigger],
) -> str:
    base_trim = f"[0:a]atrim=duration={segment_duration_s:.6f},asetpts=PTS-STARTPTS"
    if not triggers:
        return f"{base_trim}[out]"

    parts: List[str] = [f"{base_trim}[base]"]
    mix_labels: List[str] = ["[base]"]
    for idx, t in enumerate(triggers, start=1):
        offset_ms = int(round((t.planned_time_sec - segment_start_s) * 1000))
        label = f"[sfx{idx}]"
        parts.append(
            f"[{idx}:a]"
            f"volume={t.volume_db}dB,"
            f"atrim=duration={t.duration_seconds:.6f},"
            f"asetpts=PTS-STARTPTS,"
            f"adelay={offset_ms}|{offset_ms},"
            f"apad=whole_dur={segment_duration_s:.6f}"
            f"{label}"
        )
        mix_labels.append(label)
    parts.append(
        "".join(mix_labels) + f"amix=inputs={len(mix_labels)}:duration=first:"
        "dropout_transition=0:normalize=0[out]"
    )
    return ";".join(parts)


def _run_segment_mix(
    base_path: Path,
    segment_start_s: float,
    segment_duration_s: float,
    triggers: List[SfxLayoutTrigger],
    sfx_resolver: SfxResolver,
    out_path: Path,
) -> None:
    ffmpeg = _ffmpeg_bin()
    sfx_paths = _resolve_sfx_inputs(triggers, sfx_resolver)
    filter_complex = _build_filter_complex(
        segment_start_s, segment_duration_s, triggers
    )

    cmd: List[str] = [
        ffmpeg,
        "-y",
        "-v",
        "error",
        "-ss",
        f"{segment_start_s:.6f}",
        "-t",
        f"{segment_duration_s:.6f}",
        "-i",
        str(base_path),
    ]
    for p in sfx_paths:
        cmd += ["-i", str(p)]
    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-ac",
        "1",
        "-ar",
        "44100",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        # Strip muxer-side metadata so identical inputs produce byte-identical
        # output (needed for AC-5 incremental-remix checksum isolation).
        "-map_metadata",
        "-1",
        "-write_xing",
        "0",
        "-id3v2_version",
        "0",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg segment mix failed (rc={proc.returncode}): {proc.stderr.strip()}"
        )


def _load_existing_mix(phase_dir: Path, base_master_file_path: str) -> SfxMixSegments:
    """Load sfx_mix_segments.json if present; reset segments if the
    base_master swapped between calls (narration -> bgm switchover should
    not silently carry stale per-segment mixes forward)."""
    path = phase_dir / SEGMENTS_JSON_NAME
    if not path.is_file():
        return SfxMixSegments(base_master=base_master_file_path, segments=[])
    data = json.loads(path.read_text(encoding="utf-8"))
    existing = SfxMixSegments.model_validate(data)
    if existing.base_master != base_master_file_path:
        return SfxMixSegments(base_master=base_master_file_path, segments=[])
    return existing


def _write_upserted(
    phase_dir: Path,
    base_master_file_path: str,
    existing: SfxMixSegments,
    segment: SfxMixSegment,
) -> None:
    segments = [s for s in existing.segments if s.segment_id != segment.segment_id]
    segments.append(segment)
    segments.sort(key=lambda s: s.segment_id)

    merged = SfxMixSegments(base_master=base_master_file_path, segments=segments)
    path = phase_dir / SEGMENTS_JSON_NAME
    tmp = path.with_suffix(".tmp.json")
    tmp.write_text(
        json.dumps(merged.model_dump(mode="json"), sort_keys=True, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


__all__ = [
    "APPLIED_DIR",
    "PHASE_6_DIR",
    "SEGMENTS_JSON_NAME",
    "SfxSegmentMixService",
]
