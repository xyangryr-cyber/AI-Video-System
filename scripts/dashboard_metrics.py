"""[SPEC-B-100] Dashboard metrics collector + alert evaluator.

Authority: tasks/SPEC-B/B-100-claim-verification-worker.md (AC-2 + AC-3).

Emits the four claim_verification metrics (task card AC-2):
    pending_count          — async_tasks rows with type='claim_verification'
                             and status in {'pending','queued'}
    verifying_latency_p95  — 95th-percentile (seconds) of finished tasks'
                             finished_at - started_at
    failed_rate            — failed / (succeeded + failed), 0.0 if no
                             terminal tasks yet
    hard_blocking_count    — claims with blocking_level='hard' and
                             verification_status NOT IN ('verified','superseded')

And evaluates the SPEC-B-100 AC-3 alert rules (pending>100, dead_letter>5)
against either a live SQLite connection or a prepared metrics dict.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALERTS_CONFIG_PATH = PROJECT_ROOT / "config" / "alerts" / "claim_verification.yaml"


DASHBOARD_METRIC_KEYS: tuple[str, ...] = (
    "pending_count",
    "verifying_latency_p95",
    "failed_rate",
    "hard_blocking_count",
)


# --------------------------------------------------------------------------- #
# AC-2: collect_metrics
# --------------------------------------------------------------------------- #


def _p95(samples: Sequence[float]) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    n = len(ordered)
    idx = max(0, math.ceil(0.95 * n) - 1)
    return float(ordered[idx])


def _iso_to_epoch(value: str) -> float:
    # Accept "YYYY-MM-DDTHH:MM:SS.fffZ" and trailing "Z".
    text = value.rstrip("Z")
    from datetime import datetime
    return datetime.fromisoformat(text).timestamp()


def collect_metrics(conn: sqlite3.Connection) -> dict[str, float]:
    """Collect the four SPEC-B-100 Dashboard metrics from a live DB.

    The caller supplies a SQLite connection; no schema mutation occurs.
    """
    cur = conn.cursor()

    pending_count = cur.execute(
        "SELECT COUNT(*) FROM async_tasks WHERE type='claim_verification' "
        "AND status IN ('pending','queued')"
    ).fetchone()[0]

    latency_rows = cur.execute(
        "SELECT started_at, finished_at FROM async_tasks "
        "WHERE type='claim_verification' AND status='succeeded' "
        "AND started_at IS NOT NULL AND finished_at IS NOT NULL"
    ).fetchall()
    latencies = [
        _iso_to_epoch(finished) - _iso_to_epoch(started)
        for started, finished in latency_rows
    ]
    verifying_latency_p95 = _p95(latencies)

    terminal = cur.execute(
        "SELECT status, COUNT(*) FROM async_tasks "
        "WHERE type='claim_verification' AND status IN ('succeeded','failed') "
        "GROUP BY status"
    ).fetchall()
    totals = {status: count for status, count in terminal}
    succeeded = totals.get("succeeded", 0)
    failed = totals.get("failed", 0)
    denom = succeeded + failed
    failed_rate = (failed / denom) if denom else 0.0

    hard_blocking_count = cur.execute(
        "SELECT COUNT(*) FROM claims WHERE blocking_level='hard' "
        "AND verification_status NOT IN ('verified','superseded')"
    ).fetchone()[0]

    return {
        "pending_count": int(pending_count),
        "verifying_latency_p95": float(verifying_latency_p95),
        "failed_rate": float(failed_rate),
        "hard_blocking_count": int(hard_blocking_count),
    }


# --------------------------------------------------------------------------- #
# AC-3: check_alerts
# --------------------------------------------------------------------------- #


_CONDITION_FNS = {
    "greater_than": lambda value, threshold: value > threshold,
    "greater_than_or_equal": lambda value, threshold: value >= threshold,
    "less_than": lambda value, threshold: value < threshold,
    "less_than_or_equal": lambda value, threshold: value <= threshold,
    "equal": lambda value, threshold: value == threshold,
}


def _load_default_alerts_config() -> dict[str, Any]:
    try:
        import yaml
    except ImportError as err:
        raise RuntimeError(
            "pyyaml is required to load config/alerts/claim_verification.yaml"
        ) from err
    return yaml.safe_load(ALERTS_CONFIG_PATH.read_text(encoding="utf-8")) or {}


def check_alerts(
    metrics: Mapping[str, float],
    *,
    alerts_config: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return the list of fired alerts for *metrics*.

    Each fired alert is a dict with the original rule fields plus
    ``fired_value``. A rule whose metric is missing from *metrics*
    silently skips (a missing metric cannot breach a threshold).
    """
    config = alerts_config if alerts_config is not None else _load_default_alerts_config()
    rules = config.get("alerts") or []
    fired: list[dict[str, Any]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        metric_name = rule.get("metric")
        if metric_name is None or metric_name not in metrics:
            continue
        condition = rule.get("condition", "greater_than")
        threshold = rule.get("threshold")
        fn = _CONDITION_FNS.get(condition)
        if fn is None or threshold is None:
            continue
        value = metrics[metric_name]
        if fn(value, threshold):
            fired.append({**rule, "fired_value": value})
    return fired


# --------------------------------------------------------------------------- #
# CLI entry point (for ad-hoc Dashboard refresh / cron use).
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit SPEC-B-100 Dashboard metrics + alert evaluation."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to sqlite DB (async_tasks + claims tables).",
    )
    parser.add_argument(
        "--dead-letter-count",
        type=int,
        default=0,
        help="Dead-letter count (passed separately; not derivable from metrics tables).",
    )
    args = parser.parse_args(argv)

    conn = sqlite3.connect(args.db)
    try:
        metrics = collect_metrics(conn)
    finally:
        conn.close()
    metrics_with_dl = {**metrics, "dead_letter_count": args.dead_letter_count}
    fired = check_alerts(metrics_with_dl)
    json.dump(
        {"metrics": metrics_with_dl, "fired_alerts": fired},
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0 if not fired else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
