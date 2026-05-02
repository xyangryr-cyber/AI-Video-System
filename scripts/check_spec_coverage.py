#!/usr/bin/env python3
"""[GAPFIX-031] Check test coverage against SPEC acceptance criteria.

Scans tests/ for test files, reads SPEC markdown files for acceptance criteria
(``- [ ]`` checkboxes), and reports any SPEC section without corresponding test
coverage.

Mapping strategy:
  - Directory-based: tests/unit/contracts/ -> SPEC-A, tests/unit/infra/ -> SPEC-B, etc.
  - Keyword-based: match test file basenames against SPEC section descriptions.
  - SPEC-prefix-based: test_spec_{letter}_{num}.py -> covers that SPEC letter.

Usage:
  python3 scripts/check_spec_coverage.py              # full report
  python3 scripts/check_spec_coverage.py --json       # JSON output
  python3 scripts/check_spec_coverage.py --help
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECS_DIR = os.path.join(PROJECT_ROOT, "docs", "specs")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")

# SPEC files to scan
SPEC_FILE_MAP: Dict[str, str] = {
    "A": "SPEC-A-contracts.md",
    "B": "SPEC-B-infra-deploy.md",
    "C": "SPEC-C-backend-core.md",
    "D": "SPEC-D-pipeline-phases.md",
    "E": "SPEC-E-frontend-ui.md",
    "F": "SPEC-F-media-render.md",
}

# Test directory -> SPEC letter mapping
DIR_TO_SPEC: Dict[str, str] = {
    "contracts": "A",
    "infra": "B",
    "backend-core": "C",
    "pipeline": "D",
    "frontend": "E",
    "media-render": "F",
    "gates": "D",
    "reviewers": "D",
    "workers": "D",
    "services": "D",
    "agents": "C",
    "api": "C",
    "db": "C",
    "scripts": "B",
}


# ---------------------------------------------------------------------------
# SPEC parsing
# ---------------------------------------------------------------------------

def _extract_spec_section_id(heading_line: str) -> Optional[str]:
    m = re.search(r'(SPEC-[\d]+[A-Za-z]*(?:\.[\d]+(?:\.[\d]+)?)?)', heading_line)
    return m.group(1) if m else None


def _extract_section_description(heading_line: str) -> str:
    """Extract the description text after the SPEC section ID."""
    m = re.search(r'SPEC-[\d]+[A-Za-z]*(?:\.[\d]+(?:\.[\d]+)?)?\s*(.*)', heading_line)
    if m:
        desc = m.group(1).strip()
        return desc
    return heading_line.strip("#").strip()


def _parse_spec_file(filepath: str) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    """Parse a SPEC file, returning {section_id: [criteria]} and {section_id: description}."""
    sections: Dict[str, List[str]] = {}
    descriptions: Dict[str, str] = {}
    if not os.path.isfile(filepath):
        return sections, descriptions

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_section: Optional[str] = None
    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("#"):
            sec_id = _extract_spec_section_id(stripped)
            if sec_id:
                current_section = sec_id
                if sec_id not in sections:
                    sections[sec_id] = []
                descriptions[sec_id] = _extract_section_description(stripped)
        m = re.match(r'^\s*-\s*\[ \]\s*(.+)', stripped)
        if m and current_section:
            sections[current_section].append(m.group(1).strip())

    return sections, descriptions


# ---------------------------------------------------------------------------
# test file scanning
# ---------------------------------------------------------------------------

def _collect_test_files_by_spec() -> Dict[str, List[str]]:
    """Collect test files organized by SPEC letter (A-F) based on directory."""
    by_spec: Dict[str, List[str]] = defaultdict(list)
    for root, _dirs, files in os.walk(TESTS_DIR):
        rel_dir = os.path.relpath(root, TESTS_DIR)
        # Determine SPEC letter from directory
        spec_letter = None
        for dir_key, letter in DIR_TO_SPEC.items():
            if rel_dir == dir_key or rel_dir.startswith(dir_key + "/") or rel_dir.startswith(dir_key):
                spec_letter = letter
                break

        if spec_letter is None:
            # Root-level test files or unmatched dirs — try to infer from filename
            for fname in files:
                m = re.match(r'test_spec_([a-f])_\d+\.py', fname)
                if m:
                    spec_letter = m.group(1).upper()
                    break
            if spec_letter is None:
                spec_letter = "?"

        for fname in files:
            if (fname.endswith(".py") and fname.startswith("test_")) or \
               fname.endswith(".test.tsx") or fname.endswith(".test.ts"):
                if not fname.startswith("__"):
                    by_spec[spec_letter].append(fname)

    return dict(by_spec)


# ---------------------------------------------------------------------------
# coverage analysis
# ---------------------------------------------------------------------------

def _build_keywords(desc: str) -> List[str]:
    """Extract meaningful lowercase keywords from a section description."""
    # Remove CJK characters and punctuation
    clean = re.sub(r'[^\w\s/-]', ' ', desc)
    words = clean.lower().split()
    # Filter short words and common stop words
    stop = {'the', 'a', 'an', 'of', 'in', 'on', 'to', 'for', 'and', 'or', 'is', 'are',
            'by', 'as', 'at', 'be', 'no', 'not', 'if', 'it', 'its', 'from', 'with',
            'this', 'that', 'these', 'those', 'has', 'have', 'was', 'were', 'been',
            'spec'}
    keywords = [w for w in words if len(w) > 2 and w not in stop]
    # Also keep the alphanumeric part of the section ID as a keyword
    return keywords


def _match_test_to_section(
    section_id: str,
    description: str,
    test_files: List[str],
    spec_letter: str,
) -> bool:
    """Check if any test file matches this SPEC section."""
    keywords = _build_keywords(description)
    # Build a simplified section id for matching (e.g., SPEC-1A -> 1a)
    id_parts = re.findall(r'[\d]+[A-Za-z]*', section_id.replace("SPEC-", ""))
    id_slug = "".join(id_parts).lower() if id_parts else ""

    for tf in test_files:
        tf_lower = tf.lower().replace("_", "").replace("-", "").replace(".py", "").replace(".tsx", "").replace(".test", "")
        # Match by spec prefix: test_spec_a_006 covers any section in SPEC-A
        m = re.match(r'testspec([a-f])(\d+)', tf_lower)
        if m:
            if m.group(1) == spec_letter.lower():
                return True

        # Match by keyword: check if test file contains keywords from section
        match_count = 0
        for kw in keywords:
            if kw in tf_lower:
                match_count += 1
        if match_count >= 2 and len(keywords) > 0:
            return True

        # Match by section id slug
        if id_slug and id_slug in tf_lower:
            return True

    return False


def _build_coverage() -> Tuple[
    Dict[str, Dict[str, List[str]]],     # {spec_letter: {section_id: [criteria]}}
    Dict[str, str],                       # {section_id: description}
    Dict[str, int],                       # {spec_letter: covered_sections}
    Dict[str, int],                       # {spec_letter: total_sections}
    Dict[str, Dict[str, List[str]]],      # {section_id: [matching_test_files]}
]:
    all_sections: Dict[str, Dict[str, List[str]]] = {}
    all_descriptions: Dict[str, str] = {}

    for letter, fname in SPEC_FILE_MAP.items():
        filepath = os.path.join(SPECS_DIR, fname)
        sections, descriptions = _parse_spec_file(filepath)
        # Filter to sections that have acceptance criteria
        sections_with_criteria = {k: v for k, v in sections.items() if v}
        if sections_with_criteria:
            all_sections[letter] = sections_with_criteria
        all_descriptions.update(descriptions)

    test_files_by_spec = _collect_test_files_by_spec()

    # Track coverage
    covered: Dict[str, int] = defaultdict(int)
    total: Dict[str, int] = {}
    section_test_map: Dict[str, List[str]] = defaultdict(list)

    for letter, sections in all_sections.items():
        test_files = test_files_by_spec.get(letter, []) + test_files_by_spec.get("?", [])
        total[letter] = len(sections)
        for sec_id, criteria in sections.items():
            desc = all_descriptions.get(sec_id, "")
            matching = [tf for tf in test_files
                        if _match_test_to_section(sec_id, desc, [tf], letter)]
            if matching:
                covered[letter] += 1
                section_test_map[sec_id] = matching

    return all_sections, all_descriptions, dict(covered), dict(total), dict(section_test_map)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check test coverage against SPEC acceptance criteria."
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    all_sections, descriptions, covered, total, section_test_map = _build_coverage()

    # Compute overall stats
    overall_total = sum(total.values())
    overall_covered = sum(covered.values())
    overall_uncovered = overall_total - overall_covered

    uncovered_sections: Dict[str, List[str]] = {}
    for letter in sorted(all_sections.keys()):
        uncovered_sections[letter] = [
            sec_id for sec_id in all_sections[letter]
            if sec_id not in section_test_map
        ]

    if args.json:
        output = {
            "total_spec_sections_with_criteria": overall_total,
            "covered_sections": overall_covered,
            "uncovered_sections": overall_uncovered,
            "coverage_rate_pct": (100 * overall_covered // overall_total) if overall_total else 0,
            "by_spec": {
                letter: {
                    "total": total.get(letter, 0),
                    "covered": covered.get(letter, 0),
                    "uncovered_sections": uncovered_sections.get(letter, []),
                }
                for letter in sorted(all_sections.keys())
            },
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 65)
        print("SPEC Coverage Report")
        print("=" * 65)
        print(f"SPEC sections with acceptance criteria: {overall_total}")
        print(f"Covered by test files:                 {overall_covered}")
        print(f"Uncovered:                             {overall_uncovered}")
        if overall_total > 0:
            print(f"Coverage rate:                         {overall_covered}/{overall_total} "
                  f"({100*overall_covered//overall_total}%)")
        print()

        # Per-SPEC breakdown
        for letter in sorted(all_sections.keys()):
            t = total.get(letter, 0)
            c = covered.get(letter, 0)
            u = t - c
            pct = 100 * c // t if t else 0
            fname = SPEC_FILE_MAP.get(letter, "?")
            print(f"  SPEC-{letter}: {c}/{t} covered ({pct}%) — {fname}")
            if u > 0:
                for sec_id in uncovered_sections.get(letter, [])[:5]:
                    desc = descriptions.get(sec_id, "")
                    criteria_count = len(all_sections[letter].get(sec_id, []))
                    print(f"    - {sec_id}: {desc[:60]} ({criteria_count} criteria)")
                if u > 5:
                    print(f"    ... and {u - 5} more uncovered sections")
        print()

    return 1 if overall_uncovered > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
