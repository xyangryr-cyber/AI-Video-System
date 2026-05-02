"""[SPEC-C-018] v3.17 reviewer namespace.

Holds the class-style MusicFitReviewer and audio-analysis helpers that
back its three v3.17 L1 checks (full_track_harmony / abrupt_transition /
speech_intelligibility). Does NOT replace `src/backend/agents/reviewers/`
— that module houses the 12-reviewer L1/L2 registry scaffolding from
SPEC-C-010. This module lives at the import path mandated by SPEC-C-018
task card `allowed_files`.
"""

from src.backend.agents.completeness_reviewer import CompletenessReviewer
