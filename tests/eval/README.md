# Eval Sets (SPEC-B-012)

Evaluation sets for agent regression testing.

## Directory Structure

```
tests/eval/
  script_agent.jsonl      -- ScriptAgent eval cases
  reviewer_agent.jsonl    -- ReviewerAgent eval cases
  chart_agent.jsonl       -- ChartIntentAgent eval cases
  claims_agent.jsonl      -- ClaimExtractor eval cases
```

## Format

Each line is a JSON object:
```json
{
  "input": {"messages": [...], "phase": 1},
  "expected_output": {"key": "value"},
  "eval_criteria": ["exact_match", "partial_match"],
  "tags": ["script", "P1"]
}
```

## Running

```bash
pytest tests/eval/ --eval-mode
```
