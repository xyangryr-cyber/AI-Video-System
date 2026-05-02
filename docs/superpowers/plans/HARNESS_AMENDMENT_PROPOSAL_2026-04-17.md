# Proposed HARNESS.md amendment (2026-04-17)

Reason: Spec docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md §1.2 isolates the imported Google AI Studio prototype under `prototype/`. That tree must be a read-only reference, not a SPEC-X-NNN-bound work area. This amendment registers the exemption.

## Diff (unified)

In §1.2 "Forbidden (Never Modify Without Red-Light Approval)", add row:
| `prototype/**` | Read-only imported prototype. Modify only via `[PROTO]` commits to refresh the imported snapshot. Do NOT import from `src/frontend/**`. |

In §3.2 "Git", append sentence:
> Exception: `prototype/**` uses commit prefix `[PROTO] <description>` (snapshot refresh from external prototype source). It is exempt from the `[SPEC-X-NNN]` rule and from per-card task flow.

In §1.1 "Allowed (Write)", add row:
| `prototype/**` | Prototype maintainer (red-light approval) | Snapshot of external prototype source; imports from `prototype/**` into `src/frontend/**` are forbidden. |
