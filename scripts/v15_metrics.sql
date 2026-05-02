-- V1.5 Kill-Switch Metrics (SPEC-0.2)
-- Produces inject_subtask usage rate and preference acceptance rate from events table.

-- inject_subtask usage rate: projects using inject_subtask / total projects
SELECT
    'inject_subtask_usage_rate' AS metric,
    CAST(
        COUNT(DISTINCT CASE WHEN type = 'task.created'
            AND json_extract(payload, '$.task_type') = 'inject_subtask'
            THEN project_id END) AS REAL
    ) / NULLIF(COUNT(DISTINCT project_id), 0) AS value
FROM events;

-- preference acceptance rate: confirmed preferences / total extracted
SELECT
    'preference_acceptance_rate' AS metric,
    CAST(
        SUM(CASE WHEN type = 'preference.confirmed' THEN 1 ELSE 0 END) AS REAL
    ) / NULLIF(
        SUM(CASE WHEN type = 'preference.extracted' THEN 1 ELSE 0 END), 0
    ) AS value
FROM events;
