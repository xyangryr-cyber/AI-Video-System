/** Table Read/Write Ownership Registry (SPEC-1B). */

export interface TableOwnership {
  table_name: string;
  writer: string | string[];
  write_trigger: string;
  readers: string[];
}

export const TABLE_OWNERSHIP: readonly TableOwnership[] = [
  {
    table_name: "projects",
    writer: "API",
    write_trigger: "User create/update/delete project",
    readers: ["frontend", "WorkflowEngine"],
  },
  {
    table_name: "phases",
    writer: "WorkflowEngine",
    write_trigger: "Phase advance/rollback/skip; Producer artifact update",
    readers: ["frontend", "GateKeeper"],
  },
  {
    table_name: "task_ledger",
    writer: "WorkflowEngine",
    write_trigger: "Task creation and status update",
    readers: ["Dispatcher", "frontend", "GateKeeper"],
  },
  {
    table_name: "async_tasks",
    writer: ["API", "Worker"],
    write_trigger: "Async task enqueue/execute/complete",
    readers: ["Worker", "frontend", "GateKeeper"],
  },
  {
    table_name: "events",
    writer: ["API", "WorkflowEngine"],
    write_trigger: "Every state change",
    readers: ["frontend", "WS"],
  },
  {
    table_name: "preferences",
    writer: "API",
    write_trigger: "User confirms preferences / Settings update",
    readers: ["frontend", "ProducerAgent", "PreferenceExtractor"],
  },
  {
    table_name: "agent_call_log",
    writer: "API",
    write_trigger: "After every LLM call",
    readers: ["frontend", "GateKeeper"],
  },
  {
    table_name: "system_status",
    writer: "API",
    write_trigger: "App startup + periodic pre-flight check",
    readers: ["frontend", "GateKeeper"],
  },
  {
    table_name: "financial_data_cache",
    writer: "FinancialDataService",
    write_trigger: "After external data fetch",
    readers: ["FinancialDataService", "ResearchAgent"],
  },
  {
    table_name: "preference_snapshots",
    writer: "API",
    write_trigger: "Preference update/rollback",
    readers: ["frontend"],
  },
] as const;
