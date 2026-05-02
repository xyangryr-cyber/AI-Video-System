/** [SPEC-D-001] Reviewer Verdict / Gate check result types (TS mirror of verdict.py). */

export interface Verdict {
  verdict: "PASS" | "FAIL";
  notes: string[];
  blocking_issues: string[];
}
