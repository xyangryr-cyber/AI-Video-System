"""Table Read/Write Ownership Registry (SPEC-1B)."""

from __future__ import annotations


class TableOwnership:
    __slots__ = ("table_name", "writer", "write_trigger", "readers")

    def __init__(
        self,
        table_name: str,
        writer: str | tuple[str, ...],
        write_trigger: str,
        readers: tuple[str, ...],
    ) -> None:
        self.table_name = table_name
        self.writer = writer
        self.write_trigger = write_trigger
        self.readers = readers

    def __repr__(self) -> str:
        return (
            f"TableOwnership(table_name={self.table_name!r}, "
            f"writer={self.writer!r}, readers={self.readers!r})"
        )


TABLE_OWNERSHIP: tuple[TableOwnership, ...] = (
    TableOwnership(
        table_name="projects",
        writer="API",
        write_trigger="User create/update/delete project",
        readers=("frontend", "WorkflowEngine"),
    ),
    TableOwnership(
        table_name="phases",
        writer="WorkflowEngine",
        write_trigger="Phase advance/rollback/skip; Producer artifact update",
        readers=("frontend", "GateKeeper"),
    ),
    TableOwnership(
        table_name="task_ledger",
        writer="WorkflowEngine",
        write_trigger="Task creation and status update",
        readers=("Dispatcher", "frontend", "GateKeeper"),
    ),
    TableOwnership(
        table_name="async_tasks",
        writer=("API", "Worker"),
        write_trigger="Async task enqueue/execute/complete",
        readers=("Worker", "frontend", "GateKeeper"),
    ),
    TableOwnership(
        table_name="events",
        writer=("API", "WorkflowEngine"),
        write_trigger="Every state change",
        readers=("frontend", "WS"),
    ),
    TableOwnership(
        table_name="preferences",
        writer="API",
        write_trigger="User confirms preferences / Settings update",
        readers=("frontend", "ProducerAgent", "PreferenceExtractor"),
    ),
    TableOwnership(
        table_name="agent_call_log",
        writer="API",
        write_trigger="After every LLM call",
        readers=("frontend", "GateKeeper"),
    ),
    TableOwnership(
        table_name="system_status",
        writer="API",
        write_trigger="App startup + periodic pre-flight check",
        readers=("frontend", "GateKeeper"),
    ),
    TableOwnership(
        table_name="financial_data_cache",
        writer="FinancialDataService",
        write_trigger="After external data fetch",
        readers=("FinancialDataService", "ResearchAgent"),
    ),
    TableOwnership(
        table_name="preference_snapshots",
        writer="API",
        write_trigger="Preference update/rollback",
        readers=("frontend",),
    ),
)
