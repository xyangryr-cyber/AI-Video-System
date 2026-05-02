"""[SPEC-C-103] Per-claim-type verifier implementations.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-4 SPEC-6.Y.

Route table (claim_type -> verifier):
  data         -> FinancialDataVerifier
  fact / event -> FactCheckVerifier
  image_backed -> ImageBackedVerifier
  citation     -> CitationVerifier
"""

from __future__ import annotations

from src.backend.services.verifiers.citation_verifier import CitationVerifier
from src.backend.services.verifiers.fact_check_verifier import FactCheckVerifier
from src.backend.services.verifiers.financial_data_verifier import (
    FinancialDataVerifier,
)
from src.backend.services.verifiers.image_backed_verifier import ImageBackedVerifier

__all__ = [
    "CitationVerifier",
    "FactCheckVerifier",
    "FinancialDataVerifier",
    "ImageBackedVerifier",
]
