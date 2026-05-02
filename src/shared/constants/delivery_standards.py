"""V1 Delivery Standards & V1.5 Kill-Switch Thresholds (SPEC-0.1, SPEC-0.2, SPEC-0.3)."""

V1_DELIVERY_STANDARDS = {
    "success_rate": 0.9,
    "p50_time_min": 45,
    "p90_time_min": 60,
    "p50_cost_usd": 8,
    "p90_cost_usd": 15,
    "first_frame_load_s": 3,
    "router_accuracy": 0.85,
    "router_p95_s": 3,
}

V15_KILLSWITCH = {
    "inject_subtask_usage_max": 0.3,
    "preference_extractor_acceptance_min": 0.2,
    "sample_size": 20,
}

P4_SINGLE_STATE_TARGET = (
    "SQLite is the only structured state write target. "
    "No file-as-DB, no dual-write to filesystem."
)

P5_STATELESS_AGENT_RULE = (
    "Agents are stateless: every call is a fresh function invocation. "
    "No self.history.append, no persistent object context across invocations."
)
